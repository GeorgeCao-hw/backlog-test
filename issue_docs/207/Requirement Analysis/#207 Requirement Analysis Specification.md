# #207 热点话题数据库补充邮件数据源需求分析说明书

## 1. 基础信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/207
* **需求名称**: 为 openUBMC、MindSpore 等社区补充邮件列表（maillist）数据源
* **开发责任人**: HuangLei

---

## 2. 需求场景说明

> 描述"在什么情况下，为了解决什么问题，用户需要做什么"。

**场景说明:**

经排查，热点话题（hotopic）数据采集管线中，openUBMC、MindSpore 等部分社区未覆盖邮件列表（maillist）数据源，导致开发者在邮件列表中提出的技术问题、功能讨论等未被纳管到热点话题数据库中，造成话题统计结果不完整。

需要在现有数据采集框架下，为这些社区补充邮件数据源的采集、清洗和 AI 总结能力，确保邮件渠道的技术讨论能够被及时采集并纳入热点分析。

本次优先实现 openUBMC 和 MindSpore 两个社区的邮件数据源接入，其余社区（CANN、Mind系列、BoostKit、HPCKit、HiFloat 等）分批跟进。

## 3 需求验收标准

> 明确需求完成的标志，必须是可量化、可测试的。

**验收标准:**

- [ ] openUBMC 社区邮件列表数据可被正常采集，邮件归档链接格式正确（`https://mailweb.openubmc.cn/archives/list/{list_name}/thread/{message_id_hash}`）
- [ ] MindSpore 社区邮件列表数据可被正常采集，邮件归档链接格式正确（`https://mailweb.mindspore.cn/archives/list/{list_name}/thread/{message_id_hash}`）
- [ ] openUBMC 邮件清洗器可正确过滤例会、公告、纪要、会议通知、转测试等非问题类邮件
- [ ] MindSpore 邮件清洗器可正确过滤例会、开源实习、测试任务、教程、CVE、会议通知等非问题类邮件
- [ ] AI 总结 Prompt 配置正确加载，可对有效邮件内容生成中文摘要
- [ ] 新增 Collector 和 Cleaner 的单元测试通过，覆盖有效/无效邮件判定及工厂路由

---

## 4. 需求设计与分解

> 说明：基于初步方案，将需求拆解为可实施的原子 Task。后续的流程判定将严格依据这些 Task 的影响范围进行。

### 4.1 核心逻辑方案

> 简述实现逻辑（如：数据流向、模块改动、新增配置项等），作为任务拆解的理论依据。

**逻辑方案:**

复用现有 `MailCollector` / `BaseCleaner` 基类框架，为每个新增社区实现子类，差异化部分仅包含：
- 邮件归档 URL 拼接规则（`.cn` 域名格式）
- 无效邮件过滤规则（各社区关键词不同）
- AI 总结 Prompt 配置（各社区领域术语差异）

数据流向与现有邮件采集管线一致：`Collector 拉取邮件 → Cleaner 过滤无效内容 → AI 总结 → 写入 DWS 数据库`

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#4caf50',
    'primaryBorderColor': '#2e7d32',
    'primaryTextColor': '#ffffff',
    'fontSize': '14px'
  }
}}%%
flowchart LR
    A["社区邮件列表"] --> B["MailCollector\n拉取邮件"]
    B --> C["BaseCleaner\n过滤无效内容"]
    C --> D{邮件有效?}
    D -->|否| E["丢弃"]
    D -->|是| F["LLM 总结"]
    F --> G["写入 DWS"]
    G --> H["热点话题分析"]
