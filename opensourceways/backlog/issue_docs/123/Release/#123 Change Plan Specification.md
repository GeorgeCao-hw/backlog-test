# #123 opengauss Issue首次响应时间扩展变更计划说明书

## 1. 变更概览

* **需求链接**: https://github.com/opensourceways/backlog/issues/123
* **需求分析说明书**: [链接](../Requirement%20Analysis/%23123%20Requirement%20Analysis%20Specification.md)
* **关联测试报告链接**: **不涉及**
* **开发责任人**: **ssignik**
* **变更责任人**: **ssignik**
* **变更时间**: **2026-04-03**
* **变更等级**:

* [ ] **L1 (重大)**

> * 定义：涉及核心数据库 Schema 修改、全局配置中心变更或底层网络拓扑调整。
> * 管控要求：
> > * 1.值守要求：变更实行开发+运维1+1check。
> > * 2.强制灰度：严禁全量发布，必须包含分级发布步骤
> > * 3.预案验证：必须在测试环境完成 1:1 的回滚实操演练。
> > * 4.变更时间：强制选在业务低峰期。

* [ ] **L2 (普通)**

> * 定义：微服务配置变更、非核心插件发布、新开发服务上线。
> * 管控要求：
> > * 1.值守要求：变更实行开发+运维1+1check。
> > * 2.预案验证：必须在测试环境完成 1:1 的回滚实操演练。

* [X] **L3 (轻微)**

> * 定义：文档更新、前端静态资源发布、不影响逻辑的配置微调和Bug修复。
> * 管控要求：
> > * 1.值守要求：变更可由开发通过发布流水线发布上线。

---

## 2. 变更内容

### 2.1 修改文件

| 文件路径 | 说明 |
|---------|------|
| `om/clean/issue_operate_log_time_cleaning_rule.py` | 移除 `ENABLED_COMMUNITIES` 白名单；`_extract_times_from_operate_log` SQL 改为 JOIN `fact_{community}_issue` + 子查询排除机器人 |
| `tests/clean/test_issue_operate_log_time_cleaning_rule.py` | 删除失效测试，新增6个覆盖新逻辑的测试方法，覆盖率 100% |
| `docs/tasks/clean.md` | 更新 `issue_operate_log_time` 规则说明，反映新的首次响应时间逻辑 |

### 2.2 逻辑变更说明

| 字段 | 变更前 | 变更后 |
|------|--------|--------|
| `first_reply_at_log` | `MIN(created_at) WHERE action_type = 'add_issue_mr_link'` | `MIN(created_at)` 其中 `operator_login != issue作者` 且 `operator_login` 不在机器人表中 |
| `closed_at_log` | `MAX(created_at) WHERE action_type='changed_issue_custom_state' AND content LIKE '%to 已完成%'` | 不变 |
| 社区过滤 | 规则内部 `ENABLED_COMMUNITIES = ['opengauss']` 白名单控制 | 由调用方任务脚本控制，规则内部无限制 |

---

## 3. 详细执行步骤

> **原则**：步骤必须可操作、原子化，且包含明确的执行人。

**执行步骤：**

| 步骤 | 操作类型 | 操作内容描述 | 预期结果 | 执行人 |
|------|---------|-------------|---------|--------|
| **1** | **代码合入** | 合并 PR `feature/zy/opengauss_first_response_extend` 到主分支，触发CI/CD门禁 | 代码通过门禁，合入主分支 | **ssignik** |
| **2** | **配置调度任务** | 在华为云 DataArts 调度平台，对 opengauss 社区执行 `issue_operate_log_time` 清洗规则 | 清洗任务成功执行，`first_reply_at_log` 字段更新 | **ssignik** |
| **3** | **联动规则执行** | 依次执行 `issue_time_merge` → `issue_holiday_calculation` → `issue_time_calculation_with_holiday_pending` | `final_first_reply_at` 和 `first_reply_time` 字段同步更新 | **ssignik** |
| **4** | **数据验证** | 执行验证 SQL，确认变化方向符合预期（时间只缩短或不变，无异常延长） | 数据变化符合预期，无异常 | **ssignik** |

---

## 4. 生产环境验证

> **参考方向**：变更后如何快速确认"系统是好的"且功能符合预期。

**验证方式：**

### 4.1 数据变化量验证

