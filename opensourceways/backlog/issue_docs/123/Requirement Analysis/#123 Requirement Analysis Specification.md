# #123 opengauss Issue首次响应时间扩展需求分析说明书

## 1. 基础信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/123
* **需求名称**: opengauss Issue首次响应时间扩展（非作者非机器人最早操作）
* **开发责任人**: **ssignik**

---

## 2. 需求场景说明

opengauss 社区 Issue 首次响应时间的计算，通过 `IssueOperateLogTimeCleaningRule` 从 `fact_opengauss_issue_operate_log` 提取 `first_reply_at_log`，当前逻辑仅取 `action_type = 'add_issue_mr_link'`（关联PR操作）的最早时间作为候选值。

**现状问题：** 社区成员对 Issue 的早期介入（评论、状态变更、指派等操作）无法被识别为首次响应，导致计算出的首次响应时间偏长，无法真实反映社区成员的实际响应速度。

**场景说明：** 在 opengauss 社区运营指标统计中，需要更准确地衡量成员对 Issue 的首次响应时间。应将所有非 Issue 作者、非机器人账号的最早操作时间作为 `first_reply_at_log` 的候选值，扩大有效响应操作的识别范围。

**数据范围：**
- 输入表：`fact_opengauss_issue_operate_log`（操作日志）、`fact_{community}_issue`（Issue 信息，用于获取作者）、`fact_community_robot_user`（机器人账号列表，全局共享表）
- 输出字段：`fact_{community}_issue.first_reply_at_log`、`fact_{community}_issue.closed_at_log`

---

## 3. 需求验收标准

- [x] `first_reply_at_log` 取所有非 Issue 作者、非机器人账号操作中 `created_at` 最早的记录时间
- [x] 非作者判断：`operator_login != fact_{community}_issue.user_login`（JOIN fact_issue 获取 issue 创建者）
- [x] 非机器人判断：`operator_login NOT IN (SELECT user_login FROM fact_community_robot_user)`
- [x] `closed_at_log` 逻辑不变：`action_type = 'changed_issue_custom_state'` 且 `content LIKE '%to 已完成%'` 的最晚时间
- [x] 移除 `ENABLED_COMMUNITIES` 白名单，社区过滤由调用方（任务脚本）控制
- [x] 单元测试覆盖率 100%（26个测试用例全部通过）
- [x] 更新 `docs/tasks/clean.md` 中 `issue_operate_log_time` 规则说明

---

## 4. 需求设计与分解

### 4.1 核心逻辑方案

**当前链路：**

```
fact_opengauss_issue_operate_log
    ↓ IssueOperateLogTimeCleaningRule
    first_reply_at_log = MIN(created_at) WHERE action_type = 'add_issue_mr_link'

fact_opengauss_issue
    ↓ IssueTimeMergeCleaningRule
    final_first_reply_at = MIN(first_reply_at_comment,
                               first_reply_at_label,
                               first_reply_at_log,
                               final_closed_at)

    ↓ IssueTimeCalculationCleaningRule
    first_reply_time = final_first_reply_at - created_at - holiday_seconds - pending_seconds
```

**变更点（仅 `_extract_times_from_operate_log` 的 SQL）：**

旧逻辑：
```sql
MIN(CASE WHEN action_type = 'add_issue_mr_link' THEN created_at END) AS first_reply_time
FROM fact_{community}_issue_operate_log
GROUP BY issue_id, code_platform
```

新逻辑：
```sql
SELECT ol.issue_id, ol.code_platform,
    MIN(CASE
        WHEN ol.operator_login != i.user_login
             AND ol.operator_login NOT IN (
                 SELECT user_login FROM fact_community_robot_user
             )
        THEN ol.created_at
    END) AS first_reply_time,
    MAX(CASE WHEN ol.action_type = 'changed_issue_custom_state'
                  AND ol.content LIKE '%to 已完成%'
        THEN ol.created_at END) AS closed_time
FROM fact_{community}_issue_operate_log ol
JOIN fact_{community}_issue i
    ON i.id = ol.issue_id AND i.code_platform = ol.code_platform
GROUP BY ol.issue_id, ol.code_platform
```

**不变部分：**
- `IssueTimeMergeCleaningRule`：`first_reply_at_log` 字段语义扩展后自然纳入，无需修改
- `IssueTimeCalculationCleaningRule`：无需修改
- `closed_at_log` 逻辑：不变

### 4.2 任务清单

