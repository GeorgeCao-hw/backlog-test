# #57 BoostKit 社区接入漏洞管理系统需求分析说明书

## 1. 基础信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/57
* **需求名称**: BoostKit 社区接入漏洞管理系统
* **开发责任人**: yangwei999

---

## 2. 需求场景说明

> 描述"在什么情况下，为了解决什么问题，用户需要做什么"。

**场景说明:**

BoostKit 是 openEuler 生态中面向鲲鹏的高性能软件套件，包含大量第三方开源依赖。当前漏洞管理系统（cve-manager-ng）已接入 MindSpore、OpenGauss、OpenUBMC、Ascend、CANN 等多个社区，但 BoostKit 社区尚未完成接入，导致 BoostKit 软件仓库中的 CVE 漏洞无法被系统自动发现与跟踪，BoostKit 社区安全团队需手动排查 CVE 影响范围并创建对应 issue，存在响应滞后和漏报风险。

为实现 BoostKit 社区 CVE 漏洞的自动化管理，需完成以下两项工作：

1. **trigger 模块**：补全 BoostKit 软件包同步逻辑，利用 syft 工具扫描 BoostKit GitCode 仓库生成 SBOM（软件物料清单）信息，并将解析结果持久化至 `new_package` 表，作为 CVE 匹配的数据基础。

2. **issue 模块**：完善 BoostKit issue handler，实现 CVE 与 BoostKit 软件包版本的精确匹配，并在 GitCode BoostKit 仓库中自动创建和更新 CVE 漏洞跟踪 issue。

---

## 3. 需求验收标准

> 明确需求完成的标志，必须是可量化、可测试的。

**验收标准:**

- 每周日 10:30 trigger 定时任务（`syncSpecialPackages`）能成功扫描 BoostKit 指定仓库，无报错日志，`new_package` 表中 `org='boostkit'` 的记录数符合仓库依赖规模预期（≥ 1 条）。
- 当 CVE 数据推送至系统后，issue 模块能自动将 CVE 与 BoostKit 软件包进行版本匹配，并在 GitCode BoostKit 仓库中成功创建对应的 CVE issue。
- 已创建的 CVE issue 在 CVE 信息更新时，issue 正文内容自动同步更新。
- issue 正文包含：漏洞编号（超链接至 NVD）、漏洞归属组件、受影响版本、CVSS V3 基础评分及等级、向量字符串、漏洞简述、漏洞公开时间、漏洞创建时间、详情参考链接，格式与 `issue/app/boostkit/issue_body.go` 模板一致。
- `MaintainedVersion()` 接口返回 BoostKit 当前维护版本列表，与社区实际维护分支保持一致。

---

## 4. 需求设计与分解

> 说明：基于初步方案，将需求拆解为可实施的原子 Task。后续的流程判定将严格依据这些 Task 的影响范围进行。

### 4.1 核心逻辑方案

**逻辑方案:**

BoostKit 社区接入遵循与 Ascend、Jiuwen、Openlibing 相同的「syft SBOM 扫描」路径，完整数据流如下：

```
BoostKit GitCode 仓库（syft.repos 配置列表）
         │
         ▼ collect_sbom.sh（浅克隆 + syft 扫描）
  syft-json 格式 SBOM 文件
         │
         ▼ domain.GenGitcodePackagesBySyft()（解析 artifacts）
  []domain.Package（org=boostkit，含包名、版本列表）
         │
         ▼ PackageRepo.Save()
  new_package 表（org='boostkit' 记录）
         │
         ▼ CVE 数据推送 → HandleCve() → 包名匹配
  boostkitHandler.MatchPackageVersion()（版本范围比对）
         │
         ▼ 命中则调用
  boostkitHandler.CreateIssue() / UpdateIssue()
         │
         ▼ go-gitcode openapi
  GitCode BoostKit 仓库 CVE issue（私密 Bug-Report 类型）
```

**trigger 模块关键改动：**

- `trigger/app/boostkit/config.go`：Config 复用 `domain.Org`（已有），需在 `config.yaml` 中补全 `boostkit` 段的 `token`（GitCode AccessToken）及 `syft.repos` 仓库列表；BoostKit 已注册至 `trigger/entrance.go` 的 Sunday 10:30 `syncSpecialPackages` 定时任务，无需改动 entrance.go。
- `trigger/app/boostkit/sync.go`：`GetPackageInfo()` 已正确委托 `domain.GenGitcodePackagesBySyft()`，无需改动逻辑，需验证配置驱动后可正常工作。

