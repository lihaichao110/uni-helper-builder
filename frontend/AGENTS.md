# 前端 React/TypeScript 企业级编码规则

## 技术与格式基线

- 使用 Node.js 20.19+、React 函数组件和 TypeScript strict；禁止用 `any` 绕过类型系统，确需使用时必须缩小边界并说明原因。
- Prettier 是唯一格式化工具，ESLint 负责代码质量、React Hooks 和热更新规则；不得添加冲突的格式化规则。
- 组件和类型使用 `PascalCase`，函数、变量和 Hook 使用 `camelCase`，自定义 Hook 必须以 `use` 开头，常量使用 `UPPER_SNAKE_CASE`。
- Props、API 响应、表单数据和 Store 状态必须有明确类型；跨模块公共类型不得重复声明。

## 组件、状态与数据流

- 页面组件只负责路由级数据装配与布局组合，不承载大型表单、表格列定义、弹窗细节或复杂业务流程。
- 具有独立职责、可复用性、可测试性或明显复杂度的 UI 拆入 feature components；复杂状态、订阅和副作用拆入 feature hooks。
- 不机械拆分只有几行、仅使用一次且没有独立语义的组件或 Hook，避免形成难以追踪的碎片层。
- 服务端状态统一交给 TanStack Query；跨页面客户端状态使用 Zustand；局部交互状态保留在组件内部。
- 请求逻辑集中在 feature api 或共享 API 层，组件不得散落重复的 URL、响应转换和错误解释。
- `useEffect` 必须声明完整依赖并清理订阅、定时器和连接；不得用 Effect 派生可在渲染阶段直接计算的状态。

## 交互、错误与安全

- 表单必须有明确校验和提交状态，异步操作必须提供加载、空数据、失败与重试反馈。
- 交互元素使用语义化标签并支持键盘操作；图标按钮必须有可访问名称。
- 不使用不受控的 `dangerouslySetInnerHTML`，不在浏览器持久化敏感凭据，不把后端错误堆栈直接展示给用户。
- 权限控制必须以后端为最终边界；前端路由和按钮隐藏只用于体验优化。

## 文件规模与拆分

- 手写 `.ts`/`.tsx` 文件建议不超过 250 行，硬上限为 300 行；生成声明、依赖和构建产物豁免。
- 超过 300 行必须按页面容器、展示组件、表单、表格列、弹窗、Hook、API、类型和纯工具函数等职责拆分。
- 拆分后保持依赖单向：页面组合 feature，feature 可依赖共享层，共享层不得反向依赖具体 feature。

## 目标目录结构

- 现有结构渐进迁移，不创建空目录。
- 应用启动、Provider 和路由放入 `src/app`；路由页面放入 `src/pages`；业务域放入 `src/features/<feature>`。
- feature 内按需使用 `api`、`components`、`hooks`、`types`、`utils`；跨业务复用内容放入 `src/components`、`src/hooks`、`src/lib`、`src/stores`、`src/styles`。

## 前端质量命令

```powershell
cd frontend
npm run check
npm run build
```
