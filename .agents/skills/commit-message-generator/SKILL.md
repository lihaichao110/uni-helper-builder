---
name: commit-message-generator
description: Generate Conventional Commits compliant commit messages by analyzing git diff (staged or working tree). Use when the user asks to generate/write a commit message, summarize code changes for committing, or mentions commit, 提交信息, commit message.
---

# Git Commit Message 生成器

分析当前仓库变更，生成符合 Conventional Commits 规范的单行提交信息。

## 工作流程

1. **收集变更**（按优先级依次尝试）：
   ```bash
   git diff --staged --stat          # 已暂存变更（优先）
   git diff --staged                 # 已暂存完整 diff
   git status --short                # 检查是否有未暂存/未跟踪文件
   git diff                          # 未暂存变更（仅在无暂存内容时使用）
   ```
   - 若有未跟踪文件（`??` 状态），读取文件内容作为新增文件的 diff 依据。
   - 若暂存区与工作区都有变更，以暂存区为准，并可提示用户差异。
   - diff 过大时先用 `--stat` 概览，再分文件读取关键 hunks，避免输出截断。

2. **判断变更类型**：参照下方「type 选择表」选择最贴切的 type。

3. **确定 scope**：从变更涉及的模块/目录名推断（如 `auth`、`api`、`frontend`、`docs`）。跨多个不相关模块时省略 scope，直接写 `type: subject`。

4. **生成提交信息**（仅一行，无正文）：
   ```
   <type>(<scope>): <中文主题>
   ```
   - **中文主题**：用简洁的中文祈使句概括本次变更，一般不超过 25 个汉字，结尾不加句号。
   - **不输出正文**：无论变更大小，只生成单行标题，不附加 body。
   - 破坏性变更时在 type 后加 `!`，如 `feat(api)!: ...`。

## type 选择表

| type | 使用场景 |
|------|----------|
| feat | 新功能 |
| fix | 缺陷修复 |
| docs | 仅文档变更 |
| style | 不影响语义的格式调整（空格、分号等） |
| refactor | 既非新增功能也非修复的代码重构 |
| perf | 提升性能的变更 |
| test | 新增或修改测试 |
| chore | 构建过程、辅助工具变更、依赖更新等杂项 |

不确定时的优先级：缺陷修复优先 `fix`；有用户可感知的新行为用 `feat`；纯内部调整用 `refactor` 或 `chore`。

## 输出要求

- 一次只给出一条最优的提交信息（不提供多选），用代码块包裹，可直接复制使用。
- 代码块后可附 1-2 句中文说明关键判断依据（如为何选该 type/scope）。
- 严格基于 diff 内容生成，禁止臆测未在变更中体现的意图。
- 不主动执行 `git commit`，除非用户明确要求。

## 示例

**示例 1**：新增了 JWT 登录接口和中间件
```
feat(auth): 新增 JWT 登录接口与令牌校验中间件
```

**示例 2**：修复报表日期因时区错误显示的问题
```
fix(reports): 统一使用 UTC 时间戳修复日期偏移问题
```

**示例 3**：仅更新 README 中的部署说明
```
docs: 更新 README 部署说明
```

**示例 4**：接口返回码破坏性调整
```
feat(api)!: 过期令牌改为返回 401
```

## 参考

- 更多类型判断与格式细节见 [examples.md](examples.md)。