```sql
-- 对比快照，统计发生变化的 issue 数量
SELECT
    COUNT(*) FILTER (WHERE fi.first_reply_at_log IS NULL     AND snap.first_reply_at_log IS NOT NULL) AS 值被清空,
    COUNT(*) FILTER (WHERE fi.first_reply_at_log IS NOT NULL AND snap.first_reply_at_log IS NULL)     AS 新补充值,
    COUNT(*) FILTER (WHERE fi.first_reply_at_log < snap.first_reply_at_log)                           AS 时间提前,
    COUNT(*) FILTER (WHERE fi.first_reply_at_log > snap.first_reply_at_log)                           AS 时间延后_异常,
    COUNT(*) FILTER (WHERE fi.first_reply_at_log = snap.first_reply_at_log)                           AS 未变化
FROM fact_opengauss_issue fi
JOIN snapshot_first_reply_at_log snap ON snap.uuid = fi.uuid;
```

**期望**：`值被清空 = 0`，`时间延后_异常 = 0`，`新补充值 > 0` 或 `时间提前 > 0`

### 4.2 新补充值合理性核查

```sql
-- 查看新增 first_reply_at_log 的 issue，核对操作日志内容
SELECT
    ol.created_at,
    ol.action_type,
    ol.operator_login,
    CASE WHEN ol.operator_login = i.user_login THEN '是作者' ELSE '非作者' END AS author_check,
    CASE WHEN r.user_login IS NOT NULL THEN '是机器人' ELSE '非机器人' END     AS robot_check
FROM fact_opengauss_issue_operate_log ol
JOIN fact_opengauss_issue i
    ON i.id = ol.issue_id AND i.code_platform = ol.code_platform
LEFT JOIN fact_community_robot_user r ON r.user_login = ol.operator_login
WHERE ol.issue_id = '<替换为具体 issue_id>'
  AND ol.code_platform = 'gitee'
ORDER BY ol.created_at;
```

### 4.3 日志验证

- 检查任务执行日志，确认无 ERROR 级别日志
- 确认 `first_reply_at_log` 和 `closed_at_log` 均成功写入

---

## 5. 回滚方案

> **原则**：回滚必须是受控且经过验证的，**禁止现场临时拼凑命令**。

> 出现以下任意一种情况，必须立即中断变更并启动回滚：
> 1. **指标异常**：`时间延后_异常 > 0`（新逻辑取 MIN，不应出现时间延后）。
> 2. **核心阻塞**：清洗任务执行失败，数据写入异常。
> 3. **不可抗力**：数据库异常或网络中断。

**回滚执行路径：**

| 步骤 | 回滚动作 | 执行命令/方式 | 预期结果 |
|------|---------|--------------|---------|
| **R1** | 停止调度任务 | 暂停华为云 DataArts 中 opengauss 清洗任务节点 | 停止继续写入新数据 |
| **R2** | 代码版本回退 | Revert PR 或 `git revert` 对应 commit，重新合入 | 代码恢复旧逻辑 |
| **R3** | 数据恢复 | 重新执行旧版本清洗规则（`issue_operate_log_time` → `issue_time_merge` → `issue_time_calculation`） | `first_reply_at_log` 恢复为关联PR逻辑的计算值 |

**注意**：本次变更为逻辑扩展（新逻辑结果 ≤ 旧逻辑结果），回滚对下游 `final_first_reply_at` 和 `first_reply_time` 的影响方向为恢复偏大值，不会产生数据错乱。

---

## 6. 风险评估

| 风险项 | 风险等级 | 应对措施 |
|-------|---------|---------|
| 机器人账号列表不完整，导致机器人操作被误计入 | 低 | `fact_community_robot_user` 为已维护的全局共享表，可持续完善 |
| opengauss 操作日志数据量大，JOIN 查询性能下降 | 低 | 查询使用流式游标分批处理，不全量加载 |
| 历史数据补录后 `first_reply_time` 大幅缩短 | 低 | 为预期效果，可结合业务确认是否需要设置变化上限 |

---

## 7. 附录

### 7.1 任务执行命令

```bash
# opengauss 首次响应时间清洗（新逻辑）
python om/tasks/clean/cleaning_task.py \
    --config config.yaml \
    --communities opengauss \
    --rules issue_operate_log_time

# 完整链路（含下游合并和计算）
python om/tasks/clean/cleaning_task.py \
    --config config.yaml \
    --communities opengauss \
    --rules issue_operate_log_time,issue_time_merge,issue_holiday_calculation,issue_time_calculation_with_holiday_pending
```

### 7.2 单元测试命令

```bash
py -B -m pytest \
    --cov=om.clean.issue_operate_log_time_cleaning_rule \
    --cov-report=term-missing \
    tests/clean/test_issue_operate_log_time_cleaning_rule.py
```
