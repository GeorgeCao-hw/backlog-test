# Release 模板

## 用途

变更计划说明书模板。**注意：变更发布已迁移到 release-mgmt 仓库**，此处保留模板参考。

## 适用阶段

Phase 3 — 发布驱动（在 release-mgmt 仓库执行）

## 产出文件

- `04-deploy-notes.md` — 部署注意事项
- `05-upgrade-guide.md` — 升级指导
- `05-upgrade-guide-qa.md` — 升级指导 QA 报告

## 变更等级判定

| 等级 | 定义     | 示例                             |
| ---- | -------- | -------------------------------- |
| L1   | 重大变更 | 数据库 Schema 修改、网络拓扑调整 |
| L2   | 普通变更 | 新功能上线、配置变更             |
| L3   | 轻微变更 | Bug 修复、代码清理               |

## 相关文档

- release-mgmt 仓库：实际发布流程执行地
- `team-end-to-end-process.md` §三 Phase 3
