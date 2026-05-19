# AGENTS.md

## 项目背景

这是 agentic-develop-playground 组织的 backlog 管理仓库，作为 Phase 1.1 需求驱动 + Phase 4 故障复盘的端到端文档主仓。

仓库核心功能：
- 需求全生命周期文档管理（需求分析 → 架构设计 → 测试策略）
- 团队知识沉淀与经验共享
- AI 辅助开发的提示词与工具管理
- `issue_docs/<issueId>/` 是全流程的**单一事实来源**

## 仓库结构

```
backlog/
├── AGENTS.md                    # AI 的"入职手册"（本文件）
├── CLAUDE.md                    # 项目 Claude 上下文
├── README.md                    # 仓库说明
├── .claude/
│   ├── settings.json            # Hooks 配置
│   └── commands/                # Claude Code 自定义命令（Skill）
├── .github/
│   ├── ISSUE_TEMPLATE/          # Issue 模板
│   ├── workflows/               # CI 工作流
│   └── actions/                 # 可复用 actions
├── context/                     # 团队知识库
│   ├── team/                    # 团队通用知识（安全规范、API 安全、工作流指南）
│   ├── experience/              # 踩坑经验（需求分析/架构设计/测试策略编写经验）
│   └── business/                # 业务逻辑规则（各项目领域知识）
├── templates/                   # 文档模板（按类型分目录，含 README 说明）
│   ├── Requirement Analysis/    # 需求分析说明书模板
│   ├── Architecture Design/     # 架构设计说明书模板
│   ├── Test/                    # 测试策略 + 测试报告模板
│   ├── Bug Report/              # 缺陷报告模板
│   ├── Release/                 # 变更计划模板（已迁移到 release-mgmt，此处保留参考）
│   └── Learn From the Incident/ # 故障复盘报告模板
└── <org>/<project>/issue_docs/  # Issue 交付件归档（Agent 运行时产出）
    └── <issueId>/
        ├── 00-user-brief.md         # workflow 自动生成（只读）
        ├── 01-requirements.md       # 需求分析说明书
        ├── 01-requirements-qa.md    # 需求 QA 报告
        ├── 02-architecture.md       # 架构设计说明书
        ├── 02-architecture-qa.md    # 架构 QA 报告
        ├── 03-test-strategy.md      # 测试策略
        ├── 03-test-strategy-qa.md   # 测试策略 QA 报告
        ├── 04-deploy-notes.md       # 部署注意事项
        ├── 05-upgrade-guide.md      # 升级指导
        ├── 05-upgrade-guide-qa.md   # 升级指导 QA 报告
        └── MANIFEST.md              # 文件清单与状态
```

## 工作规范

### 需求文档生命周期

每个需求 Issue 按以下阶段推进，产出文档归档到 `<org>/<project>/issue_docs/<issueId>/`：

1. **需求分析**：输出 `01-requirements.md`，完成需求相关性分析（安全/架构/测试），确定需要打的标签
2. **需求 QA**：输出 `01-requirements-qa.md`，检查需求文档的完整性和可测试性
3. **架构设计**（need_design 或 need_security 触发）：输出 `02-architecture.md`（含安全威胁分析）
4. **架构 QA**：输出 `02-architecture-qa.md`
5. **测试策略**（need_itest 触发）：输出 `03-test-strategy.md`（含验证矩阵）
6. **测试策略 QA**：输出 `03-test-strategy-qa.md`
7. **变更发布**（已迁移到 release-mgmt 仓库）：`04-deploy-notes.md` + `05-upgrade-guide.md`
8. **故障复盘**：按需在 `Learn From the Incident/` 下归档

### 需求相关性标签体系

| 标签 | 含义 | 触发条件 |
|------|------|----------|
| `need_security` | 需架构设计（含安全威胁分析） | 涉及边界变更/凭证处理/权限调整/供应链/隐私/AI |
| `need_design` | 需架构设计 | 拓扑变更/API 变更/新中间件/need_security 触发 |
| `need_itest` | 需测试策略 | 需安全或架构设计/跨组件影响/核心组件/端到端流程 |
| `need_ux` | 需 UX 设计 | 交互变更/性能变动/文档变更/无障碍 |
| `need_light` | 轻量化特性，走快速合入通道 | 以上均未勾选 |

### 文档编写规范

- 先读模板再写，严格遵循模板结构
- 验收标准必须**可量化、可测试**
- 勾选相关性分析时**必须给出原因**
- 任务拆解到**原子级别**，每个 Task 可独立交付
- 不确定的地方先标注 `[TODO]`，后续补充
- 文件名使用统一编号（`01-requirements.md` 等）

