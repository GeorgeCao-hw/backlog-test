# #101 论坛负向事件与Issue严重缺陷识别变更计划说明书

## 1. 变更概览

* **需求链接**: https://github.com/opensourceways/backlog/issues/101
* **需求分析说明书**: [链接](../Requirement%20Analysis/%23101%20论坛负向事件与Issue严重缺陷识别需求分析说明书.md)
* **关联测试报告链接**: **不涉及**
* **开发责任人**: **ssignik**
* **变更责任人**: **ssignik**
* **变更时间**: **2026-03-29**
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
| `om/dws/forum_negative_event_scorer.py` | 论坛负向事件评分逻辑 |
| `om/dws/issue_defect_scorer.py` | Issue严重缺陷评分逻辑 |
| `om/tasks/forum/negative_event_task.py` | 论坛负向事件任务入口 |
| `om/tasks/issue/defect_analysis_task.py` | Issue缺陷分析任务入口 |
| `om/db/table/forum_negative_event_table.py` | 论坛负向事件表定义 |
| `om/db/table/issue_defect_table.py` | Issue缺陷表定义 |
| `config/forum_negative_event_keywords.yaml` | 论坛负向事件关键词配置 |
| `config/issue_defect_keywords.yaml` | Issue缺陷关键词配置 |

### 2.2 新增数据库表

| 表名 | 说明 |
|------|------|
| `dwm_{community}_forum_negative_event` | 论坛负向事件评分表 |
| `dwm_{community}_issue_defect` | Issue严重缺陷评分表 |

### 2.3 数据库表结构

#### dwm_{community}_forum_negative_event

| 字段 | 类型 | 说明 |
|------|------|------|
| uuid | VARCHAR(512) | 主键，格式：{community}-{topic_id} |
| topic_id | VARCHAR(512) | 关联的 topic id |
| community | VARCHAR(255) | 社区名称 |
| score | INT | 综合得分 (0-100) |
| risk_level | VARCHAR(32) | 风险等级 (P0-P4) |
| negative_type | VARCHAR(32) | 负向类型编码 |
| negative_type_name | VARCHAR(64) | 负向类型名称 |
| matched_keywords | TEXT | 命中的关键词 JSON |
| eval_criteria | TEXT | 评判标准说明 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

#### dwm_{community}_issue_defect

| 字段 | 类型 | 说明 |
|------|------|------|
| uuid | VARCHAR(512) | 主键，格式：{community}-{code_platform}-{issue_id} |
| issue_id | VARCHAR(512) | Issue ID |
| issue_number | INT | Issue编号 |
| community | VARCHAR(255) | 社区名称 |
| code_platform | VARCHAR(50) | 代码托管平台 |
| severity_score | INT | 严重度评分 |
| severity_level | VARCHAR(32) | 严重等级 |
| is_severe | VARCHAR(8) | 是否严重缺陷 |
| defect_category | VARCHAR(64) | 缺陷分类 |
| cve_id | VARCHAR(32) | CVE编号 |
| score_reasons | TEXT | 评分原因 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

---

## 3. 详细执行步骤

> **原则**：步骤必须可操作、原子化，且包含明确的执行人。

**执行步骤：**

| 步骤 | 操作类型 | 操作内容描述 | 预期结果 | 执行人 |
|------|---------|-------------|---------|--------|
| **1** | **代码合入** | 合并代码到主分支，触发CI/CD流水线 | 代码通过门禁，合入到主分支 | **ssignik** |
| **2** | **配置调度任务** | 在华为云DataArts调用平台配置调用任务 | 调度任务成功执行 | **ssignik** |
| **3** | **功能验证** | 配置MagicAPI接口调用数据 | 能够正常查回数据 | **ssignik** |

---

## 4. 生产环境验证

> **参考方向**：变更后如何快速确认"系统是好的"且功能符合预期。

**验证方式：**

### 4.1 数据验证

```sql
-- 验证论坛负向事件表
SELECT COUNT(*) FROM dwm_openeuler_forum_negative_event;
SELECT topic_id, score, risk_level, negative_type_name
FROM dwm_openeuler_forum_negative_event
ORDER BY score DESC LIMIT 10;

-- 验证Issue缺陷表
SELECT COUNT(*) FROM dwm_vllm_issue_defect;
SELECT issue_number, code_platform, severity_score, severity_level, defect_category, cve_id
FROM dwm_vllm_issue_defect
ORDER BY severity_score DESC LIMIT 10;
```

### 4.2 日志验证

- 检查任务执行日志，确认无 ERROR 级别日志
- 验证关键词匹配结果符合预期
- 确认评分计算逻辑正确

### 4.3 业务验证

- 验证增量模式参数 `--incremental-days` 生效
- 验证删除数据同步处理正确
- 验证多代码平台支持（Issue缺陷）

---

## 5. 回滚方案

> **原则**：回滚必须是受控且经过验证的，**禁止现场临时拼凑命令**。

> 出现以下任意一种情况，必须立即中断变更并启动回滚：
> 1. **指标异常**：错误率超过 5% 或 P99 延迟增加超过 50% 且持续 2 分钟。
> 2. **核心阻塞**：主要业务链路中断，且无法在 10 分钟内定位根因。
> 3. **不可抗力**：变更期间发生严重的云服务中断或网络分区。

**回滚执行路径：**

| 步骤 | 回滚动作 | 执行命令/方式 | 预期结果 |
|------|---------|--------------|---------|
| **R1** | 停止调用任务 | 删除华为云DataArts任务节点 | 流水线恢复之前逻辑 |
| **R2** | 数据清理 | `DROP TABLE IF EXISTS dwm_{community}_forum_negative_event;` `DROP TABLE IF EXISTS dwm_{community}_issue_defect;` | 新增表被删除 |

**注意**：由于本次变更为新增功能，回滚后不影响现有业务。

---

## 6. 风险评估

| 风险项 | 风险等级 | 应对措施 |
|-------|---------|---------|
| 关键词配置不完整 | 低 | 后续迭代优化关键词列表 |
| 大量历史数据处理性能问题 | 中 | 使用增量模式，分批处理 |
| 评分误判 | 低 | 结合人工审核，持续优化规则 |

---

## 7. 附录

### 7.1 任务执行命令

```bash
# 论坛负向事件 - 全量模式
python om/tasks/forum/negative_event_task.py \
    --config config.yaml \
    --communities openeuler \
    --mode full

# 论坛负向事件 - 增量模式（处理前3天至今的数据）
python om/tasks/forum/negative_event_task.py \
    --config config.yaml \
    --communities openeuler \
    --mode incremental \
    --incremental-days 3

# Issue严重缺陷 - 全量模式
python om/tasks/issue/defect_analysis_task.py \
    --config config.yaml \
    --communities vllm \
    --mode full

# Issue严重缺陷 - 增量模式（处理前3天至今的数据）
python om/tasks/issue/defect_analysis_task.py \
    --config config.yaml \
    --communities vllm \
    --mode incremental \
    --incremental-days 3
```

### 7.2 单元测试命令

```bash
python -B -m pytest \
    --cache-clear \
    -p no:cacheprovider \
    --cov=./om/dws \
    --cov-report=term-missing \
    tests/dws/
```