# #161 社区PR评论标记功能变更计划说明书

## 1. 变更概览

* **需求链接**: https://github.com/opensourceways/backlog/issues/161
* **需求分析说明书**: [链接](../Requirement%20Analysis/%23161%20Requirement%20Analysis%20Specification.md)
* **关联测试报告链接**: **不涉及**
* **开发责任人**: **ssignik**
* **变更责任人**: **ssignik**
* **变更时间**: **2026-04-17**
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

### 2.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `om/clean/comment_marker_cleaning_rule.py` | 评论标记清洗规则核心逻辑 |
| `om/utils/template_parser.py` | 模板解析器，判断评论类型并解析用户 |
| `om/collector/lgtm_config_collector.py` | LGTM 配置采集器，从 GitHub YAML 采集配置 |
| `om/db/table/merge_config_table.py` | 合并配置表管理 |
| `om/validator/comment_marker_validator.py` | 评论标记验证器 |
| `om/tasks/clean/comment_marker_task.py` | 任务入口脚本 |
| `docs/tasks/lgtm_approve_tag.md` | 功能设计文档 |

### 2.2 修改文件

| 文件路径 | 说明 |
|---------|------|
| 配置文件 | 添加 openfuyao 社区支持 |

### 2.3 逻辑变更说明

| 字段 | 变更前 | 变更后 |
|------|--------|--------|
| `is_active_lgtm` | 无 | 根据 lgtm_count 配置标记有效的 LGTM 评论 |
| `is_active_approve` | 无 | 每个 PR 标记一个有效的 Approve 评论 |
| `fact_community_merge_config` | 无 | 新增表，存储各社区 LGTM 配置 |

---

## 3. 详细执行步骤

> **原则**：步骤必须可操作、原子化，且包含明确的执行人。

**执行步骤：**

| 步骤 | 操作类型 | 操作内容描述 | 预期结果 | 执行人 |
|------|---------|-------------|---------|--------|
| **1** | **代码开发** | 完成所有任务开发（task1-task8），通过本地单元测试 | 所有测试通过 | **ssignik** |
| **2** | **代码合入** | 合并 PR 到主分支，触发CI/CD门禁 | 代码通过门禁，合入主分支 | **ssignik** |
| **3** | **配置调度任务** | 在华为云 DataArts 调度平台，对目标社区执行 `comment_marker` 清洗规则 | 清洗任务成功执行 | **ssignik** |
| **4** | **数据验证** | 执行验证 SQL，确认 is_active_lgtm 和 is_active_approve 字段正确写入 | 数据符合预期 | **ssignik** |

---

## 4. 生产环境验证

> **参考方向**：变更后如何快速确认"系统是好的"且功能符合预期。

**验证方式：**

### 4.1 数据标记验证

```sql
-- 统计有效标记数量
SELECT
    COUNT(*) FILTER (WHERE is_active_lgtm = true) AS 有效lgtm数,
    COUNT(*) FILTER (WHERE is_active_approve = true) AS 有效approve数,
    COUNT(*) AS 总评论数
FROM fact_{community}_comment
WHERE comment_type = 'pr_comment';

-- 查看特定 PR 的标记情况
SELECT
    uuid,
    body,
    user_login,
    is_active_lgtm,
    is_active_approve
FROM fact_{community}_comment
WHERE ref_id = '<替换为具体pr_id>'
  AND (body ILIKE '%/lgtm%' OR body ILIKE '%/approve%')
ORDER BY created_at DESC;
```

### 4.2 配置验证

```sql
-- 确认 merge_config 表数据
SELECT community, namespace, repo_path, lgtm_count
FROM fact_community_merge_config
WHERE community = '<community_name>';
```

### 4.3 日志验证

- 检查任务执行日志，确认无 ERROR 级别日志
- 确认标记更新数量符合预期

---

## 5. 回滚方案

> **原则**：回滚必须是受控且经过验证的，**禁止现场临时拼凑命令**。

> 出现以下任意一种情况，必须立即中断变更并启动回滚：
> 1. **核心阻塞**：清洗任务执行失败，数据写入异常。
> 2. **数据异常**：标记数量异常（远超配置要求）。
> 3. **不可抗力**：数据库异常或网络中断。

**回滚执行路径：**

| 步骤 | 回滚动作 | 执行命令/方式 | 预期结果 |
|------|---------|--------------|---------|
| **R1** | 停止调度任务 | 暂停华为云 DataArts 中清洗任务节点 | 停止继续写入新数据 |
| **R2** | 代码版本回退 | Revert PR 或 `git revert` 对应 commit，重新合入 | 代码恢复无此功能状态 |
| **R3** | 数据恢复 | 将 is_active_lgtm 和 is_active_approve 字段重置为 false | 数据恢复初始状态 |

---

## 6. 风险评估

| 风险项 | 风险等级 | 应对措施 |
|-------|---------|---------|
| 模板解析规则不适用于所有社区 | 中 | 支持从数据库动态配置模板，逐步完善各社区模板 |
| 并发处理大数据量时性能下降 | 低 | 使用分批查询和多线程优化 |
| 反馈评论解析逻辑复杂可能导致误标记 | 中 | 通过单元测试和人工抽样验证确保准确性 |

---

## 7. 附录

### 7.1 任务执行命令

```bash
# 带 interval 参数运行
om-dpy -m om.tasks.clean.comment_marker_task \
    --config config_prod.yaml \
    --community openfuyao \
    --batch-size 5000 \
    --interval 7

# 全量运行（去掉 interval）
om-dpy -m om.tasks.clean.comment_marker_task \
    --config config_prod.yaml \
    --community openfuyao \
    --batch-size 5000
```

### 7.2 单元测试命令

```bash
py -B -m pytest \
    --cov=om.clean.comment_marker_cleaning_rule \
    --cov-report=term-missing \
    tests/clean/test_comment_marker_cleaning_rule.py
```

### 7.3 相关文件路径

| 文件 | 路径 |
|------|------|
| 清洗规则 | `om/clean/comment_marker_cleaning_rule.py` |
| 模板解析器 | `om/utils/template_parser.py` |
| 配置采集器 | `om/collector/lgtm_config_collector.py` |
| 任务入口 | `om/tasks/clean/comment_marker_task.py` |