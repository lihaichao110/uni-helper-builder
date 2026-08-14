import hashlib
import os
import queue
import shutil
import threading
import time
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import docker
import redis
from celery import shared_task
from docker.errors import DockerException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .config import get_settings
from .database import SessionLocal
from .git_service import GitOperationError, clone_ref
from .models import Artifact, BuildJob, BuildStatus, InstallStrategy, Project


class BuildCanceled(RuntimeError):
    pass


class BuildExecutionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class BuildLogger:
    def __init__(self, build_id: str, path: Path):
        self.build_id = build_id
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.redis = redis.from_url(get_settings().redis_url)

    def __call__(self, message: str):
        line = f"[{datetime.now(UTC).isoformat()}] {message.rstrip()}\n"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
        try:
            self.redis.publish(f"build-log:{self.build_id}", line)
        except Exception:
            pass


def update_build(build_id: str, **values) -> BuildJob:
    with SessionLocal() as db:
        build = db.get(BuildJob, build_id)
        if not build:
            raise BuildExecutionError("BUILD_NOT_FOUND", "构建任务不存在")
        for key, value in values.items():
            setattr(build, key, value)
        db.commit()
        db.refresh(build)
        return build


def is_canceled(build_id: str) -> bool:
    with SessionLocal() as db:
        build = db.get(BuildJob, build_id)
        return not build or build.cancel_requested


def chown_tree(path: Path, uid: int = 1000, gid: int = 1000) -> None:
    chown = getattr(os, "chown", None)
    if chown is None:
        return
    for root, dirs, files in os.walk(path):
        chown(root, uid, gid)
        for name in dirs:
            chown(Path(root) / name, uid, gid)
        for name in files:
            chown(Path(root) / name, uid, gid)


def stream_container(build_id: str, container, timeout_seconds: int, log: BuildLogger) -> None:
    messages: queue.Queue[bytes | Exception | None] = queue.Queue()

    def reader():
        try:
            for chunk in container.logs(stream=True, follow=True, stdout=True, stderr=True):
                messages.put(chunk)
        except Exception as exc:
            messages.put(exc)
        finally:
            messages.put(None)

    threading.Thread(target=reader, daemon=True).start()
    started = time.monotonic()
    reader_finished = False
    while True:
        try:
            item = messages.get(timeout=0.5)
            if item is None:
                reader_finished = True
            elif isinstance(item, Exception):
                log(f"日志读取警告：{item}")
            else:
                text = item.decode("utf-8", errors="replace")
                for line in text.splitlines():
                    log(line)
        except queue.Empty:
            pass
        container.reload()
        if is_canceled(build_id):
            log("收到取消请求，正在停止构建容器")
            container.stop(timeout=5)
            raise BuildCanceled("用户取消构建")
        if time.monotonic() - started > timeout_seconds:
            log("构建超过超时时间，正在停止容器")
            container.stop(timeout=5)
            raise BuildExecutionError("BUILD_TIMEOUT", "构建执行超时")
        if container.status in {"exited", "dead"} and reader_finished:
            break
    result = container.wait()
    if result.get("StatusCode", 1) != 0:
        raise BuildExecutionError("CONTAINER_FAILED", f"构建容器退出码：{result.get('StatusCode')}")


def run_builder_container(
    build_id: str,
    source_host_path: Path,
    command: list[str],
    environment: dict[str, str],
    network_disabled: bool,
    timeout_seconds: int,
    log: BuildLogger,
) -> None:
    settings = get_settings()
    client = docker.from_env()
    container = None
    try:
        safe_environment = {
            "HOME": "/tmp",
            "npm_config_cache": "/tmp/npm-cache",
            "YARN_CACHE_FOLDER": "/tmp/yarn-cache",
            "PNPM_HOME": "/tmp/pnpm-home",
            **environment,
        }
        container = client.containers.run(
            settings.builder_image,
            command=command,
            detach=True,
            remove=False,
            name=f"uni-build-{build_id[:12]}-{int(time.time())}",
            environment=safe_environment,
            volumes={str(source_host_path): {"bind": "/workspace", "mode": "rw"}},
            working_dir="/workspace",
            network_disabled=network_disabled,
            user="1000:1000",
            read_only=True,
            tmpfs={"/tmp": "rw,noexec,nosuid,size=512m"},
            mem_limit=settings.build_memory,
            nano_cpus=settings.build_cpu_count * 1_000_000_000,
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
            labels={"uni-builder.build-id": build_id},
        )
        update_build(build_id, container_id=container.id)
        stream_container(build_id, container, timeout_seconds, log)
    except DockerException as exc:
        raise BuildExecutionError("DOCKER_ERROR", f"Docker 执行失败：{exc}") from exc
    finally:
        update_build(build_id, container_id=None)
        if container:
            try:
                container.remove(force=True)
            except DockerException:
                pass
        client.close()


