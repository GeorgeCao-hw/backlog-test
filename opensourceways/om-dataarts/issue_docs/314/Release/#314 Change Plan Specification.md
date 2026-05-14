# #314 论坛用户内外部区分 变更计划说明书

## 1. 变更概览

* **需求链接**: https://github.com/opensourceways/backlog/issues/314
* **关联测试报告链接**: 待补充
* **开发责任人**: ssignik
* **变更责任人**: ssignik
* **变更时间**: 2026-05-30
* **变更等级**:

* [ ] **L1 (重大)**

> * 定义：涉及核心数据库 Schema 修改、全局配置中心变更或底层网络拓扑调整。

* [x] **L2 (普通)**

> * 定义：微服务配置变更、非核心插件发布、新开发服务上线。
> * 管控要求：
> > * 1.值守要求：变更实行开发+运维1+1check。
> > * 2.预案验证：必须在测试环境完成 1:1 的回滚实操演练。

* [ ] **L3 (轻微)**

---

## 2. 详细执行步骤

| 步骤 | 操作类型 | 操作内容描述 | 预期结果 | 执行人 |
|---|---|---|---|---|
| **1** | **数据库变更** | 执行 ALTER TABLE 为 `fact_{community}_forum_user` 新增 `email` 和 `internal` 字段 | 字段创建成功，已有数据不受影响 | ssignik |
| **2** | **数据库变更** | 创建 `dws_{community}_forum_category_tag_internal_daily` 表 | 表创建成功 | ssignik |
| **3** | **配置变更** | 在 `service_platform_config` 表中，为需要启用用户采集的社区添加 `params.collect_users = true` 和 `params.api_username` | 配置更新成功 | ssignik |
| **4** | **代码部署** | 部署 om-dataarts 新版本（含用户采集、清洗、DWS 功能） | 服务正常运行 | ssignik |
| **5** | **功能验证** | 手动触发 forum_task 验证用户采集功能 | `fact_forum_user` 表中出现 email 数据 | ssignik |
| **6** | **功能验证** | 手动触发 forum_clean_task 验证 internal 填充 | `fact_forum_user.internal` 字段正确填充 | ssignik |
| **7** | **功能验证** | 手动触发 dws_table_data_generate 验证新 DWS 表 | `dws_forum_category_tag_internal_daily` 表数据正确 | ssignik |
| **8** | **线上观测** | 检查采集日志，确认无报错，匹配率符合预期 | 采集和匹配指标正常 | ssignik |

### 数据库变更详细脚本

```sql
-- 步骤1: fact_forum_user 新增字段
ALTER TABLE fact_{community}_forum_user
ADD COLUMN IF NOT EXISTS email VARCHAR(512) NULL,
ADD COLUMN IF NOT EXISTS internal VARCHAR(10) NULL;

-- 索引
CREATE INDEX IF NOT EXISTS idx_fact_{community}_forum_user_email
ON fact_{community}_forum_user(email)
WHERE email IS NOT NULL;
```

```sql
-- 步骤2: 创建 DWS 表
CREATE TABLE IF NOT EXISTS dws_{community}_forum_category_tag_internal_daily (
    uuid VARCHAR(500) NOT NULL,
    sub_community VARCHAR(255),
    date DATE,
    category_id VARCHAR(512),
    category_name VARCHAR(512),
    tag VARCHAR(512),
    internal VARCHAR(10),
    topic_count INT4 DEFAULT 0,
    reply_topic_count INT4 DEFAULT 0,
    one_day_response_topic_count INT4 DEFAULT 0,
    resolved_topic_count INT4 DEFAULT 0,
    total_first_reply_time INT8 DEFAULT 0,
    avg_first_reply_time INT8 DEFAULT 0,
    CONSTRAINT pk_dws_forum_cat_tag_internal PRIMARY KEY (uuid)
);
```

**注意**: 需要对每个 discuss 类型社区（openeuler、opengauss 等）分别执行上述 SQL。

### 配置变更详细

```sql
-- 步骤3: 更新 service_platform_config（合并为一条UPDATE，避免多次写盘）
UPDATE service_platform_config
SET params = jsonb_set(
    jsonb_set(
        COALESCE(params, '{}'::jsonb),
        '{collect_users}',
        'true'::jsonb
    ),
    '{api_username}',
    '"admin"'::jsonb
)
WHERE platform = 'discuss'
AND service = 'forum'
AND community = 'openeuler';  -- 按需替换社区名
```

---

## 3. 生产环境验证

**验证方式:**

1. **采集验证**: 执行 forum_task 后，查询 `SELECT count(*) FROM fact_{community}_forum_user WHERE email IS NOT NULL` 确认 email 字段已填充
2. **匹配率验证**: 执行 forum_clean_task 后，查询 `SELECT internal, count(*) FROM fact_{community}_forum_user GROUP BY internal` 确认 internal 分布合理
3. **DWS 验证**: 执行 dws_table_data_generate 后，查询 `SELECT * FROM dws_{community}_forum_category_tag_internal_daily LIMIT 10` 确认数据生成正确
4. **无回归验证**: 确认现有论坛采集任务（帖子、分类、标签等）不受影响
5. **日志检查**: 确认采集日志无 ERROR，用户数量和匹配率在预期范围内

---

## 4. 回滚方案

**回滚执行路径：**

| 步骤 | 回滚动作 | 执行命令/方式 | 预期结果 |
|---|---|---|---|
| **R1** | 代码回退 | 回退 om-dataarts 到上一版本 | 用户采集、清洗、DWS 功能不再执行 |
| **R2** | 配置还原 | 将 `params.collect_users` 设为 `false` | 即使新版本部署，也不执行用户采集 |
| **R3** | 数据保留 | email 和 internal 字段及 DWS 表数据保留（不影响现有功能） | 现有功能不受影响 |
| **R4** | 字段清理（可选） | `ALTER TABLE fact_{community}_forum_user DROP COLUMN email, DROP COLUMN internal; DROP TABLE dws_{community}_forum_category_tag_internal_daily;` | 完全恢复到变更前状态（需对每个社区分别执行） |

**说明**:
- 新增的 `email` 和 `internal` 字段为可 NULL，不影响现有数据读写
- 新增的 DWS 表为独立表，不影响现有 DWS 分析
- 因此回滚风险较低，代码回退 + 配置关闭即可，数据库变更可以保留
