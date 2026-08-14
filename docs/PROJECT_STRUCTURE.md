# Uni Builder 项目目录结构

## 维护规则

本文档描述仓库当前实际结构及各目录职责。任何目录新增、删除、移动、重命名或职责变化，都必须在同一任务内同步更新本文档。

目录树不记录 `node_modules`、虚拟环境、`__pycache__`、`.pytest_cache`、数据库文件、日志、临时工作区、构建产物和其他可再生内容。Codex 只能保证其参与的变更同步更新；发现人工改动造成偏差时，应在下一次 Codex 任务中校正。

## 当前实际结构

```text
uni-builder/
├── AGENTS.md                  # 全仓库 Codex 持久化规则
├── README.md                  # 项目介绍、部署与使用说明
├── .env.example              # 环境变量示例，不包含真实密钥
├── docker-compose.yml        # PostgreSQL、Redis、API、Worker、Scheduler、Web 编排
├── scripts/
│   └── check_source_size.py  # Python 与 TypeScript 源码行数门禁
├── docs/
│   └── PROJECT_STRUCTURE.md  # 当前目录职责与目标结构
├── backend/
│   ├── AGENTS.md             # Python/FastAPI 子树规则
│   ├── app/                  # FastAPI、Celery、SQLAlchemy 核心应用
│   │   └── routers/          # 按资源划分的 HTTP API 路由
│   ├── alembic/              # 数据库迁移环境与版本脚本
│   ├── tests/                # 后端 API 与构建流程测试
│   ├── Dockerfile            # Python 3.12 后端镜像
│   ├── requirements.txt      # 运行时依赖
│   ├── requirements-dev.txt  # 格式化、静态检查与类型检查依赖
│   ├── pyproject.toml        # Ruff、Mypy 与 Pytest 配置
│   └── alembic.ini           # Alembic 配置入口
├── frontend/
│   ├── AGENTS.md             # React/TypeScript 子树规则
│   ├── src/
│   │   ├── components/       # 当前跨页面布局组件
│   │   └── pages/            # 当前路由页面组件
│   ├── eslint.config.js      # ESLint flat config
│   ├── .prettierrc.json      # Prettier 格式配置
│   ├── package.json          # 前端依赖与质量命令
│   ├── package-lock.json     # npm 依赖锁文件
│   ├── vite.config.ts        # Vite 构建配置
│   ├── tsconfig*.json        # TypeScript 工程配置
│   ├── Dockerfile            # Node 构建与 Nginx 运行镜像
│   └── nginx.conf            # 前端静态资源及 API 代理配置
├── builder-image/
│   ├── Dockerfile            # HBuilderX Core 构建镜像
│   ├── prepare-core.sh       # Core 文件准备脚本
│   ├── patch-core.mjs        # Core 兼容性修补脚本
│   └── build-wgt.sh          # WGT 构建入口
├── outputs/                  # 本地运行产物目录，不属于源码
└── work/                     # 本地虚拟环境、日志和临时工作区，不属于源码
```

## 当前模块职责

- `backend/app/main.py`：FastAPI 生命周期、中间件与路由注册。
- `backend/app/routers/`：认证、用户、凭据、项目、构建和健康检查 API。
- `backend/app/tasks.py`：当前 Celery 构建任务及容器执行流程；接近建议规模阈值，后续新增职责前应优先拆分。
- `backend/app/models.py`、`schemas.py`：当前数据库模型与 API Schema。
- `frontend/src/App.tsx`：登录态初始化、路由和权限入口。
- `frontend/src/pages/`：仪表盘、项目、凭据、构建、用户和审计页面。
- `frontend/src/api.ts`、`store.ts`、`types.ts`：当前共享请求、状态与类型入口。

## 后端目标结构（渐进演进）

```text
backend/app/
├── api/routers/       # HTTP 协议适配与权限入口
├── core/              # 配置、安全、日志和通用基础能力
├── db/                # 会话、数据库初始化与事务基础设施
├── models/            # SQLAlchemy 持久化模型
├── schemas/           # Pydantic 输入输出模型
├── repositories/      # 数据访问与查询封装
├── services/          # 业务用例和领域编排
├── tasks/             # Celery 任务入口与任务状态推进
└── integrations/      # Git、Docker、Redis 等外部系统适配
```

仅在实际业务变更需要时创建和迁移对应目录，禁止一次性建立空目录或无收益地搬移所有文件。

## 前端目标结构（渐进演进）

```text
frontend/src/
├── app/                    # 应用启动、Provider 与路由
├── pages/                  # 路由级页面组合
├── features/<feature>/     # 按业务域组织 api、components、hooks、types、utils
├── components/             # 跨业务共享组件
├── hooks/                  # 跨业务共享 Hook
├── lib/                    # API Client、Query Client 等基础设施
├── stores/                 # 跨页面客户端状态
└── styles/                 # 全局样式、主题和设计变量
```

页面保持轻量组合；业务组件和 Hook 只在形成明确职责边界时拆分，避免过度碎片化。
