from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Uni WGT Builder"
    environment: str = "development"
    database_url: str = "sqlite:///./uni_builder.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-this-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    credential_encryption_key: str = "change-this-credential-key"
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "ChangeMe123!"
    data_root: Path = Path("./data")
    host_data_root: Path = Path("./data")
    builder_image: str = "uni-builder-core:4.15.0-r1"
    build_cpu_count: int = 2
    build_memory: str = "4g"
    build_retention_count: int = 10
    min_free_disk_gb: float = 2.0
    frontend_origin: str = "http://localhost:3000"

    @property
    def workspace_root(self) -> Path:
        return self.data_root / "workspaces"

    @property
    def host_workspace_root(self) -> Path:
        return self.host_data_root / "workspaces"

    @property
    def log_root(self) -> Path:
        return self.data_root / "logs"

    @property
    def artifact_root(self) -> Path:
        return self.data_root / "artifacts"

    @property
    def credential_temp_root(self) -> Path:
        return self.data_root / "credentials-temp"


@lru_cache
def get_settings() -> Settings:
    return Settings()