**issue 模块关键改动：**

- `issue/app/boostkit/handler.go`：
  - `MaintainedVersion()`：当前返回 nil，需实现为返回 BoostKit 实际维护的版本分支列表（如 `["master", "2.x", ...]`）。
  - `CommentIssue()`、`SetLabel()`、`CheckRelatedPR()`：当前均为空实现，需结合 BoostKit 社区工作流评估是否需要实现；初期可保持空实现，后续按需补齐。
- `issue/app/boostkit/issue_body.go`：issue 正文中文模板已完整，无需改动。
- `config.yaml`：补全 `issue.boostkit.token` 为实际 GitCode Token。

### 4.2 任务清单

**任务清单:**

| 任务 ID   | 任务描述 (Task Description)                                                              | 预期产出 (Deliverables)        | 预期工作量（人天） |
|---------|--------------------------------------------------------------------------------------|----------------------------|------------|
| **TASK1** | 梳理 BoostKit GitCode 仓库清单，确认需要 syft 扫描的仓库范围及 Token 访问权限（clone 权限）                    | 仓库清单、权限确认                  | 0.5        |
| **TASK2** | trigger 模块：更新 `config.yaml`，填入 BoostKit GitCode AccessToken 及 `syft.repos` 仓库列表      | `config.yaml` 配置变更          | 0.5        |
| **TASK3** | trigger 模块：端到端联调验证 syft SBOM 扫描流程，排查克隆/扫描/解析/入库各环节问题，确认包数据正确写入 `new_package` 表 | 代码修复（如有）、联调记录              | 1          |
| **TASK4** | issue 模块：实现 `MaintainedVersion()`，返回 BoostKit 当前维护的版本分支列表                           | `handler.go` 代码变更           | 0.5        |
| **TASK5** | issue 模块：评估并按需实现 `CommentIssue()`、`SetLabel()`、`CheckRelatedPR()` 方法                 | `handler.go` 代码变更（或评估说明）   | 1          |
| **TASK6** | issue 模块：配置实际 GitCode Token，联调验证 `CreateIssue()` / `UpdateIssue()` 对 BoostKit 仓库的读写 | 配置变更、联调记录                  | 0.5        |

---

## 5. 需求相关性分析

> **操作说明**：根据上述拆解出的 Task，识别其变更行为。任何一项勾选为"是"：打上对应issue标签，必须执行对应的流程门禁。全部未勾选：该需求自动判定为轻量化特性，打上need_light标签。

### A. 安全相关性分析

> 若涉及以下任一项，打标 `need_security`标签，PR 必须关联特性issue的架构设计文档（含安全设计部分）**如勾选需要给出原因**。

* [ ] **边界变更**：新增公网端口、修改防火墙规则、变更网关配置。
* [ ] **凭证处理**：涉及密钥（Secret/Key）、Token、证书的存储或分发。
  > TASK2、TASK6 需为 BoostKit 新增两个 GitCode API Token（trigger 侧用于仓库克隆，issue 侧用于 issue 读写），涉及新凭证的存储与配置管理，触发本项。
* [ ] **权限调整**：修改权限模型、服务账号（SA）权限或鉴权逻辑。
* [ ] **供应链**：引入新的第三方二进制文件、SDK 或重大版本依赖升级。
  > syft 工具已在同类社区（Ascend、Jiuwen 等）中使用，非新引入。
* [ ] **隐私风险评估**：涉及用户个人数据（Email、手机号、IP、邮箱 等）的处理。
* [ ] **AI使用**：涉及AIGC能力应用，并提供服务。

### B. 架构设计相关性分析

> 若涉及以下任一项，打标 `need_design`标签，PR 必须关联特性issue的架构设计文档。 **如勾选需要给出原因**。

* [ ] A环节判定需要完成安全设计
  > 凭证处理被触发，需在架构设计中说明 BoostKit Token 的存储方式（Kubernetes Secret）和使用范围隔离。
* [ ] 改变了现有系统的物理/逻辑拓扑
  > 本需求为在现有 trigger/issue 框架内新增一个社区适配，不改变系统拓扑结构。
* [ ] 新增或大幅修改对外暴露的 API/CLI 接口
* [ ] 引入了新的中间件、数据库或三方核心组件

### C. 系统集成测试相关性分析

> 若涉及以下任一项，打标 `need_itest`标签，PR必须关联特性issue的测试策略和测试报告文档。 **如勾选需要给出原因**。

