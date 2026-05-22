# #997 spec-template E2E — Architecture Design Specification

> 验证 architecture-to-test 新版 Generate step 能从 agent-development-specification 拉取并应用 Test Strategy / Test Specification 模板。

## 1. 基础信息

- **目标**：合入本 PR 后，自动生成的 `test-design-report.md` / `test-design-cases.md` 应分别来自上游 Strategy / Specification 模板，含 7 个专项章节 + 源信息块。

## 2. 功能设计分解TASK清单

| Task ID | 描述                                           | 负责人 |
| ------- | ---------------------------------------------- | ------ |
| T-201   | 自托管 runner 能拉取 raw.githubusercontent.com | bot    |
| T-202   | 模板 H1 改写为 `# #997 ...`                    | bot    |
| T-203   | 源信息块插入位置正确（紧跟 H1）                | bot    |
