import asyncio
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from ..celery_app import celery_app
from ..config import get_settings
from ..database import SessionLocal, get_db
from ..dependencies import get_current_user, get_user_from_access_token
from ..models import (
    ACTIVE_BUILD_STATUSES,
    Artifact,
    BuildJob,
    BuildStatus,
    Project,
    User,
    UserRole,
)
from ..schemas import BuildCreate, BuildOut
from ..services import write_audit

router = APIRouter(tags=["构建"])


def build_query() -> Select[tuple[BuildJob]]:
    return select(BuildJob).options(selectinload(BuildJob.artifact))


def get_build_or_404(db: Session, build_id: str) -> BuildJob:
    build = db.scalar(build_query().where(BuildJob.id == build_id))
    if not build:
        raise HTTPException(status_code=404, detail="构建任务不存在")
    return build


@router.get("/builds", response_model=list[BuildOut])
def list_builds(
    project_id: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = build_query().order_by(BuildJob.created_at.desc()).limit(200)
    if project_id:
        query = query.where(BuildJob.project_id == project_id)
    return list(db.scalars(query).unique())


@router.post("/builds", response_model=BuildOut, status_code=202)
def create_build(
    payload: BuildCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if idempotency_key:
        existing = db.scalar(build_query().where(BuildJob.idempotency_key == idempotency_key))
        if existing:
            return existing
    project = db.get(Project, payload.project_id)
    if not project or not project.is_active:
        raise HTTPException(status_code=404, detail="项目不存在或已停用")
    active = db.scalar(
        select(BuildJob.id).where(
            BuildJob.project_id == project.id,
            BuildJob.status.in_(ACTIVE_BUILD_STATUSES),
        )
    )
    if active:
        raise HTTPException(status_code=409, detail="该项目已有排队或运行中的任务")
    build = BuildJob(
        project_id=project.id,
        requested_by_id=user.id,
        requested_ref=payload.ref or project.default_ref,
        vue_version=payload.vue_version or project.vue_version,
        install_strategy=payload.install_strategy or project.install_strategy,
        idempotency_key=idempotency_key,
    )
    db.add(build)
    db.flush()
    write_audit(db, user, "build.create", "build", build.id, {"project_id": project.id})
    db.commit()
    try:
        task = celery_app.send_task("app.tasks.execute_build", args=[build.id])
    except Exception as exc:
        build.status = BuildStatus.failed
        build.error_code = "QUEUE_UNAVAILABLE"
        build.error_summary = "任务队列暂不可用，请稍后重试"
        db.commit()
        raise HTTPException(status_code=503, detail=build.error_summary) from exc
    build.celery_task_id = task.id
    db.commit()
    return get_build_or_404(db, build.id)


@router.get("/builds/{build_id}", response_model=BuildOut)
def get_build(build_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_build_or_404(db, build_id)


@router.post("/builds/{build_id}/cancel", response_model=BuildOut)
def cancel_build(
    build_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    build = get_build_or_404(db, build_id)
    if user.role != UserRole.admin and build.requested_by_id != user.id:
        raise HTTPException(status_code=403, detail="只能取消自己的构建")
    if build.status not in ACTIVE_BUILD_STATUSES:
        raise HTTPException(status_code=409, detail="当前状态不能取消")
    build.cancel_requested = True
    build.status = BuildStatus.canceling
    write_audit(db, user, "build.cancel", "build", build.id)
    db.commit()
    return get_build_or_404(db, build.id)


@router.get("/builds/{build_id}/logs")
def get_build_logs(
    build_id: str,
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    build = get_build_or_404(db, build_id)
    if not build.log_path or not Path(build.log_path).exists():
        return {"content": "", "offset": 0}
    path = Path(build.log_path)
    with path.open("rb") as handle:
        handle.seek(offset)
        content = handle.read(1024 * 512)
        new_offset = handle.tell()
    return {"content": content.decode("utf-8", errors="replace"), "offset": new_offset}


@router.websocket("/builds/{build_id}/logs/stream")
async def stream_build_logs(
    websocket: WebSocket, build_id: str, token: str = Query(...), offset: int = Query(0)
):
    with SessionLocal() as db:
        user = get_user_from_access_token(token, db)
        build = db.get(BuildJob, build_id)
        if not user or not build:
            await websocket.close(code=4401)
            return
        log_path = build.log_path
    await websocket.accept()
    if log_path and Path(log_path).exists():
        with Path(log_path).open("rb") as handle:
            handle.seek(offset)
            chunk = handle.read()
            if chunk:
                await websocket.send_text(chunk.decode("utf-8", errors="replace"))
    redis_client = aioredis.from_url(get_settings().redis_url)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"build-log:{build_id}")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = message["data"]
                await websocket.send_text(data.decode() if isinstance(data, bytes) else str(data))
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"build-log:{build_id}")
        await pubsub.close()
        await redis_client.close()


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    artifact = db.get(Artifact, artifact_id)
    if not artifact or not Path(artifact.storage_path).is_file():
        raise HTTPException(status_code=404, detail="产物不存在")
    write_audit(db, user, "artifact.download", "artifact", artifact.id)
    db.commit()
    return FileResponse(
        artifact.storage_path, filename=artifact.filename, media_type="application/octet-stream"
    )
