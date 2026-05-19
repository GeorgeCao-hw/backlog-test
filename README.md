# backlog 仓库

> Phase 1.1 需求驱动 + Phase 4 故障复盘  
> 端到端文档主仓：需求 Issue 入口 → AI 文档产出 → 统一产物目录

## 定位

- `issue_docs/<issueId>/` 是全流程的**单一事实来源**
- Phase 1.1 需求驱动流程的全部文档在此产出（需求分析/架构设计/测试策略）
- Phase 4 故障复盘文档在此归档
- 变更发布规划**已迁移到 release-mgmt 仓库**

## 仓库结构

```
backlog/
├── README.md
├── CLAUDE.md                        # 项目 Claude 上下文
├── AGENTS.md                        # AI Agent 入职手册
├── .claude/
│   ├── settings.json                # Hooks 配置
│   └── commands/                    # AI 辅助 Skill
├── .github/
│   ├── ISSUE_TEMPLATE/              # Issue 模板
│   ├── workflows/                   # CI 工作流
│   └── actions/                     # 可复用 actions
├── context/                         # 团队知识库
│   ├── team/                        # 团队通用知识（安全规范、工作流指南）
│   ├── experience/                  # 踩坑经验
│   └── business/                    # 业务逻辑规则
├── templates/                       # 文档模板（按类型分目录，含 README 说明）
│   ├── Requirement Analysis/        # 需求分析说明书
│   ├── Architecture Design/         # 架构设计说明书
│   ├── Test/                        # 测试策略 + 测试报告
│   ├── Bug Report/                  # 缺陷报告
│   ├── Release/                     # 变更计划（已迁移到 release-mgmt）
│   └── Learn From the Incident/     # 故障复盘
└── <org>/<project>/issue_docs/      # Issue 交付件归档
    └── <issueId>/
        ├── 00-user-brief.md         # workflow 自动生成（只读）
        ├── 01-requirements.md       # 需求分析
        ├── 01-requirements-qa.md    # 需求 QA
        ├── 02-architecture.md       # 架构设计
        ├── 02-architecture-qa.md    # 架构 QA
        ├── 03-test-strategy.md      # 测试策略
        ├── 03-test-strategy-qa.md   # 测试策略 QA
        ├── 04-deploy-notes.md       # 部署注意事项
        ├── 05-upgrade-guide.md      # 升级指导
        ├── 05-upgrade-guide-qa.md   # 升级指导 QA
        └── MANIFEST.md              # 文件清单与状态
```

## 开发流程

**Phase 1.1 — 需求驱动**：
```
Issue 创建 → RAT 评审 → 需求分析 → 需求 QA → 架构设计 + 测试策略(并行) → 架构 QA + 测试策略 QA → Phase 2
```

**Phase 4 — 故障复盘**（按需触发）：
```
故障发生 → 复盘报告 → 改进措施跟踪
```

## 需求相关性标签

需求分析阶段通过勾选清单确定标签，标签决定后续文档产出：

| 标签 | 触发条件 | 后续文档 |
|------|----------|----------|
| `need_security` | 边界变更/凭证/权限/供应链/隐私/AI | 架构设计（含安全威胁分析） |
| `need_design` | 拓扑变更/API 变更/新中间件 | 架构设计 |
| `need_itest` | 跨组件影响/核心组件/端到端流程 | 测试策略 + 测试报告 |
| `need_ux` | 交互变更/性能变动/文档变更/无障碍 | 架构设计（含 UX 设计） |
| `need_light` | 以上均不涉及 | 无额外文档，快速合入 |

## Issue 交付件归档

每个 Issue 的文档归档在 `<org>/<project>/issue_docs/<issueId>/` 下，使用统一编号命名（如 `01-requirements.md`）。

`MANIFEST.md` 记录文件清单和阶段完成状态。

## 关键边界调整

- 变更发布规划 → **已迁移到 release-mgmt 仓库**
- `templates/Release/` → 保留模板参考，实际发布流程在 release-mgmt
- backlog 只保留：需求分析、架构设计、测试策略、故障复盘

## AI 辅助开发

通过 Claude Code 自定义命令实现：

- `/ai-design <Issue URL 或 issueId>` — 自动判断当前阶段，完成对应文档编写
- `/code-review <PR 编号或 PR URL>` — 结构化代码检视

AI 工作时会：
1. 读取 `AGENTS.md` 了解项目规范
2. 参考 `context/experience/` 中的历史经验
3. 按 `templates/` 中的模板格式输出
4. 完成后沉淀新经验到 `context/experience/`

## 知识库贡献

团队知识沉淀在 `context/` 目录下：

| 信息类型 | 放哪里 | 示例 |
|----------|--------|------|
| 踩坑经验 | `context/experience/` | "验收标准必须可量化" |
| 业务规则 | `context/business/` | "需求相关性标签判定逻辑" |
| 团队知识 | `context/team/` | "文档 review 流程" |