```

**改动文件清单:**

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `app/data_collect_clean/collector.py` | 新增类 | 新增 `OpenUBMCMailCollector`、`MindSporeMailCollector`，注册到工厂方法 |
| `app/data_collect_clean/clean.py` | 新增类 | 新增 `OpenUBMCMailCleaner`、`MindSporeMailCleaner`，含社区特定过滤规则 |
| `app/main.py` | 修改配置 | openUBMC 和 MindSpore 采集管线中新增 `mail` 数据源条目 |
| `config/conf.yaml` | 新增配置 | 新增 `OPENUBMC_MAIL_PROMPT` 和 `MINDSPORE_MAIL_PROMPT` |
| `config/settings.py` | 新增字段 | 新增 `openubmc_mail_prompt`、`mindspore_mail_prompt` |
| `tests/test_collector.py` | 新增测试 | 新增 MailCollector 相关单元测试（6 个 test class） |
| `tests/test_clean.py` | 新增测试 | 新增 MailCleaner 相关单元测试（4 个 test class） |

### 4.2 任务清单

| 任务 ID              | 任务描述 (Task Description)            | 预期产出 (Deliverables) | 预期工作量（人天） |
|--------------------|------------------------------------|---------------------|--------------|
| **task1 _#207_** | **实现 openUBMC 和 MindSpore 邮件 Collector** | collector.py 新增类 | **0.5** |
| **task2 _#207_** | **实现 openUBMC 和 MindSpore 邮件 Cleaner（含过滤规则和 AI Prompt）** | clean.py 新增类、conf.yaml 新增配置、settings.py 新增字段 | **1** |
| **task3 _#207_** | **在 main.py 中注册两个社区的 mail 数据源** | main.py 采集管线配置 | **0.25** |
| **task4 _#207_** | **编写 Collector 和 Cleaner 单元测试** | test_collector.py、test_clean.py 新增测试类 | **1** |
| **task5 _后续_** | **CANN、Mind系列、BoostKit、HPCKit、HiFloat 社区邮件数据源接入** | 按社区分批提交 PR | **3** |

---

## 5. 需求相关性分析

> **操作说明**：根据上述拆解出的 Task，识别其变更行为。任何一项勾选为"是"：打上对应issue标签，必须执行对应的流程门禁。全部未勾选：该需求自动判定为轻量化特性，打上need_light标签。

### A. 安全相关性分析

> 若涉及以下任一项，打标 `need_security`标签，PR 必须关联特性issue的架构设计文档（含安全设计部分）**如勾选需要给出原因**。

**邮件数据处理和 AIGC 能力均为现有系统已有能力，本次变更仅新增社区适配，未引入新的安全风险。**

* [ ] **边界变更**：新增公网端口、修改防火墙规则、变更网关配置。
* [ ] **凭证处理**：涉及密钥（Secret/Key）、Token、证书的存储或分发。
* [ ] **权限调整**：修改权限模型、服务账号（SA）权限或鉴权逻辑。
* [ ] **供应链**：引入新的第三方二进制文件、SDK 或重大版本依赖升级。
* [ ] **隐私风险评估**：涉及用户个人数据（Email、手机号、IP、邮箱 等）的处理。
* [ ] **AI使用**：涉及AIGC能力应用，并提供服务。

### B. 架构设计相关性分析

> 若涉及以下任一项，打标 `need_design`标签，PR 必须关联特性issue的架构设计文档。**如勾选需要给出原因**。

**本次变更在现有 Collector/BaseCleaner 框架内扩展，未改变系统拓扑、未新增对外接口、未引入新组件。**

* [ ] A环节判定需要完成安全设计
* [ ] 改变了现有系统的物理/逻辑拓扑
* [ ] 新增或大幅修改对外暴露的 API/CLI 接口
* [ ] 引入了新的中间件、数据库或三方核心组件

### C. 系统集成测试相关性分析

> 若涉及以下任一项，打标 `need_itest`标签，PR必须关联特性issue的测试策略和测试报告文档。**如勾选需要给出原因**。

**新增社区适配仅影响各自的采集管线分支，无跨组件级联影响，单元测试已覆盖核心逻辑。**

* [ ] 上述环节判定需要执行安全设计或架构设计。
* [ ] **跨组件影响**：变更会触发下游服务或关联系统的连锁反应（级联效应）。
* [ ] **核心组件管控**：含项目定级为 Core 的核心逻辑变更。
* [ ] **环境强依赖**：功能高度依赖内核参数、网络拓扑或特定的物理挂载。
* [ ] **端到端流程**：涉及从用户输入到持久化存储的全链路逻辑。

### D. 用户体验相关性分析

> 若涉及以下任一项，打标 `need_ux`标签，PR必须关联特性issue的用户体验设计文档。**如勾选需要给出原因**。

**本次变更为后台数据采集管线变更，无前端或用户交互界面改动。**

* [ ] **交互逻辑变更**：涉及 Web 门户、控制台（Dashboard）或命令行工具（CLI）的交互流程调整。
* [ ] **感知性能变动**：变更可能显著影响页面的加载时间、同步请求的响应时延或异步任务的进度反馈。
* [ ] **文档与辅助能力**：涉及报错提示语、帮助中心链接、FAQ 或新功能的 Runbook 说明。
* [ ] **无障碍与多语种**：涉及国际化（i18n）支持、辅助功能或不同终端（移动端/桌面端）的适配。

### 5.1 需求相关性分析汇总结果

**本次变更为轻量化特性，在现有框架内扩展新社区适配，不引入新的安全、架构、集成或 UX 风险。**

* [ ] need_security (需架构设计（含安全威胁分析和安全设计）)
* [ ] need_design (需架构设计)
* [ ] need_itest (需执行测试策略设计和全链路集成测试)
* [ ] need_ux (需架构设计（含UX设计）)
* [x] need_light (上述均未勾选，走快速合入通道)

---

## 6. 价值识别与业务评估

> **判定准则**：基础设施接纳需求必须具备明确的 ROI（投资回报比）或合规必要性。

| 维度        | 评估问题                            | 结论/说明               |
|-----------|---------------------------------|---------------------|
| **范围判定**  | 该需求是否属于基础设施范围内？                 | **是** — 热点话题数据采集管线的基础能力补全 |
| **规划一致性** | 该需求是否在年度技术规划中？                | **是** — 多社区数据源完善计划的一部分 |
| **优先级**   | 该需求优先级评估（高/中/低）？                | **高** — 缺失邮件数据源导致话题统计不完整 |
| **通用性**   | 该需求是否解决 3 个以上业务方的共性痛点？          | **是** — openUBMC、MindSpore 等多个社区存在相同缺口 |
| **必要性**   | 现有组件通过配置变更是否无法实现目标或没有不用开发的替代方案？ | **是** — 各社区邮件格式和领域术语不同，需社区特定 Cleaner 和 Prompt |
| **工作量**   | 预计总工作量 **5.75** 人天？        | **本期 2.75 人天**（openUBMC + MindSpore），后续社区约 3 人天 |
| **价值评估**  | 实现后能减少多少手动操作或提升多少系统稳定性？         | **消除邮件渠道数据盲区，完善热点话题数据库的数据完整性，预计覆盖 openUBMC/MindSpore 社区邮件列表中 80%+ 的技术讨论** |

> **状态定义：** **Accept (准入)** | **Reject (驳回)** |  **Pending (待议)**

**建议结论**： **Accept**

**原因描述:** 该需求补齐了 openUBMC 和 MindSpore 社区的邮件数据源缺口，消除热点话题数据库的数据盲区。实现方案复用现有 Collector/BaseCleaner 框架，仅在社区差异点（URL 格式、过滤关键词、AI Prompt）进行扩展，改动风险低。单元测试覆盖了 Collector URL 拼接、Cleaner 过滤规则及工厂路由，验证充分。

---
