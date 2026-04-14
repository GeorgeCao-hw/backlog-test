# AI辅助需求分析的工作模式

## 问题
如何高效使用 AI 辅助完成需求分析说明书？

## 最佳实践

### 工作流程
1. 使用 `gh issue view` 获取 Issue 完整信息（不要猜测）
2. 阅读 `templates/` 下的模板了解标准格式
3. 参考 `opensourceways/{repo}/issue_docs/` 下已有的优秀文档了解写作深度（如 `opensourceways/backlog/issue_docs/`）
4. 按阶段创建目录 → 填写当前阶段文档 → 提示下一步
5. 沉淀经验到 `context/experience/`

### 关键发现
- **文本是通用接口**：不需要复杂的Agent编排，结构化的 Markdown 提示词即可驱动 AI 完成高质量文档
- **模板 + 示例 = 高质量输出**：给 AI 同时提供模板（格式规范）和已有示例（写作深度参考），效果远好于只给模板
- **先跑起来，再迭代**：第一版文档不必完美，标注 [TODO] 后续补充即可
- **复合工程**：每次编写后把经验沉淀到 context/，下次效率更高

### 已封装的 Skill
- `/ai-design <Issue URL 或 issueId>`：DevOps 全生命周期文档编写（需求分析 → 架构设计 → 测试策略 → 变更计划）
- 位置：`.claude/commands/ai-design.md`
