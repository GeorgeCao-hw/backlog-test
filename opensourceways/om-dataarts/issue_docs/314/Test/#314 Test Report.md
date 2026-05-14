# #314 论坛用户内外部区分 测试报告

## 1. 基本信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/314
* **需求名称**: 论坛用户内外部区分——采集用户邮箱并标识华为/非华为归属
* **开发责任人**: ssignik
* **测试责任人**: ssignik
* **最终结论**： **[TODO]**  (通过 / 风险通过 / 不通过)
* **测试维度** ：
* [X] **功能自检测试**
* [ ] **体验测试**
* [X] **集成测试**
* [X] **安全与隐私测试**
* [ ] **可靠性与韧性测试**
* [ ] **可服务性与可观测性测试**
* [ ] **性能与伸缩性测试**

## 2. 测试过程

### 2.1 功能测试专项

**1.get_all_users 分页获取**: 验证 discuss_forum_api.get_all_users() 分页遍历

* **对应task(issueID)链接**: TASK1
* **预期结果**: 分页遍历完成，不遗漏用户，不无限循环
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**2.collect_users 数据写入**: 验证用户数据（含 email）upsert 写入

* **对应task(issueID)链接**: TASK2, TASK3
* **预期结果**: fact_forum_user 表 email 字段正确填充，已有数据不被空值覆盖
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**3.email 匹配 internal 填充**: 验证 forum_clean_task 清洗逻辑

* **对应task(issueID)链接**: TASK4
* **预期结果**: 匹配成功→正确内部/外部；无匹配→外部
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**4.配置开关验证**: collect_users = false 时不执行采集

* **对应task(issueID)链接**: TASK5
* **预期结果**: 不触发用户采集，其他任务正常
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**5.DWS 聚合表生成**: 验证 dws_forum_category_tag_internal_daily 数据正确

* **对应task(issueID)链接**: TASK6, TASK7
* **预期结果**: 按 date+category+tag+internal 维度聚合，UUID 规则正确
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**6.幂等性验证**: 重复执行不产生重复数据

* **对应task(issueID)链接**: TASK2, TASK4
* **预期结果**: upsert 逻辑正确，重复执行数据一致
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

### 2.3 集成测试专项

**1.采集→清洗→聚合全链路**: 端到端数据一致性验证

* **对应task(issueID)链接**: TASK8
* **预期结果**: 全链路执行成功，fact 层和 DWS 层数据一致，现有功能无回归
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**2.跨表 JOIN 正确性**: email→dws_community_user→dws_user_company 多表关联

* **对应task(issueID)链接**: TASK4
* **预期结果**: SQL 匹配逻辑返回正确 uuid 和 internal 值
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**3.多社区兼容性**: 不同 discuss 社区分别执行

* **对应task(issueID)链接**: TASK8
* **预期结果**: 各社区数据独立正确，表名动态替换无误
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**4.数据库表结构兼容性**: 新增字段和表不破坏现有结构

* **对应task(issueID)链接**: TASK3, TASK6
* **预期结果**: 现有查询和操作不受影响
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

### 2.4 安全与隐私测试专项

**1.API Key 加密存储验证**: 检查 token 字段非明文存储

* **对应task(issueID)链接**: SEC1
* **预期结果**: 数据库中 token 为 AES 加密密文
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**2.日志脱敏校验**: 日志中不含用户邮箱明文

* **对应task(issueID)链接**: SEC2
* **预期结果**: 日志仅记录数量、进度、耗时
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**3.email 字段存储安全**: DWS 表不暴露邮箱明细

* **对应task(issueID)链接**: SEC1
* **预期结果**: dws_forum_category_tag_internal_daily 不含 email 字段
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

**4.传输加密验证**: API 调用使用 HTTPS

* **对应task(issueID)链接**: SEC1
* **预期结果**: base_url 为 https://，HTTP 请求被拒绝
* **测试结果**： **[TODO]** （Passed/Failed）
* **证明截图**:  **[TODO]**

---

## 3. 测试结果汇总表

| 测试维度          | 用例总数   | 重点测试点描述             | 通过数    | 不通过数   | 结论 (Pass/Fail) |
|---------------|--------|---------------------|--------|--------|----------------|
| **功能测试**      | 6 | 分页采集、upsert、email匹配清洗、配置开关、DWS聚合、幂等 | [TODO] | [TODO] | [TODO]         |
| **集成测试**      | 4 | 全链路一致性、跨表JOIN、多社区兼容、表结构兼容 | [TODO] | [TODO] | [TODO]         |
| **安全与隐私测试**   | 4 | API Key加密、日志脱敏、email隔离、HTTPS传输 | [TODO] | [TODO] | [TODO]         |

---

## 4. 遗留问题与风险说明

| 缺陷 ID         | 缺陷描述       | 严重程度 | 处理意见 (修复/忽略/转运维) |
|---------------|------------|------|------------------|
| **[Bug-#01]** | **[TODO]** | 中    | **[TODO]**       |
