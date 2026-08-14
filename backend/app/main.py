from contextlib import asynccontextmanager

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
