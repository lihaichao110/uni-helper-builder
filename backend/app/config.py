from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置；可经 .env 或同名大写环境变量覆盖，lru_cache 缓存后启动期间不变。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Uni WGT Builder"  # 应用名称，用于 FastAPI 文档标题等展示，无业务影响
    environment: str = "development"  # 运行环境；production 时收紧 CORS 并为 Cookie 加 secure
    cookie_secure: bool | None = (
        None  # refresh_token Cookie 的 secure 标记；None 时按 environment 推断，纯 HTTP 部署须显式设为 false
    )
    database_url: str = "sqlite:///./uni_builder.db"  # 数据库连接串；默认 SQLite，部署可覆盖
    redis_url: str = "redis://localhost:6379/0"  # Redis 地址：Celery broker、SSE 日志与健康检查
    jwt_secret: str = "change-this-jwt-secret"  # JWT 签名密钥；默认仅供开发，生产须用 .env 覆盖
    jwt_algorithm: str = "HS256"  # JWT 签名与校验算法，与 jwt_secret 配套使用
    access_token_minutes: int = 15  # 访问令牌有效期（分钟），过期后需用刷新令牌换取新令牌
    refresh_token_days: int = 7  # 刷新令牌有效期（天），同时决定 refresh_token Cookie 的 max_age
    credential_encryption_key: str = "change-this-credential-key"  # Fernet 密钥，更换后旧凭据失效
    bootstrap_admin_username: str = "admin"  # 初始管理员用户名；仅首次启动且用户不存在时创建
    bootstrap_admin_password: str = "admin"  # 初始管理员密码；仅首次创建账号时生效
    data_root: Path = Path("./data")  # 容器内数据根目录；派生工作区/日志/产物子目录，部署时为 /data
    host_data_root: Path = Path("./data")  # 宿主机数据根目录；worker 用于拼接构建容器的挂载路径
    builder_image: str = "uni-builder-core:4.15.0-r1"  # 执行 uni-app 构建所用的 Docker 镜像名及标签
    build_cpu_count: int = 2  # 单次构建容器的 CPU 核数上限（docker run --cpus）
    build_memory: str = "4g"  # 单次构建容器的内存上限（docker run --memory）
    build_retention_count: int = 10  # 构建产物保留数量，超出后由定时任务清理最旧的记录与产物
    min_free_disk_gb: float = 2.0  # 构建前宿主机磁盘最小剩余空间（GB），不足时拒绝新构建任务
    frontend_origin: str = "http://localhost:3000"  # 前端访问地址，作为后端 CORS 允许来源

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
