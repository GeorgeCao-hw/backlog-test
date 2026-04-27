# #148 GitHub CI Workflow 指标采集需求分析说明书

## 1. 基础信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/148
* **需求名称**: GitHub CI Workflow 指标采集系统
* **开发责任人**: Creyson-peng

---

## 2. 需求场景说明

> 描述"在什么情况下，为了解决什么问题，用户需要做什么"。

**场景说明:**

开源社区（如 vllm-project、LLaMA-Factory、sglang 等 AI/ML 项目）在 GitHub 上运行大量 CI Workflow，涉及 NPU 和 GPU 设备的构建测试。当前缺乏对这些 CI 运行的系统性指标采集与分析能力，导致无法量化 CI 运行效率、区分设备类型性能、追踪 PR workflow 状态。运维需要配置仓库的 step 名称映射和 device 类型映射，系统自动采集 GitHub Actions 数据并聚合到数据仓库，供后续分析使用。

## 3 需求验收标准

> 明确需求完成的标志，必须是可量化、可测试的。

**验收标准:**

- [x] 支持 YAML 配置指定多仓库 CI 数据采集
- [x] 正确提取 download_time、prepare_time、run_time、wait_time、e2e_time 指标
- [x] 正确映射 workflow_name 到 device_type（NPU/GPU）
- [x] 数据写入 fact_ci_workflow 和 dws_opensource_ci 表
- [x] 增量更新机制正常工作
- [x] 单元测试覆盖率 ≥ 90%

---

## 4. 需求设计与分解

> 说明：基于初步方案，将需求拆解为可实施的原子 Task。后续的流程判定将严格依据这些 Task 的影响范围进行。

### 4.1 核心逻辑方案

> 简述实现逻辑（如：数据流向、模块改动、新增配置项等），作为任务拆解的理论依据。推荐使用Mermaid图表展示流程，支持GitHub原生渲染。

**逻辑方案:** 配置层定义仓库和映射规则，采集层通过 GitHub API 获取数据，处理层提取时间指标并映射 device_type，存储层写入 PostgreSQL。增量更新追踪未完成 workflow。

**流程图示例（使用Mermaid）：**

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
flowchart TD
    A["加载配置"] --> B["获取 workflow runs"]
    B --> C["获取 jobs 详情"]
    C --> D["提取时间指标"]
    D --> E["映射 device_type"]
    E --> F["写入数据库"]