* [ ] 上述环节判定需要执行安全设计或架构设计。
* [ ] **跨组件影响**：变更会触发下游服务或关联系统的连锁反应（级联效应）。
  > trigger 模块同步的 BoostKit 包信息直接作为 issue 模块 CVE 匹配的数据输入。
* [ ] **核心组件管控**：含项目定级为 Core 的核心逻辑变更。
* [ ] **环境强依赖**：功能高度依赖内核参数、网络拓扑或特定的物理挂载。
* [ ] **端到端流程**：涉及从用户输入到持久化存储的全链路逻辑。
  > 完整链路为：syft 扫描仓库 → SBOM 解析 → 包信息入库 → CVE 推送匹配 → issue 创建，覆盖从数据采集到结果输出的全流程。

### D. 用户体验相关性分析

> 若涉及以下任一项，打标 `need_ux`标签，PR必须关联特性issue的用户体验设计文档。 **如勾选需要给出原因**。

* [ ] **交互逻辑变更**：涉及 Web 门户、控制台（Dashboard）或命令行工具（CLI）的交互流程调整。
* [ ] **感知性能变动**：变更可能显著影响页面的加载时间、同步请求的响应时延或异步任务的进度反馈。
* [ ] **文档与辅助能力**：涉及报错提示语、帮助中心链接、FAQ 或新功能的 Runbook 说明。
* [ ] **无障碍与多语种**：涉及国际化（i18n）支持、辅助功能或不同终端（移动端/桌面端）的适配。

### 5.1 需求相关性分析汇总结果

* [ ] **need_security**（需架构设计（含安全威胁分析和安全设计））
* [ ] **need_design**（需架构设计）
* [ ] **need_itest**（需执行测试策略设计和全链路集成测试）
* [ ] need_ux（需架构设计（含UX设计））
* [x] need_light（上述均未勾选，走快速合入通道）

---

## 6. 价值识别与业务评估

> **判定准则**：基础设施接纳需求必须具备明确的 ROI（投资回报比）或合规必要性。

| 维度        | 评估问题                                        | 结论/说明                                                                                          |
|-----------|---------------------------------------------|-------------------------------------------------------------------------------------------------|
| **范围判定**  | 该需求是否属于基础设施范围内？                             | 是，cve-manager-ng 属于社区安全基础设施，BoostKit 接入属于平台扩展                                                 |
| **规划一致性** | 该需求是否是否在年度技术规划中？                            | 是，多社区统一漏洞管理是 cve-manager-ng 平台建设的核心目标                                                         |
| **优先级**   | 该需求优先级评估（高/中/低）？                            | 中，BoostKit 作为 openEuler 生态重要组件，CVE 漏洞自动跟踪具备安全合规价值                                            |
| **通用性**   | 该需求是否解决 3 个以上业务方的共性痛点？                      | 否，专项接入 BoostKit 社区；但接入模式可复用于后续其他社区                                                           |
| **必要性**   | 现有组件通过配置变更是否无法实现目标或没有不用开发的替代方案？             | 是，代码库中已存在 BoostKit 骨架代码，但 `MaintainedVersion()`、`syft.repos` 配置等关键逻辑缺失，仅靠配置变更无法实现完整功能           |
| **工作量**   | 预计总工作量                                      | 5 人天（TASK1: 0.5天，TASK2: 0.5天，TASK3: 1天，TASK4: 0.5天，TASK5: 1天，TASK6: 0.5天）          |
| **价值评估**  | 实现后能减少多少手动操作或提升多少系统稳定性？                     | 实现后 BoostKit CVE 漏洞跟踪全自动化，预计消除社区安全团队每周 2～4 小时的手动排查与 issue 创建工作，并将漏洞响应时效从人工发现缩短至系统自动触发（分钟级） |

> **状态定义：** **Accept (准入)** | **Reject (驳回)** | **Pending (待议)**

**建议结论**：Accept

**原因描述:** BoostKit 社区接入遵循 cve-manager-ng 现有的社区适配框架（syft SBOM + GitCode issue），实现成本低（5 人天）、风险可控。代码库中已有骨架实现，主要工作集中在配置补全和关键方法实现，无需引入新的架构复杂度。接入后可实现 BoostKit 开源依赖 CVE 漏洞的自动化发现与跟踪，消除手动排查工作，符合"多社区统一漏洞管理"的平台演进目标，建议准入。

---