INSTALL_COMMANDS = {
    InstallStrategy.npm_ci: ["npm", "ci", "--no-audit", "--no-fund"],
    InstallStrategy.yarn_frozen: ["yarn", "install", "--frozen-lockfile"],
    InstallStrategy.pnpm_frozen: ["pnpm", "install", "--frozen-lockfile"],
}


def package_wgt(project: Project, build: BuildJob, source_dir: Path, log: BuildLogger) -> Artifact:
    dist_dir = source_dir / "wgt-dist"
    if not dist_dir.is_dir() or not any(path.is_file() for path in dist_dir.rglob("*")):
        raise BuildExecutionError("EMPTY_OUTPUT", "编译完成但 wgt-dist 为空")
    settings = get_settings()
    destination = settings.artifact_root / project.id
    destination.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(
        char if char.isalnum() or char in "-_" else "-" for char in project.name
    ).strip("-")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{safe_name}-{(build.commit_sha or 'unknown')[:8]}-{timestamp}.wgt"
    artifact_path = destination / filename
    with zipfile.ZipFile(
        artifact_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(dist_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() != ".wgt":
                archive.write(path, path.relative_to(dist_dir).as_posix())
    hasher = hashlib.sha256()
    with artifact_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    log(f"WGT 已生成：{filename}，SHA-256={digest}")
    return Artifact(
        build_id=build.id,
        filename=filename,
        storage_path=str(artifact_path),
        size_bytes=artifact_path.stat().st_size,
        sha256=digest,
    )


@shared_task(name="app.tasks.execute_build", bind=True)
def execute_build(self, build_id: str):
    settings = get_settings()
    workspace = settings.workspace_root / build_id
    source_dir = workspace / "source"
    source_host_path = settings.host_workspace_root / build_id / "source"
    log_path = settings.log_root / f"{build_id}.log"
    log = BuildLogger(build_id, log_path)
    update_build(
        build_id,
        log_path=str(log_path),
        started_at=datetime.now(UTC),
        celery_task_id=self.request.id,
    )
    try:
        free_bytes = shutil.disk_usage(settings.data_root).free
        if free_bytes < settings.min_free_disk_gb * 1024**3:
            raise BuildExecutionError("DISK_LOW", "服务器可用磁盘空间不足")
        with SessionLocal() as db:
            build = db.scalar(
                select(BuildJob)
                .options(selectinload(BuildJob.project).selectinload(Project.credential))
                .where(BuildJob.id == build_id)
            )
            if not build:
                raise BuildExecutionError("BUILD_NOT_FOUND", "构建任务不存在")
            project = build.project
            if build.cancel_requested:
                raise BuildCanceled("任务在执行前已取消")
            timeout_seconds = project.timeout_minutes * 60
            update_build(build_id, status=BuildStatus.cloning)
            workspace.mkdir(parents=True, exist_ok=False)
            log(f"开始构建项目 {project.name}")
            commit_sha = clone_ref(
                project.git_url,
                build.requested_ref,
                source_dir,
                project.credential,
                settings.credential_temp_root,
                log,
            )
            update_build(build_id, commit_sha=commit_sha)
            build.commit_sha = commit_sha
            log(f"检出提交：{commit_sha}")
            chown_tree(source_dir)
            if build.install_strategy != InstallStrategy.none:
                update_build(build_id, status=BuildStatus.installing)
                log(f"安装项目依赖：{build.install_strategy.value}")
                run_builder_container(
                    build_id,
                    source_host_path,
                    INSTALL_COMMANDS[build.install_strategy],
                    {},
                    False,
                    timeout_seconds,
                    log,
                )
            if is_canceled(build_id):
                raise BuildCanceled("用户取消构建")
            update_build(build_id, status=BuildStatus.building)
            log(f"开始执行 Vue {build.vue_version} App WGT 编译")
            run_builder_container(
                build_id,
                source_host_path,
                ["build-wgt"],
                {
                    "VUE_VERSION": build.vue_version,
                    "NODE_MEMORY_MB": str(project.node_memory_mb),
                    "UNI_INPUT_DIR": "/workspace",
                    "UNI_OUTPUT_DIR": "/workspace/wgt-dist",
                },
                True,
                timeout_seconds,
                log,
            )
            update_build(build_id, status=BuildStatus.packaging)
            log("正在打包 WGT")
            artifact = package_wgt(project, build, source_dir, log)
            db.add(artifact)
            db.commit()
        update_build(
            build_id,
            status=BuildStatus.succeeded,
            finished_at=datetime.now(UTC),
            error_code=None,
            error_summary=None,
        )
        log("构建成功")
        cleanup_project_builds.delay(project.id)
    except BuildCanceled as exc:
        update_build(
            build_id,
            status=BuildStatus.canceled,
            finished_at=datetime.now(UTC),
            error_summary=str(exc),
        )
        log(f"构建已取消：{exc}")
    except GitOperationError as exc:
        update_build(
            build_id,
            status=BuildStatus.failed,
            finished_at=datetime.now(UTC),
            error_code="GIT_FAILED",
            error_summary="仓库拉取失败，请检查地址、Ref 和凭据",
        )
        log(f"Git 失败：{exc}")
    except BuildExecutionError as exc:
        update_build(
            build_id,
            status=BuildStatus.failed,
            finished_at=datetime.now(UTC),
            error_code=exc.code,
            error_summary=str(exc),
        )
        log(f"构建失败：{exc}")
    except Exception as exc:
        update_build(
            build_id,
            status=BuildStatus.failed,
            finished_at=datetime.now(UTC),
            error_code="INTERNAL_ERROR",
            error_summary="构建服务内部错误",
        )
        log(f"未预期错误：{type(exc).__name__}: {exc}")
        raise
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


@shared_task(name="app.tasks.cleanup_project_builds")
def cleanup_project_builds(project_id: str):
    settings = get_settings()
    with SessionLocal() as db:
        completed = list(
            db.scalars(
                select(BuildJob)
                .options(selectinload(BuildJob.artifact))
                .where(
                    BuildJob.project_id == project_id,
                    BuildJob.status.in_(
                        [BuildStatus.succeeded, BuildStatus.failed, BuildStatus.canceled]
                    ),
                )
                .order_by(BuildJob.finished_at.desc())
            ).unique()
        )
        for build in completed[settings.build_retention_count :]:
            if build.log_path:
                Path(build.log_path).unlink(missing_ok=True)
                build.log_path = None
            if build.artifact:
                Path(build.artifact.storage_path).unlink(missing_ok=True)
                db.delete(build.artifact)
        db.commit()


@shared_task(name="app.tasks.cleanup_old_builds")
def cleanup_old_builds():
    with SessionLocal() as db:
        project_ids = list(db.scalars(select(Project.id)))
    for project_id in project_ids:
        cleanup_project_builds(project_id)


@shared_task(name="app.tasks.recover_orphaned_builds")
def recover_orphaned_builds():
    threshold = datetime.now(UTC) - timedelta(hours=4)
    active = [
        BuildStatus.cloning,
        BuildStatus.installing,
        BuildStatus.building,
        BuildStatus.packaging,
        BuildStatus.canceling,
    ]
    with SessionLocal() as db:
        builds = list(
            db.scalars(
                select(BuildJob).where(BuildJob.status.in_(active), BuildJob.updated_at < threshold)
            )
        )
        for build in builds:
            build.status = BuildStatus.failed
            build.error_code = "WORKER_LOST"
            build.error_summary = "Worker 长时间未更新任务，已自动收敛"
            build.finished_at = datetime.now(UTC)
            shutil.rmtree(get_settings().workspace_root / build.id, ignore_errors=True)
        db.commit()
