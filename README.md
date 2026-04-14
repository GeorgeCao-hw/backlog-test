#  社区基础设施团队 Backlog

社区基础设施团队的需求与交付管理仓库，管理需求全生命周期文档（需求分析 → 架构设计 → 测试 → 发布变更 → 故障复盘），同时作为团队知识沉淀平台。

## 仓库结构

```
backlog/
├── AGENTS.md                        # AI 入职手册（项目背景、规范、标签体系）
├── README.md                        # 本文件
├── context/                         # 团队知识库
│   ├── team/                        #   团队通用知识（工作流程、工具使用）
│   ├── experience/                  #   踩坑经验（问题 → 原因 → 解决方案）
│   └── business/                    #   业务逻辑规则（各项目的领域知识）
├── templates/                       # 文档模板（标准格式，所有 Issue 共用）
│   ├── Requirement Analysis/        #   需求分析说明书模板
│   ├── Architecture Desgin/         #   架构设计说明书模板
│   ├── Test/                        #   测试策略 + 测试报告模板
│   ├── Release/                     #   变更计划说明书模板
│   └── Learn From the Incident/     #   故障复盘报告模板
├── opensourceways/              # GitHub 组织下各仓库的 issue 交付件目录
│   ├── backlog/issue_docs/      #   backlog 仓库的各 Issue 交付件归档
│   │   └── {issueId}/
│   │       ├── Requirement Analysis/    #     需求分析说明书
│   │       ├── Architecture Desgin/     #     架构设计说明书
│   │       ├── Test/                    #     测试策略 + 测试报告
│   │       ├── Release/                 #     变更计划
│   │       └── Docs/                    #     交付件总结等
│   ├── {repo}/issue_docs/       #   其他仓库的各 Issue 交付件归档
│   │   └── {issueId}/
│   │       ├── Requirement Analysis/
│   │       ├── Architecture Desgin/
│   │       ├── Test/
│   │       ├── Release/
│   │       └── Docs/
├── .claude/commands/                # AI 辅助 Skill（可复用的自动化命令）
├── 🛡️ *.md                          # 安全工具使用指南（Gitleaks / SAST / UT 覆盖率）
└── {project}/                       # 各项目子目录（openeuler, mindspore, ascend...）
```

## 开发流程

每个 GitHub Issue 按以下阶段推进，每个阶段产出对应文档归档到 `opensourceways/{repo}/issue_docs/{issueId}/`（如 backlog 仓库为 `opensourceways/backlog/issue_docs/{issueId}/`）：

```
Issue 创建 → 需求分析 → 架构设计 → 测试策略 → 开发实现 → 变更发布 → (故障复盘)
```

### 1. 需求分析

基于 `templates/Requirement Analysis/` 模板，完成需求分析说明书，核心产出：
- 需求场景说明与验收标准
- 任务拆解（Task 清单 + 工作量估算）
- **需求相关性分析**：判定需要打的标签，决定后续需要哪些文档

### 2. 架构设计（need_security / need_design）

基于 `templates/Architecture Desgin/` 模板，完成架构设计说明书：
- 功能设计：架构图、数据流图、组件职责与接口、TASK 清单
- 非功能设计：安全与隐私（`need_security` 时必填）、可靠性、可服务性、性能

### 3. 测试策略（need_itest）

基于 `templates/Test/` 模板，完成测试策略和测试报告：
- 测试维度确认（安全测试、性能测试、兼容性测试等）
- 专项验证设计方案

### 4. 变更发布

基于 `templates/Release/` 模板，完成变更计划说明书：
- 变更等级（L1/L2/L3）、执行步骤、验证方式、回滚方案

### 5. 故障复盘

基于 `templates/Learn From the Incident/` 模板，完成故障复盘报告。

## 需求相关性标签

需求分析阶段通过勾选清单确定标签，标签决定后续需要完成哪些文档：

| 标签 | 含义 | 后续文档 |
|------|------|----------|
| `need_security` | 涉及安全（边界变更/凭证/权限/供应链/隐私/AI） | 架构设计（含安全设计） |
| `need_design` | 涉及架构变更（拓扑/API/新中间件） | 架构设计 |
| `need_itest` | 涉及集成测试（跨组件/核心组件/端到端流程） | 测试策略 + 测试报告 |
| `need_ux` | 涉及用户体验变更 | 架构设计（含 UX 设计章节） |
| `need_light` | 以上均不涉及 | 无额外文档，走快速合入通道 |

## Issue 交付件归档

每个 Issue 的文档归档在 `opensourceways/{repo}/issue_docs/{issueId}/` 下，按阶段创建目录，例如：

```
opensourceways/backlog/issue_docs/29/
├── Requirement Analysis/
│   └── #29 Requirement Analysis Specification.md
├── Architecture Desgin/
│   └── #29 Architecture Design Specification.md
└── Docs/
    └── 交付件总结.md
```

文件命名以 `#{issueId}` 开头，不是固定的 `#1`。

## 安全工具指南

仓库根目录下的安全指南文档：
- `🛡️ Gitleaks 误报屏蔽与漏洞处理指南.md` — Git 仓库密钥泄露扫描的误报处理
- `🛡️ 单元测试 (UT) 覆盖率门禁工具说明书.md` — UT 覆盖率门禁配置与使用
- `🛡️ 软件安全编码扫描（SAST）问题整改与误报治理指南.md` — SAST 扫描问题整改

## AI 辅助开发

本仓库支持 AI 辅助文档编写，通过 Claude Code 自定义命令实现：

- `/ai-design <Issue URL 或 issueId>` — 自动判断当前阶段，完成对应文档编写（需求分析 → 架构设计 → 测试策略 → 变更计划）

AI 工作时会：
1. 读取 `AGENTS.md` 了解项目规范
2. 参考 `context/experience/` 中的历史经验
3. 按 `templates/` 中的模板格式输出
4. 完成后沉淀新经验到 `context/experience/`

## 知识库贡献

团队知识沉淀在 `context/` 目录下，遵循"文档即记忆"原则：

| 信息类型 | 放哪里 | 示例 |
|----------|--------|------|
| 踩坑经验 | `context/experience/` | "需求分析中验收标准必须可量化" |
| 业务规则 | `context/business/` | "需求相关性标签判定逻辑" |
| 团队知识 | `context/team/` | "文档 review 流程" |

贡献方式：
1. 遇到问题解决后 → 记录到对应目录
2. 识别高频模式 → 讨论是否封装为 `.claude/commands/` 下的 Skill
