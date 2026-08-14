import argparse
import errno
import logging
import socket
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .config import get_settings
from .database import SessionLocal
from .models import User, UserRole
from .routers import auth, builds, credentials, projects, system, users
from .security import hash_password


def initialize_database() -> None:
    settings = get_settings()
    for path in (
        settings.workspace_root,
        settings.log_root,
        settings.artifact_root,
        settings.credential_temp_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.username == settings.bootstrap_admin_username)):
            db.add(
                User(
                    username=settings.bootstrap_admin_username,
                    password_hash=hash_password(settings.bootstrap_admin_password),
                    role=UserRole.admin,
                )
            )
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
allowed_origins = [settings.frontend_origin]
if settings.environment != "production":
    allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    users.router,
    credentials.router,
    projects.router,
    builds.router,
    system.router,
):
    app.include_router(router, prefix="/api")


logger = logging.getLogger("uvicorn.error")
_SEPARATOR = "=" * 70


def _port_in_use_message(host: str, port: int) -> str:
    """构造端口被占用时的醒目中文提示，包含排查命令与处理建议。"""
    return "\n".join(
        [
            _SEPARATOR,
            f"错误: 端口 {port} 已被其他进程占用，服务无法启动（地址 {host}:{port}）",
            f"排查命令: lsof -nP -iTCP:{port} -sTCP:LISTEN",
            "处理建议:",
            "  1. 确认占用进程是自己的服务后结束它: kill <PID>",
            f"  2. 或换一个端口启动: uv run python -m app.main --host {host} --port {port + 1}",
            _SEPARATOR,
        ]
    )


def check_port_available(host: str, port: int) -> None:
    """启动前预检端口占用；被占用时输出提示并以退出码 1 结束进程。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                logger.error(_port_in_use_message(host, port))
                sys.exit(1)
            raise


def main() -> None:
    """带端口占用预检的服务启动入口：uv run python -m app.main。"""
    parser = argparse.ArgumentParser(description="Uni WGT Builder 后端服务启动入口")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument("--reload", action="store_true", help="开启开发热重载")
    args = parser.parse_args()
    check_port_available(args.host, args.port)
    try:
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            logger.error(_port_in_use_message(args.host, args.port))
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