```

**说明：**
- 推荐使用Flowchart展示业务流程
- 所有Mermaid代码直接嵌入Markdown，GitHub自动渲染

### 4.2 任务清单

**任务清单:**

| 任务 ID              | 任务描述 (Task Description)            | 预期产出 (Deliverables) | 预期工作量（人天）    |
|--------------------|------------------------------------|---------------------|--------------|
| **task1** | 实现数据模型 + 核心采集逻辑（配置加载、API调用、时间提取、device映射） | om/config/models.py, om/collector/workflow_metric_collector.py | 2.5 |
| **task2** | 实现数据表定义 + 聚合逻辑 + 增量更新 | om/db/table/dws_table.py, 聚合函数 | 1 |
| **task3** | 编写单元测试 + 配置示例 | tests/, config_workflow_*.yaml.example | 1.5 |

---

## 5. 需求相关性分析

> **操作说明**：根据上述拆解出的 Task，识别其变更行为。任何一项勾选为"是"：打上对应issue标签，必须执行对应的流程门禁。全部未勾选：该需求自动判定为轻量化特性，打上need_light标签。

### A. 安全相关性分析

> 若涉及以下任一项，打标 `need_security`标签，PR 必须关联特性issue的架构设计文档（含安全设计部分）**如勾选需要给出原因**。

无勾选项

* [ ] **边界变更**：新增公网端口、修改防火墙规则、变更网关配置。
* [ ] **凭证处理**：涉及密钥（Secret/Key）、Token、证书的存储或分发。
* [ ] **权限调整**：修改权限模型、服务账号（SA）权限或鉴权逻辑。
* [ ] **供应链**：引入新的第三方二进制文件、SDK 或重大版本依赖升级。
* [ ] **隐私风险评估**：涉及用户个人数据（Email、手机号、IP、邮箱 等）的处理。
* [ ] **AI使用**：涉及AIGC能力应用，并提供服务。

### B. 架构设计相关性分析

> 若涉及以下任一项，打标 `need_design`标签，PR 必须关联特性issue的架构设计文档。 **如勾选需要给出原因**。

* [ ] A环节判定需要完成安全设计
* [ ] 改变了现有系统的物理/逻辑拓扑
* [ ] 新增或大幅修改对外暴露的 API/CLI 接口
* [x] 引入了新的中间件、数据库或三方核心组件 **原因：新增 workflow_metric_collector 模块**

### C. 系统集成测试相关性分析

> *若涉及以下任一项，打标 `need_itest`标签，PR必须关联特性issue的测试策略和测试报告文档。 **如勾选需要给出原因**。

无勾选项

* [ ] 上述环节判定需要执行安全设计或架构设计。
* [ ] **跨组件影响**：变更会触发下游服务或关联系统的连锁反应（级联效应）。
* [ ] **核心组件管控**：含项目定级为 Core 的核心逻辑变更。
* [ ] **环境强依赖**：功能高度依赖内核参数、网络拓扑或特定的物理挂载。
* [ ] **端到端流程**：涉及从用户输入到持久化存储的全链路逻辑。

### D. 用户体验相关性分析

> 若涉及以下任一项，打标 `need_ux`标签，PR必须关联特性issue的用户体验设计文档。 **如勾选需要给出原因**。

无勾选项

* [ ] **交互逻辑变更**：涉及 Web 门户、控制台（Dashboard）或命令行工具（CLI）的交互流程调整。
* [ ] **感知性能变动**：变更可能显著影响页面的加载时间、同步请求的响应时延或异步任务的进度反馈。
* [ ] **文档与辅助能力**：涉及报错提示语、帮助中心链接、FAQ 或新功能的 Runbook 说明。
* [ ] **无障碍与多语种**：涉及国际化（i18n）支持、辅助功能或不同终端（移动端/桌面端）的适配。

### 5.1 需求相关性分析汇总结果

* [ ] need_security (需架构设计（含安全威胁分析和安全设计）)
* [x] need_design (需架构设计)
* [ ] need_itest (需执行测试策略设计和全链路集成测试)
* [ ] need_ux (需架构设计（含UX设计)）
* [ ] need_light (上述均未勾选，走快速合入通道)

---

## 6. 价值识别与业务评估

> **判定准则**：基础设施接纳需求必须具备明确的 ROI（投资回报比）或合规必要性。

| 维度        | 评估问题                            | 结论/说明               |
|-----------|---------------------------------|---------------------|
| **范围判定**  | 该需求是否属于基础设施范围内？                 | 是，CI 数据采集属于基础设施能力   |
| **规划一致性** | 该需求是否是否在年度技术规划中？                | 是，符合开源生态数据洞察规划 | 
| **优先级**   | 该需求优先级评估（高/中/低）？                | 中 | 
| **通用性**   | 该需求是否解决 3 个以上业务方的共性痛点？          | 是，适用于多个开源项目仓库   |
| **必要性**   | 现有组件通过配置变更是否无法实现目标或没有不用开发的替代方案？ | 是，现有无类似采集能力 | 
| **工作量**   | 预计总工作量 5 人天？        | 5 人天  |
| **价值评估**  | 实现后能减少多少手动操作或提升多少系统稳定性？         | 为 CI 优化提供量化数据支撑，预计可减少 50% 手动分析时间 |

> **状态定义：** **Accept (准入)** | **Reject (驳回)** |  **Pending (待议)**

**建议结论**： Accept

**原因描述:** 该需求通过自动化 CI 数据采集，为开源项目 CI 优化提供量化数据支撑，预计可减少 SRE 团队 50% 的手动分析工作时间，且符合开源生态数据洞察演进目标。

---

## 7. 附录

### 7.1 配置示例

```yaml
workflow:
  table_name: "fact_ci_workflow"
  metadata_table: "fact_ci_workflow_meta"
  github_token: "${GITHUB_TOKEN}"
  github_base_api: "https://api.github.com"
  repos: "vllm-project/vllm,vllm-project/vllm-ascend"
  collect_from: "2026-04-01"
  step_configs:
    - org: "vllm-project"
      repo: "vllm"
      download_steps:
        - "Checkout code"
        - "Download wheels"
      prepare_steps:
        - "Set up Python"
        - "Install dependencies"
      device_configs:
        - workflow_name: "NPU Tests"
          device_type: "NPU"
        - workflow_name: "GPU Tests"
          device_type: "GPU"

database:
  host: "${DB_HOST}"
  port: 5432
  name: "om_dataarts"
  user: "${DB_USER}"
  password: "${DB_PASSWORD}"
```

### 7.2 数据表字段说明

**dws_opensource_ci 表核心字段：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| uuid | VARCHAR(500) | 主键：commit_id_workflow_id |
| org | VARCHAR(255) | 组织名 |
| repo | VARCHAR(255) | 仓库名 |
| workflow_id | TEXT | GitHub workflow run ID |
| workflow_status | VARCHAR(50) | completed/in_progress/queued |
| device_type | VARCHAR(50) | NPU/GPU |
| e2e_time | INT8 | workflow 端到端时长 |
| total_run_time | INT8 | jobs 最大运行时长 |
| success_rate | NUMERIC(5,2) | 成功 job 占比 |