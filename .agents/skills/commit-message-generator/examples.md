# 提交信息生成示例集

补充 SKILL.md 的进阶判断场景。所有输出均为单行「type(scope): 中文主题」格式，不附加正文。

## 混合变更的判断

一次提交同时包含多种改动时，按「最主要意图」选择 type：

- 新功能 + 配套测试 → `feat`（测试随功能一并提交）
- 缺陷修复 + 顺手格式化 → `fix`
- 重构 + 顺带修了一个小 bug → 若 bug 是主要动机则 `fix`，否则 `refactor`

**示例**：新增项目列表分页接口，同时补了测试
```
feat(projects): 新增项目列表分页接口并补充测试
```

## scope 判断

- 后端路由/服务变更：`api`、`auth`、`builds`、`users` 等（对应模块名）
- 前端页面变更：`frontend` 或具体页面名如 `login`、`dashboard`
- 构建脚本/依赖/Dockerfile：`deps`、`build`、`docker`
- CI/CD：`ci`
- 仅文档：通常省略 scope

## 常见 type 对应示例

**perf**：给热点查询加了索引
```
perf(db): 为构建列表查询添加 created_at 索引
```

**chore**：升级依赖
```
chore(deps): 升级 fastapi 至 0.111.0
```

**refactor**：抽取重复逻辑
```
refactor(git): 抽取仓库地址校验为公共方法
```

**test**：仅补测试
```
test(api): 补充凭据 CRUD 异常输入测试用例
```

**BREAKING CHANGE**：破坏性变更（type 后加 `!`）
```
feat(api)!: 过期令牌改为返回 401
```

## 反面示例（禁止）

- `fix: 修复bug` — 太泛化，应说明修了什么
- `feat(login): 新增登录功能。` — 结尾不加句号
- `update files` — 缺少 type 前缀
- 生成多行信息或附加正文
- 主题与 diff 内容不符或夸大影响
