from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import BuildStatus, CredentialType, InstallStrategy, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(ORMModel):
    id: str
    username: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=10, max_length=128)
    role: UserRole = UserRole.member


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=10, max_length=128)


class CredentialCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    type: CredentialType
    username: str | None = None
    secret: str = Field(min_length=1)
    known_hosts: str | None = None


class CredentialUpdate(BaseModel):
    name: str | None = None
    username: str | None = None
    secret: str | None = None
    known_hosts: str | None = None


class CredentialOut(ORMModel):
    id: str
    name: str
    type: CredentialType
    username: str | None
    known_hosts: str | None
    created_at: datetime
    updated_at: datetime


class ProjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    git_url: str = Field(min_length=5, max_length=1000)
    default_ref: str = Field(default="main", min_length=1, max_length=255)
    vue_version: str = "3"
    install_strategy: InstallStrategy = InstallStrategy.none
    node_memory_mb: int = Field(default=2048, ge=512, le=8192)
    timeout_minutes: int = Field(default=30, ge=5, le=180)
    is_active: bool = True
    credential_id: str | None = None

    @field_validator("vue_version")
    @classmethod
    def validate_vue_version(cls, value: str) -> str:
        if value not in {"2", "3"}:
            raise ValueError("vue_version must be 2 or 3")
        return value


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    git_url: str | None = None
    default_ref: str | None = None
    vue_version: str | None = None
    install_strategy: InstallStrategy | None = None
    node_memory_mb: int | None = Field(default=None, ge=512, le=8192)
    timeout_minutes: int | None = Field(default=None, ge=5, le=180)
    is_active: bool | None = None
    credential_id: str | None = None

    @field_validator("vue_version")
    @classmethod
    def validate_vue_version(cls, value: str | None) -> str | None:
        if value is not None and value not in {"2", "3"}:
            raise ValueError("vue_version must be 2 or 3")
        return value


class ProjectOut(ORMModel):
    id: str
    name: str
    git_url: str
    default_ref: str
    vue_version: str
    install_strategy: InstallStrategy
    node_memory_mb: int
    timeout_minutes: int
    is_active: bool
    credential_id: str | None
    created_at: datetime
    updated_at: datetime


class BuildCreate(BaseModel):
    project_id: str
    ref: str | None = Field(default=None, max_length=255)
    vue_version: str | None = None
    install_strategy: InstallStrategy | None = None

    @field_validator("vue_version")
    @classmethod
    def validate_vue_version(cls, value: str | None) -> str | None:
        if value is not None and value not in {"2", "3"}:
            raise ValueError("vue_version must be 2 or 3")
        return value


class ArtifactOut(ORMModel):
    id: str
    filename: str
    size_bytes: int
    sha256: str
    created_at: datetime


class BuildOut(ORMModel):
    id: str
    project_id: str
    requested_by_id: str
    requested_ref: str
    commit_sha: str | None
    vue_version: str
    install_strategy: InstallStrategy
    status: BuildStatus
    error_code: str | None
    error_summary: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    cancel_requested: bool
    artifact: ArtifactOut | None = None


class AuditOut(ORMModel):
    id: str
    user_id: str | None
    action: str
    target_type: str | None
    target_id: str | None
    detail: str | None
    created_at: datetime


TokenResponse.model_rebuild()
