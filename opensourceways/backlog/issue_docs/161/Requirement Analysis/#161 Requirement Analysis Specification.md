# #161 社区PR评论标记功能需求分析说明书

## 1. 基础信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/161
* **需求名称**: 社区PR评论标记功能（LGTM/Approve标记）
* **开发责任人**: **ssignik**

---

## 2. 需求场景说明

在开源社区的 PR 合并流程中，需要对 LGTM（Looks Good To Me）和 Approve 评论进行有效性标记。只有通过特定流程验证的评论才被视为有效的合并审批评论。

**现状问题：**
- 当前缺乏对 PR 评论的 LGTM/Approve 有效性标记
- 无法区分哪些评论是真正的合并审批，哪些只是普通的代码审查反馈

**场景说明：**
- 从反馈类型评论（包含 "Review Code Feedback"、"Review Guide" 或 "代码审视消息"）中解析有效的用户
- 对标记评论（只包含 `/lgtm` 或 `/approve`）进行有效性验证
- 根据各社区的 `lgtm_count` 配置要求，标记符合数量要求的 LGTM 评论
- 每个 PR 只标记一个有效的 Approve 评论

**数据范围：**
- 输入表：`fact_{community}_comment`（评论）、`fact_{community}_pr`（PR信息）、`fact_community_merge_config`（各社区LGTM配置）
- 输出字段：`fact_{community}_comment.is_active_lgtm`、`fact_{community}_comment.is_active_approve`

---

## 3. 需求验收标准

- [ ] 支持 openfuyao 社区的模板解析
- [ ] 从反馈类型评论中正确解析有效的 user_login 集合
- [ ] LGTM 标记：按 `lgtm_count` 配置数量标记有效评论，每位用户只保留最新的评论
- [ ] Approve 标记：每个 PR 只标记一个最新的有效评论
- [ ] 支持社区层级继承查询（如 mindie -> ascend）
- [ ] SQL 查询阶段添加关键字过滤，优化性能
- [ ] 单元测试覆盖核心逻辑

---

## 4. 需求设计与分解

### 4.1 核心逻辑方案

**处理流程：**

```
1. 查询已合并的 PR 列表（条件：state='merged', code_platform='gitcode'）
2. 批量获取每个 PR 的 lgtm_count 配置（从 fact_community_merge_config 表）
3. 从反馈类型评论中解析有效的 user_login 集合
   - Approve: 取最新的反馈评论解析 approve 用户
   - LGTM: 按时间倒序，取前 lgtm_count 条反馈评论解析 lgtm 用户
4. 获取所有标记评论（包含 /lgtm 或 /approve）
5. 验证并标记有效的评论
   - 用户必须在有效的 user_login 集合中
   - 每位用户的 LGTM 评论只保留最新的
   - Approve 只取最新的一个
```

**关键SQL变更：**

反馈评论查询（添加关键字过滤）：
```sql
SELECT uuid, body, created_at, user_login, comment_type, ref_id
FROM fact_{community}_comment
WHERE comment_type = 'pr_comment' AND ref_id IN ({pr_ids})
AND is_removed is null AND body ILIKE '%Review Code Feedback%'
ORDER BY created_at DESC
```

标记评论查询：
```sql
SELECT uuid, body, created_at, user_login, comment_type, ref_id
FROM fact_{community}_comment
WHERE comment_type = 'pr_comment' AND ref_id IN ({pr_ids})
AND is_removed is null AND (body ILIKE '%/lgtm%' OR body ILIKE '%/approve%')
ORDER BY ref_id, created_at DESC
```

### 4.2 任务清单

| 任务 ID | 任务描述 | 预期产出 | 预期工作量（人天） |
|---------|---------|---------|-----------------|
| **task1** | 实现 CommentMarkerCleaningRule 清洗规则 | `om/clean/comment_marker_cleaning_rule.py` | 1.0 |
| **task2** | 实现 TemplateParser 模板解析器 | `om/utils/template_parser.py` | 0.5 |
| **task3** | 实现 LgtmConfigCollector 配置采集器 | `om/collector/lgtm_config_collector.py` | 0.5 |
| **task4** | 实现 MergeConfigTable 配置表管理 | `om/db/table/merge_config_table.py` | 0.3 |
| **task5** | 实现 CommentMarkerValidator 验证器 | `om/validator/comment_marker_validator.py` | 0.3 |
| **task6** | 实现 comment_marker_task 任务入口 | `om/tasks/clean/comment_marker_task.py` | 0.3 |
| **task7** | 添加 openfuyao 社区支持 | 配置文件更新 | 0.2 |
| **task8** | 单元测试编写 | 测试用例 | 0.5 |

**总工作量：3.6 人天**

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

**结论**：不涉及架构设计变更，仅在现有清洗规则框架内新增功能模块

### C. 系统集成测试相关性分析

* [ ] 上述环节判定需要执行安全设计或架构设计。
* [ ] **跨组件影响**：变更会触发下游服务或关联系统的连锁反应（级联效应）。
* [ ] **核心组件管控**：含项目定级为 Core 的核心逻辑变更。
* [ ] **环境强依赖**：功能高度依赖内核参数、网络拓扑或特定的物理挂载。
* [ ] **端到端流程**：涉及从用户输入到持久化存储的全链路逻辑。

**结论**：不涉及系统集成测试，本功能为独立的数据清洗规则，不影响下游计算链路

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
| **范围判定** | 该需求是否属于基础设施范围内？ | 是，数据采集清洗服务功能扩展 |
| **规划一致性** | 该需求是否在年度技术规划中？ | 否 |
| **优先级** | 该需求优先级评估（高/中/低）？ | 中 |
| **通用性** | 该需求是否解决 3 个以上业务方的共性痛点？ | 否，当前主要支持 openfuyao 社区 |
| **必要性** | 现有组件通过配置变更是否无法实现目标？ | 是，需要开发新的清洗规则 |
| **工作量** | 预计总工作量 | 3.6 人天 |
| **价值评估** | 实现后能减少多少手动操作或提升多少系统稳定性？ | 实现 PR 评论有效性自动标记，提升社区运营指标数据准确性 |

**建议结论**：Accept

**原因描述**：该需求为社区运营指标计算提供基础数据支撑，通过自动化标记 LGTM/Approve 评论，减少人工统计工作量，技术方案清晰，风险可控。