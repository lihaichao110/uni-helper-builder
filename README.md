# Uni WGT Builder

一个面向内部团队的 uni-app WGT 构建平台。React 页面负责项目配置和构建操作，FastAPI/Celery 负责从 Git 拉取源码、调用隔离的 HBuilderX Core 容器、推送实时日志并保存 WGT 产物。

## 已实现能力

- 管理员与普通成员登录、JWT 刷新和角色权限。
- 通用 HTTPS/SSH Git 仓库，项目级加密凭据和 `known_hosts` 强校验。
- Vue 2、Vue 3 项目参数和 npm/Yarn/pnpm 安装策略。
- Celery 串行队列、同项目并发保护、幂等创建和任务取消。
- 一次性非 root Docker 构建容器，资源限制和正式编译断网。
- 实时 WebSocket 日志、WGT 下载、SHA-256 和审计记录。
- 每个项目仅保留最近 10 次构建日志与产物。
- React 仪表盘、项目、凭据、构建、用户和审计页面。

## 目录

```text
backend/        FastAPI、Celery、SQLAlchemy、测试和 Alembic
frontend/       React、TypeScript、Ant Design
builder-image/  HBuilderX Core Linux 构建镜像骨架
docker-compose.yml
```

## 1. 准备 HBuilderX Core 镜像

仓库不会分发 HBuilderX 编译插件。请在合法安装 HBuilderX 后，先分别创建 Vue 2、Vue 3 项目并完成一次真机运行，让所需插件安装完整。

在 Linux/macOS 上执行：

```bash
cd builder-image
chmod +x prepare-core.sh build-wgt.sh
./prepare-core.sh /path/to/HBuilderX/plugins
docker build -t uni-builder-core:4.15.0-r1 .
```

如果插件来自 Windows，请在 Linux 上执行准备脚本，或确认复制后文件权限和 Linux 原生依赖均已正确替换。镜像可在没有 Core 的情况下构建，但实际任务会明确报出缺失的 CLI 路径。

## 2. 配置服务器

要求：Linux x86-64、Docker Engine、Docker Compose Plugin。建议至少 4 核、8 GB 内存和足够的构建磁盘。

```bash
cp .env.example .env
mkdir -p /opt/uni-builder/data
chmod 700 /opt/uni-builder/data
```

必须修改 `.env` 中的数据库密码、两个独立密钥和初始管理员密码。`HOST_DATA_ROOT` 必须是宿主机绝对路径；Worker 会把其中的单个任务源码目录挂载给 Builder 容器。

首次启动：

```bash
docker compose build
docker compose run --rm api alembic upgrade head
docker compose up -d
```

访问 `http://服务器地址:8080`，使用 `.env` 中的初始管理员登录。正式部署应在 Web 服务前配置 HTTPS，并将 `FRONTEND_ORIGIN` 改成真实 HTTPS 地址。

## 3. 添加仓库与构建

1. 管理员在“仓库凭据”中添加项目级只读 SSH Key 或 HTTPS Token。
2. SSH 凭据必须粘贴经过管理员核对的 `known_hosts` 内容。
3. 新建项目，明确选择 Vue 版本、默认 Ref 和依赖安装策略。
4. 测试仓库连接。
5. 在“构建任务”中新建任务并观察实时日志。
6. 成功后下载 `.wgt` 并校验页面提供的 SHA-256。

## 本地开发

后端默认可使用 SQLite，但 Celery 构建仍需要 Redis 和 Docker：

```bash
cd backend
uv venv --python 3.12
uv sync
uv run python -m app.main --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

测试：

```bash
cd backend
uv run python -m pytest
cd ../frontend
npm run build
```

## 安全与运维说明

- API 容器不接触 Docker Socket，只有 Worker 可以启动构建容器。
- Worker 的 Docker Socket 权限等价于宿主机高权限，应部署在专用构建机并限制平台管理员。
- 不允许用户配置任意 Shell 预构建命令；项目源码本身仍属于待执行代码，必须把仓库成员视为受信任开发者。
- Builder 正式编译阶段禁用网络，依赖安装阶段按项目策略临时联网。
- Token 和私钥仅以 AES-GCM 密文入库，任务期间临时解密且不会写入构建日志。
- 修改 `CREDENTIAL_ENCRYPTION_KEY` 前必须先迁移已有密文，否则旧凭据将无法解密。
- 当前第一版只支持单 Worker 串行构建和 App WGT，不提供 APK、IPA、Webhook 或 Kubernetes 调度。

