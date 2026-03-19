根据 GitHub Issue，完成 DevOps 全生命周期文档编写（需求分析 → 架构设计 → 测试策略 → 变更计划）。

## 输入参数
- $ARGUMENTS: GitHub Issue URL 或 Issue 编号（如 `https://github.com/opensourceways/backlog/issues/29` 或 `29`）

## 核心理念
> 遵循"文档即记忆"原则：同一份文档，人类和 AI 都能读懂、都能用。
> 不追求完美，先跑起来。标注 [TODO] 的内容后续补充。
> 每次实践产生复利：完成后沉淀经验到 context/experience/。
> 所有设计应参考 `context/team/` 中的设计和开发规范。

## 参考规范
编写文档时应参考 `context/team/` 目录中的所有设计和开发规范文档，以及 `context/experience/` 中的编写经验。

## 执行步骤

### 第一步：获取 Issue 信息
1. 从参数中解析 `owner/repo` 和 `issueNumber`（纯数字默认为 `opensourceways/backlog`）
2. 使用 `gh issue view <issueNumber> --repo <owner/repo> --json title,body,labels,assignees,state,comments` 获取完整信息
3. 解析 issueId、标题、需求背景、需求价值、需求详情、负责人等

### 第二步：判断当前阶段
检查 `opensourceways/issue_docs/{issueId}/` 下已有文档，确定当前处于哪个阶段：

| 检查项 | 阶段判断 |
|--------|---------|
| 无 `Requirement Analysis/` 目录 | → 从**需求分析**开始 |
| 有需求分析但无架构设计，且标签含 `need_security`/`need_design` | → 进入**架构设计** |
| 有架构设计但无测试策略，且标签含 `need_itest` | → 进入**测试策略** |
| 所有标签对应文档已完成 | → 提示可进入开发或编写**变更计划** |

向用户确认："当前处于 [xxx] 阶段，是否开始编写？"
- 如果只有一个待完成文档，直接开始
- 如果有多个，让用户选择

### 第三步：加载知识上下文
1. 读取 `AGENTS.md` 了解仓库规范
2. 读取对应阶段的模板文件
3. 读取 `context/experience/` 下相关经验文件
4. `ls context/business/` 和 `ls context/team/` 检查是否有相关文件，如有则读取
5. 阅读已有的优秀示例文档了解写作深度

### 第四步：创建目录和编写文档

根据阶段执行对应操作：

---

#### 阶段 A：需求分析说明书

**创建目录**：
```
opensourceways/issue_docs/{issueId}/
├── Requirement Analysis/
│   └── #{issueId} Requirement Analysis Specification.md
└── Docs/
```
**注意**：本步骤只创建需求分析目录和 Docs 目录，其他目录在后续阶段按需创建。

**写作原则：只做简要分析，不做具体设计。文字精简。**

填写内容：
1. **基础信息**：需求链接、名称、责任人
2. **需求场景说明**：简要描述（2-3 句话），明确范围边界
3. **需求验收标准**：3-5 条可量化标准，每条一句话
4. **需求设计与分解**：
   - 核心逻辑方案：简述实现思路（3-5 句话），具体设计留给架构设计
   - 任务清单：**Task 2-4 个**，合并相关性强的工作，工作量紧凑
5. **需求相关性分析**：逐项勾选，勾选项写一句话原因
6. **价值识别与业务评估**：给出 Accept/Reject/Pending 结论

---

#### 阶段 B：架构设计说明书

**前置条件**：需求分析已完成，标签含 `need_security` 或 `need_design`

**创建目录**：`opensourceways/issue_docs/{issueId}/Architecture Desgin/`

**写作内容**：
1. 基础信息（需求链接、名称、责任人、设计目标）
2. 功能设计（2.1-2.6）：架构图、数据流图、组件职责与接口、UX设计、SOD设计、功能TASK清单
3. 非功能设计：
   - `need_security` 时：**必须填写** 3.1 安全与隐私设计（威胁分析 + 安全设计实现 + 安全任务分解）
   - 3.2-3.4 可靠性/可服务性/性能为可选
4. 不涉及的章节保留结构，标注"不涉及，原因：xxx"

---

#### 阶段 C：测试策略设计说明书

**前置条件**：需求分析已完成，标签含 `need_itest`

**创建目录**：`opensourceways/issue_docs/{issueId}/Test/`

**写作内容**：
1. 复制模板为 `#{issueId} Test Strategy.md`
2. 基于标签和架构设计填写测试维度、专项验证设计
3. 同时创建 `#{issueId} Test Report.md`（模板占位）

---

#### 阶段 D：变更计划说明书

**创建目录**：`opensourceways/issue_docs/{issueId}/Release/`

**写作内容**：
1. 复制模板为 `#{issueId} xx Change Plan Specification.md`
2. 填写执行步骤、验证方式、回滚方案

---

### 第五步：提示下一步
文档编写完成后，检查还有哪些标签对应的文档未完成：
- 有待完成文档："[当前文档]已完成。根据标签结果，还需要完成：[xxx]。是否继续？"
- 全部完成："所有设计文档已完成，可以进入开发阶段。"

### 第六步：经验沉淀【必选步骤，不可跳过】

1. **回顾本次编写过程**，从以下维度提炼经验：
   - 本次需求类型有什么特殊之处？
   - 相关性分析中是否有容易误判的地方？
   - 任务拆解粒度是否合适？
   - 模板中哪些部分有困难或歧义？

2. **更新 `context/experience/` 对应文件**（按阶段追加）：
   - 需求分析 → `context/experience/需求分析说明书编写经验.md`
   - 架构设计 → `context/experience/架构设计说明书编写经验.md`
   - 测试策略 → `context/experience/测试策略编写经验.md`（首次时创建）
   - 变更计划 → `context/experience/变更计划编写经验.md`（首次时创建）

3. **Skill 改进检测【必须执行】**：如发现改进点，主动询问用户是否更新 skill。不要自行修改。

### 第七步：输出总结
1. 创建/更新的文件清单
2. 需求相关性分析的标签结论（需求分析阶段）
3. 本次沉淀的经验要点
4. Skill 改进建议（如有）

## 关键规范
- **文件命名**：`#{issueId}` 开头，不是 `#1`
- **目录拼写**：`Architecture Desgin` 保持历史拼写
- **保留模板结构**：所有 `>` 引导提示和勾选项列表必须保留，不涉及的章节标注原因而非删除
- **需求分析精简**：只做简要分析，Task 2-4 个，不做具体设计
- **架构设计简要**：重点在设计思路和决策理由
- **`need_security`**：安全设计章节（3.1）为必填
- **经验只写到 `context/experience/`**：不在 issue_docs 下创建经验文件
- **按需创建目录**：每个阶段只创建当前阶段的目录，不预创建后续阶段目录
