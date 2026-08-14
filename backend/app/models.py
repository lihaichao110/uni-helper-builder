import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class CredentialType(str, enum.Enum):
    ssh = "ssh"
    https_token = "https-token"


class InstallStrategy(str, enum.Enum):
    none = "none"
    npm_ci = "npm-ci"
    yarn_frozen = "yarn-frozen"
    pnpm_frozen = "pnpm-frozen"


class BuildStatus(str, enum.Enum):
    queued = "queued"
    cloning = "cloning"
    installing = "installing"
    building = "building"
    packaging = "packaging"
    succeeded = "succeeded"
    failed = "failed"
    canceling = "canceling"
    canceled = "canceled"


ACTIVE_BUILD_STATUSES = {
    BuildStatus.queued,
    BuildStatus.cloning,
    BuildStatus.installing,
    BuildStatus.building,
    BuildStatus.packaging,
    BuildStatus.canceling,
}


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), default=UserRole.member
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RepositoryCredential(TimestampMixin, Base):
    __tablename__ = "repository_credentials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), unique=True)
    type: Mapped[CredentialType] = mapped_column(Enum(CredentialType, native_enum=False))
    username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    encrypted_secret: Mapped[str] = mapped_column(Text)
    known_hosts: Mapped[str | None] = mapped_column(Text, nullable=True)
    projects: Mapped[list["Project"]] = relationship(back_populates="credential")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    git_url: Mapped[str] = mapped_column(String(1000))
    default_ref: Mapped[str] = mapped_column(String(255), default="main")
    vue_version: Mapped[str] = mapped_column(String(1), default="3")
    install_strategy: Mapped[InstallStrategy] = mapped_column(
        Enum(InstallStrategy, native_enum=False), default=InstallStrategy.none
    )
    node_memory_mb: Mapped[int] = mapped_column(Integer, default=2048)
    timeout_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    credential_id: Mapped[str | None] = mapped_column(
        ForeignKey("repository_credentials.id", ondelete="SET NULL"), nullable=True
    )
    credential: Mapped[RepositoryCredential | None] = relationship(back_populates="projects")
    builds: Mapped[list["BuildJob"]] = relationship(back_populates="project")


class BuildJob(TimestampMixin, Base):
    __tablename__ = "build_jobs"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_build_idempotency_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    requested_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    requested_ref: Mapped[str] = mapped_column(String(255))
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vue_version: Mapped[str] = mapped_column(String(1))
    install_strategy: Mapped[InstallStrategy] = mapped_column(
        Enum(InstallStrategy, native_enum=False)
    )
    status: Mapped[BuildStatus] = mapped_column(
        Enum(BuildStatus, native_enum=False), default=BuildStatus.queued, index=True
    )
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    container_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    log_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project: Mapped[Project] = relationship(back_populates="builds")
    requested_by: Mapped[User] = relationship()
    artifact: Mapped["Artifact | None"] = relationship(back_populates="build", uselist=False)


class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    build_id: Mapped[str] = mapped_column(ForeignKey("build_jobs.id"), unique=True)
    filename: Mapped[str] = mapped_column(String(500))
    storage_path: Mapped[str] = mapped_column(String(1000))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    build: Mapped[BuildJob] = relationship(back_populates="artifact")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User | None] = relationship()
