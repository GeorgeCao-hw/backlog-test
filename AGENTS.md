# AGENTS.md

## 项目背景

这是 openEuler 社区基础设施团队的 backlog 管理仓库，用于管理团队的需求、架构设计、测试策略、变更计划和故障复盘文档。

仓库核心功能：
- 需求全生命周期文档管理（需求分析 → 架构设计 → 测试 → 发布 → 复盘）
- 团队知识沉淀与经验共享
- AI 辅助开发的提示词与工具管理

## 仓库结构

```
backlog/
├── AGENTS.md                    # AI 的"入职手册"（本文件）
├── context/                     # 团队知识库
│   ├── team/                    # 团队通用知识
│   ├── experience/              # 踩坑经验
│   └── business/                # 业务逻辑规则
├── templates/                   # 文档模板（标准格式）
│   ├── Requirement Analysis/    # 需求分析说明书模板
│   ├── Architecture Desgin/     # 架构设计说明书模板
│   ├── Test/                    # 测试策略 + 测试报告模板
│   ├── Release/                 # 变更计划说明书模板
│   └── Learn From the Incident/ # 故障复盘报告模板
├── opensourceways/issue_docs/   # 各 Issue 的交付件目录
│   └── {issueId}/               # 每个 Issue 独立目录
│       ├── Requirement Analysis/
│       ├── Architecture Desgin/
│       ├── Test/
│       ├── Release/
│       └── Docs/
├── .claude/commands/            # Claude Code 自定义命令（Skill）
└── {project}/                   # 各项目子目录（openeuler, mindspore...）
```

## 工作规范

### 需求文档生命周期

每个 GitHub Issue 对应 `opensourceways/issue_docs/{issueId}/` 下的一组文档，按以下阶段交付：

1. **需求分析**：填写需求分析说明书，完成需求相关性分析（安全/架构/测试/UX），确定需要打的标签
2. **架构设计**：如需 `need_security` 或 `need_design`，必须完成架构设计文档（含安全威胁分析）
3. **测试策略**：如需 `need_itest`，必须完成测试策略和测试报告
4. **变更计划**：发布前完成变更计划说明书
5. **故障复盘**：如有故障，按模板完成复盘报告

### 需求相关性标签体系

| 标签 | 含义 | 触发条件 |
|------|------|----------|
| `need_security` | 需架构设计（含安全威胁分析和安全设计） | 涉及边界变更/凭证处理/权限调整/供应链/隐私/AI |
| `need_design` | 需架构设计 | A环节判定需安全设计/拓扑变更/API变更/新中间件 |
| `need_itest` | 需测试策略和集成测试 | 需安全或架构设计/跨组件影响/核心组件/环境依赖/端到端流程 |
| `need_ux` | 需UX设计 | 交互变更/性能变动/文档变更/无障碍 |
| `need_light` | 轻量化特性，走快速合入通道 | 以上均未勾选 |

### 文档编写规范

- 先读模板再写，严格遵循模板结构
- 验收标准必须**可量化、可测试**
- 勾选相关性分析时**必须给出原因**
- 任务拆解到**原子级别**，每个 Task 可独立交付
- 不确定的地方先标注 `[TODO]`，后续补充

### AI 注意事项

- 【重要】文件名以 `#{issueId}` 开头（如 `#29 Requirement Analysis Specification.md`），不是固定的 `#1`
- 【重要】目录名 `Architecture Desgin` 有历史拼写问题（少了一个 n），但全仓库保持一致，不要修改
- 【重要】需求分析说明书只做简要分析，不做具体设计，文字精简；Task 控制在 2-4 个，工作量紧凑
- 【重要】需求分析阶段只产出需求分析说明书，不创建其他模板文件；根据标签结果提示用户是否进入下一阶段
- 【重要】需求分析中的"价值识别与业务评估"部分必须给出 Accept/Reject/Pending 结论
- 使用 `gh` CLI 获取 GitHub Issue 信息，不要猜测 Issue 内容

## 知识检索规则

在工作过程中，遇到以下情况时**必须主动检索**对应的知识目录：

### 何时查 `context/team/`
- 涉及 Git 分支、PR、代码审查等**协作流程**时
- 涉及文档 review 审批流程时
- 需要了解团队成员分工或职责时
- 涉及 CI/CD 流水线、工具使用等**团队基础设施**时

### 何时查 `context/business/`
- 编写需求分析时，需要了解**该项目的业务背景和规则**
- 做需求相关性分析时，需要判断**业务影响范围**
- 涉及服务间调用关系、数据模型、接口约定等**领域知识**时
- 涉及特定子项目（openeuler / opensourceways / mindspore 等）的**项目特定约定**时

### 何时查 `context/experience/`
- 开始编写任何文档**之前**，先检查是否有同类经验
- 遇到不确定的判断时，检查是否有历史踩坑记录
- 完成工作**之后**，将新经验追加到此目录

### 检索方式
不需要 RAG 或向量数据库。直接用以下方式：
1. 先 `ls context/{team,business,experience}/` 看有什么文件
2. 根据文件名判断相关性
3. 读取相关文件获取知识

## 常见坑点

（遇到问题时补充到此处或 context/experience/ 目录）

## 可用命令

- `/ai-design <Issue URL 或 issueId>`：DevOps 全生命周期文档编写（需求分析 → 架构设计 → 测试策略 → 变更计划），自动判断当前阶段
- `/code-review <PR 编号或 PR URL>`：对指定 PR 进行结构化代码检视，按高/中/低分级输出检视报告
