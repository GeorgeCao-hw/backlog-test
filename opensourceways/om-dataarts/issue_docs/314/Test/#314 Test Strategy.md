# #314 论坛用户内外部区分 测试策略设计说明书

## 1. 基本信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/314
* **需求名称**: 论坛用户内外部区分——采集用户邮箱并标识华为/非华为归属
* **核心目标**:
  验证论坛用户采集、内外部标识清洗、DWS 聚合统计全链路功能正确性，以及架构设计中定义的安全与隐私、可靠性与韧性等非功能专项任务的闭环验收。
* **开发责任人**: ssignik
* **测试责任人**: ssignik

---

## 2. 测试维度确认

> **操作指南**：请依据需求分析阶段的标签勾选。勾选后，必须在"第 3 节"提供对应的测试用例或方案。

* [X] **功能自检测试**

> * **测试重点：** API 分页逻辑、数据映射 upsert、email 匹配清洗、DWS 聚合计算、配置开关。
>* **目的：** 确保功能实现符合设计预期。
>* **触发条件：** 强制执行,**可委托开发测试完成，测试完成验收**。

* [ ] **体验测试**

> * 不涉及。本需求为后端数据采集和分析功能，无用户界面变更。

* [X] **集成测试**

> * **测试重点：** 采集→清洗→聚合全链路数据一致性、跨表 JOIN 查询正确性、数据库表结构兼容性。
>* **目的：** 消除组件间级联影响风险。
>* **触发条件：** 需求标签含 `need_itest`

* [X] **安全与隐私测试**：

> * **测试重点：** API Key 加密存储验证、日志脱敏校验（邮箱不出现在日志中）、email 字段存储安全性。
>* **目的：** 验证"纵深防御"机制是否生效，确保无隐私泄露。
>* **触发条件：** 需求标签含 `need_security`

* [ ] **可靠性与韧性测试**

> * 不涉及核心 Core 服务变更。

* [ ] **可服务性与可观测性测试**

> * 不涉及核心 Core 服务变更。

* [ ] **性能与伸缩性测试**

> * 不涉及核心 Core 服务变更。

---

## 3. 专项验证设计和执行详情

> 测试自检
>* [ ] **Task 闭环**: 架构设计说明书中定义的 TASK 是否均有对应的测试结果？
>* [ ] **证据留存**: 关键测试（如安全扫描）是否附带了截图或报告链接？

### 3.1 功能测试专项

**1.get_all_users 分页获取**: 调用 discuss_forum_api.get_all_users()，验证分页遍历正常，每页约 50 条，最后一页返回空列表时停止

* **对应task(issueID)链接**: TASK1
* **预期结果**: 分页遍历完成，不遗漏用户，不无限循环

**2.collect_users 数据写入**: 调用 discuss_forum_collector.collect_users()，验证用户数据（含 email）正确 upsert 写入 fact_forum_user 表

* **对应task(issueID)链接**: TASK2, TASK3
* **预期结果**: fact_forum_user 表中 email 字段正确填充，已有数据不被空值覆盖

**3.email 精确匹配 internal 填充**: 执行 forum_clean_task，验证 email 匹配 dws_community_user.emails 后获取平台 login，再查询 dws_user_company 获取 internal 值

* **对应task(issueID)链接**: TASK4
* **预期结果**:
  - email 匹配成功且任一平台 internal="内部" → 结果为"内部"
  - email 匹配成功但所有平台 internal≠"内部" → 结果为"外部"
  - email 无匹配 → internal 为"外部"（默认值）

**4.配置开关验证**: 当 service_platform_config.params.collect_users = false 时，不执行用户采集

* **对应task(issueID)链接**: TASK5
* **预期结果**: collect_users 功能不触发，不影响其他采集任务

**5.DWS 聚合表生成**: 执行 dws_table_data_generate，验证 dws_forum_category_tag_internal_daily 表数据正确

* **对应task(issueID)链接**: TASK6, TASK7
* **预期结果**:
  - 统计表按 date + category_id + tag + internal 维度聚合
  - tag 为空时使用"无标签"占位
  - internal 为 NULL 时默认"外部"
  - UUID 生成规则：{community}_{category_id}_{tag}_{internal}_{date}

**6.幂等性验证**: 重复执行 collect_users 和 forum_clean_task，验证不产生重复数据

* **对应task(issueID)链接**: TASK2, TASK4
* **预期结果**: upsert 逻辑正确，重复执行后数据与首次一致

### 3.2 体验测试专项

> 不涉及，删除。

### 3.3 集成测试专项

**1.采集→清洗→聚合全链路**: 依次执行 forum_task → forum_clean_task → dws_table_data_generate，验证端到端数据一致性

* **对应task(issueID)链接**: TASK8
* **预期结果**:
  - fact_forum_user 表 email 和 internal 字段均有值
  - dws_forum_category_tag_internal_daily 表统计数据与 fact 层数据一致
  - 现有论坛采集任务（帖子、分类、标签）不受影响

**2.跨表 JOIN 正确性**: 验证 forum_clean_task 中 email→dws_community_user→dws_user_company 的多表关联查询结果正确

* **对应task(issueID)链接**: TASK4
* **预期结果**: SQL 匹配逻辑（emails @> ARRAY[fu.email]::text[]）返回正确的 uuid 和 internal 值

**3.多社区兼容性**: 对不同 discuss 类型社区（如 openeuler、opengauss）分别执行，验证表名动态替换正确

* **对应task(issueID)链接**: TASK8
* **预期结果**: 各社区 fact_{community}_forum_user 和 dws_{community}_forum_category_tag_internal_daily 数据独立正确

**4.数据库表结构兼容性**: 验证新增字段（email, internal）和新增表不破坏现有表结构和查询

* **对应task(issueID)链接**: TASK3, TASK6
* **预期结果**: 现有 SQL 查询和 ORM 操作不受影响，新字段为可 NULL 不强制填充

### 3.4 安全与隐私测试专项

**1.API Key 加密存储验证**: 检查 service_platform_config.token 字段存储的是加密后值，非明文 API Key

* **对应task(issueID)链接**: SEC1
* **预期结果**: 数据库中 token 字段为 AES 加密密文，运行时解密仅在内存中

**2.日志脱敏校验**: 执行用户采集任务后检查日志输出，确认不包含任何用户邮箱明文

* **对应task(issueID)链接**: SEC2
* **预期结果**: 日志中仅记录采集用户数量、分页进度、耗时，无邮箱地址

**3.email 字段存储安全**: 验证 email 字段不通过任何对外接口暴露（DWS 表仅含 internal 维度，不含邮箱明细）

* **对应task(issueID)链接**: SEC1
* **预期结果**: dws_forum_category_tag_internal_daily 表不含 email 字段，仅有 internal 维度

**4.传输加密验证**: 确认 API 调用使用 HTTPS 协议

* **对应task(issueID)链接**: SEC1
* **预期结果**: base_url 以 https:// 开头，HTTP 请求被拒绝

---
