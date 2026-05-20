# Architecture Design 模板

## 用途

架构设计说明书模板，适用于 Phase 1.1.4。

## 适用阶段

Phase 1.1.4 — AI 写架构设计（need_design 或 need_security 标签触发）

## 产出文件

- `02-architecture.md` — 架构设计说明书
- `02-architecture-qa.md` — 架构 QA 报告（由 architecture-qa agent 产出）

## 模板要点

- 功能设计：架构图、数据流图、组件职责与接口、TASK 清单
- 非功能设计：安全与隐私（need_security 时必填）、可靠性、可服务性、性能
- 不涉及的章节保留结构，标注原因而非删除

## 相关文档

- `AGENTS.md` — 架构设计触发条件
- `context/experience/架构设计说明书编写经验.md`
- `context/team/安全设计与开发最佳实践.md`