### AI 注意事项

- 产物统一写入 `issue_docs/<issueId>/` 下对应编号文件
- `00-user-brief.md` 由 workflow 自动生成，Agent **只读**
- QA agent 只读前置产物，产出写到同目录 qa 文件
- 需求分析只做简要分析，不做具体设计；Task 控制在 2-4 个
- 需求分析阶段只产出需求分析说明书，不创建其他模板文件
- 需求分析中的"价值识别与业务评估"必须给出 Accept/Reject/Pending 结论
- 使用 `gh` CLI 获取 GitHub Issue 信息，不要猜测 Issue 内容

## Agent 文件写权限矩阵

> 每个 Agent **只能写入**自己职责范围内的文件。此约束由 workflow 文件路径校验强制执行。

| Agent | 阶段 | 可写文件 | 只读文件 |
|-------|------|----------|----------|
| `issue-refinement` | 1.1.1b | issue 评论 | issue 模板、CLAUDE.md、context/experience/ |
| `requirements` | 1.1.3 | `issue_docs/<issueId>/01-requirements.md` | `00-user-brief.md`、CLAUDE.md、`context/experience/` |
| `requirements-qa` | 1.1.3b | `issue_docs/<issueId>/01-requirements-qa.md` | `01-requirements.md`、`00-user-brief.md` |
| `architecture-design` | 1.1.4 | `issue_docs/<issueId>/02-architecture.md` | `01-requirements.md` |
| `architecture-qa` | 1.1.4b | `issue_docs/<issueId>/02-architecture-qa.md` | `02-architecture.md`、`01-requirements.md` |
| `test-strategy` | 1.1.5 | `issue_docs/<issueId>/03-test-strategy.md` | `01-requirements.md`、`02-architecture.md` |
| `test-strategy-qa` | 1.1.5b | `issue_docs/<issueId>/03-test-strategy-qa.md` | `03-test-strategy.md`、`01-requirements.md` |

## Agent 行为硬约束

| # | 约束 | 原因 |
|---|------|------|
| 1 | Agent **禁止**直接 push `main` 分支 | 防止 AI 绕过 PR review |
| 2 | Agent **禁止**执行 `gh pr merge` | PR 合入由人工决策 |
| 3 | Agent **禁止**修改非授权文件 | 防止跨阶段产物污染 |
| 4 | Agent **禁止**修改已完成阶段的产物 | 保证每个阶段的输出是不可变的输入 |
| 5 | Agent **禁止**绕过 QA 阶段直接推进 | QA 是每个阶段的默认门禁 |
| 6 | Agent 只能推送到 feature 分支：`agentic/issue-<issueId>` | 多 Issue 并行隔离 |
| 7 | Agent **禁止**调用外部 API 或未授权网络资源 | 安全边界 |

## 知识检索规则

### 何时查 `context/team/`
- 涉及安全编码、API 安全等**安全规范**时
- 涉及 Git 分支、PR、文档 review 等**协作流程**时
- 需要了解团队工具使用或基础设施时

### 何时查 `context/experience/`
- 开始编写任何文档**之前**，先检查是否有同类经验
- 遇到不确定的判断时，检查是否有历史踩坑记录
- 完成工作**之后**，将新经验追加到此目录

### 何时查 `context/business/`
- 编写需求分析时，需要了解**该项目的业务背景和规则**
- 做需求相关性分析时，需要判断**业务影响范围**

### 检索方式
1. 先 `ls context/{team,experience,business}/` 看有什么文件
2. 根据文件名判断相关性
3. 读取相关文件获取知识

## 常见坑点

| 坑点 | 错误做法 | 正确做法 |
|------|----------|----------|
| 相关性分析遗漏 | 未勾选触发项 | 根据 Task 影响逐项检查勾选 |
| 验收标准模糊 | "功能正常工作" | "响应时间 < xxx ms，覆盖率 > xx%" |
| 文件名错误 | 使用 `#N` 前缀 | 使用统一编号 `01-requirements.md` 等 |
| 需求分析写设计 | 详细描述实现方案 | 只做简要分析，具体设计留给架构设计 |
| QA 跳过 | 直接推进 | QA 是每个阶段的默认门禁 |

## 可用命令

- `/ai-design <Issue URL 或 issueId>`：DevOps 全生命周期文档编写（需求分析 → 架构设计 → 测试策略），自动判断当前阶段
- `/code-review <PR 编号或 PR URL>`：对指定 PR 进行结构化代码检视
