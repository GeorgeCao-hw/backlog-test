# backlog — Phase 1.1 需求驱动 + Phase 4 故障复盘

> 定位：需求/缺陷 Issue 管理、AI 文档产出（需求分析/架构设计/测试策略）、统一产物目录的单一事实来源。
> 详见 workflow-control-tower 仓库的 `team-end-to-end-process.md` §三 Phase 1.1。

## 关键规则

### Issue 管理

- 需求 Issue 按 Feature Request 模板提，经 RAT（不含 PM）技术评审决策
- 缺陷 Issue 在**项目代码仓库**提交（非本仓库），按 Bug Report 模板
- RAT 评审通过后，maintainer 在 issue 评论输入 `/accepts` 触发 workflow

### Issue 触发词

| 触发词       | 作用                                                 |
| ------------ | ---------------------------------------------------- |
| `/accepts`   | RAT 评审通过，进入开发流程                           |
| `[需求分析]` | 触发 requirements agent 写 01-requirements.md        |
| `[架构设计]` | 触发 architecture-design agent 写 02-architecture.md |
| `[测试策略]` | 触发 test-strategy agent 写 03-test-strategy.md      |
| `[需求实现]` | Dispatch 到 umbrella 仓进入 Phase 2                  |

### 产物目录

- 需求 Issue 产物统一写入 `issue_docs/<issueId>/`，该目录是端到端单一事实来源
- `00-user-brief.md` 由 workflow 自动生成，**Agent 只读**
- 每个阶段产物写入对应编号文件（详见 README）

### Agent 行为

- 见 `AGENTS.md`
- Agent 行为硬约束（禁止 push main、禁止修改非授权文件等）必须遵守
- QA agent 只读前置产物，产出写到同目录 qa 文件

### 工作流程

1. PM 按 Feature Request 模板提 Issue
2. RAT 技术评审（不含 PM）
3. maintainer `/accepts` → workflow 触发
4. AI 写需求文档 PR → 人评审合入
5. AI 需求 QA → 并行启动架构设计 + 测试策略
6. AI 架构 QA + 测试策略 QA
7. 前置条件满足 → dispatch 到 umbrella 仓

## 团队规范层引用

- 团队层规范: agent-development-specification 仓库
- 流程权威文档: workflow-control-tower/team-end-to-end-process.md

## 提交前校验

提交前请手动检查 Markdown 格式：

```bash
# 检查格式（CI 在 PR 时自动执行）
npx prettier --check "**/*.md"

# 自动修复格式问题
npx prettier --write "**/*.md"
```

CI（`.github/workflows/markdown-format-check.yml`）在 PR 和 push main 时自动校验 markdown 格式。
