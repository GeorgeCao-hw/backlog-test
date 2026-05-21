# #999 Workflow Smoke Test — Architecture Design Specification

> 临时文档：仅用于验证 `architecture-to-test` workflow 的端到端行为。

## 1. 基础信息

- **需求链接**: N/A（smoke test）
- **设计目标**: 触发 architecture-to-test workflow，验证 SR/AR 识别和草稿 PR 生成。

## 2. SR（系统级需求 / 大颗粒）

- **SR-001**：系统在合入架构设计文档后，应自动生成测试设计骨架。
- **SR-002**：测试设计文档需要按 issue id 归档到统一目录。

## 3. AR（架构级需求 / 小颗粒）

- **AR-001**：workflow 通过 `gh pr view --json files` 拉取改动文件列表。
- **AR-002**：路径匹配兼容 `Architecture Design/` 与历史拼写 `Architecture Desgin/`。
- **AR-003**：生成阶段使用占位模板 + sed 替换，避免反引号转义问题。

## 4. 验收说明

merge 本 PR 后，预期：

1. workflow 日志出现 `::notice::` 列出 SR-001/SR-002 与 AR-001/AR-002/AR-003。
2. 自动开出标题为 `docs(test): test design from #<N>` 的草稿 PR。
3. 草稿 PR 内容为 `issue_docs/999/Test/test-design-report.md` 与 `test-design-cases.md`。