| 任务 ID | 任务描述 | 预期产出 | 预期工作量（人天） |
|---------|---------|---------|-----------------|
| **task1** | 移除 `ENABLED_COMMUNITIES` 常量及 `execute_cleaning_pg` 中的社区白名单判断 | `om/clean/issue_operate_log_time_cleaning_rule.py` | 0.5 |
| **task2** | 替换 `_extract_times_from_operate_log` SQL 为新 JOIN 逻辑 | `om/clean/issue_operate_log_time_cleaning_rule.py` | 0.5 |
| **task3** | 更新模块 docstring，反映新的首次响应时间语义 | `om/clean/issue_operate_log_time_cleaning_rule.py` | 0.2 |
| **task4** | 删除失效测试，新增覆盖新逻辑的6个测试方法 | `tests/clean/test_issue_operate_log_time_cleaning_rule.py` | 0.5 |
| **task5** | 更新文档规则说明 | `docs/tasks/clean.md` | 0.3 |

**总工作量：2 人天**

---

## 5. 需求相关性分析

### A. 安全相关性分析

* [ ] **边界变更**：新增公网端口、修改防火墙规则、变更网关配置。
* [ ] **凭证处理**：涉及密钥（Secret/Key）、Token、证书的存储或分发。
* [ ] **权限调整**：修改权限模型、服务账号（SA）权限或鉴权逻辑。
* [ ] **供应链**：引入新的第三方二进制文件、SDK 或重大版本依赖升级。
* [ ] **隐私风险评估**：涉及用户个人数据（Email、手机号、IP、邮箱 等）的处理。
* [ ] **AI使用**：涉及AIGC能力应用，并提供服务。

**结论**：不涉及安全相关变更

### B. 架构设计相关性分析

* [ ] A环节判定需要完成安全设计
* [ ] 改变了现有系统的物理/逻辑拓扑
* [ ] 新增或大幅修改对外暴露的 API/CLI 接口
* [ ] 引入了新的中间件、数据库或三方核心组件

**结论**：不涉及架构设计变更，仅修改现有清洗规则 SQL 逻辑，不新增数据表或组件

### C. 系统集成测试相关性分析

* [ ] 上述环节判定需要执行安全设计或架构设计。
* [ ] **跨组件影响**：变更会触发下游服务或关联系统的连锁反应（级联效应）。
* [ ] **核心组件管控**：含项目定级为 Core 的核心逻辑变更。
* [ ] **环境强依赖**：功能高度依赖内核参数、网络拓扑或特定的物理挂载。
* [ ] **端到端流程**：涉及从用户输入到持久化存储的全链路逻辑。

**结论**：不涉及系统集成测试，下游 `IssueTimeMergeCleaningRule` 和 `IssueTimeCalculationCleaningRule` 无需修改，`first_reply_at_log` 字段语义扩展后自然纳入合并逻辑

### D. 用户体验相关性分析

* [ ] **交互逻辑变更**：涉及 Web 门户、控制台（Dashboard）或命令行工具（CLI）的交互流程调整。
* [ ] **感知性能变动**：变更可能显著影响页面的加载时间、同步请求的响应时延或异步任务的进度反馈。
* [ ] **文档与辅助能力**：涉及报错提示语、帮助中心链接、FAQ 或新功能的 Runbook 说明。
* [ ] **无障碍与多语种**：涉及国际化（i18n）支持、辅助功能或不同终端（移动端/桌面端）的适配。

**结论**：不涉及用户体验变更

### 5.1 需求相关性分析汇总结果

* [ ] need_security (需架构设计（含安全威胁分析和安全设计）)
* [ ] need_design (需架构设计)
* [ ] need_itest (需执行测试策略设计和全链路集成测试)
* [ ] need_ux (需架构设计（含UX设计）)
* [x] need_light (上述均未勾选，走快速合入通道)

---

## 6. 价值识别与业务评估

| 维度 | 评估问题 | 结论/说明 |
|------|---------|----------|
| **范围判定** | 该需求是否属于基础设施范围内？ | 是，数据采集清洗服务逻辑优化 |
| **规划一致性** | 该需求是否在年度技术规划中？ | 否 |
| **优先级** | 该需求优先级评估（高/中/低）？ | 中 |
| **通用性** | 该需求是否解决 3 个以上业务方的共性痛点？ | 否，当前仅供 opengauss 社区使用 |
| **必要性** | 现有组件通过配置变更是否无法实现目标？ | 是，需要修改 SQL 逻辑才能扩展响应范围 |
| **工作量** | 预计总工作量 | 2 人天 |
| **价值评估** | 实现后能减少多少手动操作或提升多少系统稳定性？ | 使首次响应时间计算更贴近真实情况，更全面地反映社区成员实际响应效率，提升指标数据准确性 |

**建议结论**：Accept

**原因描述**：当前首次响应时间仅依赖"关联PR"操作，漏计了社区成员通过评论、标签、状态变更等早期介入的响应行为，导致指标偏长。新逻辑通过 JOIN 排除作者和机器人操作，覆盖所有有效响应操作，技术方案清晰，风险可控，无 Schema 变更，单元测试覆盖率 100%。
