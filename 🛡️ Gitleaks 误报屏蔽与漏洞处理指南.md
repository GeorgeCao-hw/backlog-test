
# 🛡️ Gitleaks 误报屏蔽与漏洞处理指南

在开发过程中，如果 Gitleaks 扫描提示了风险，请首先判断是**误报**还是**真实的密钥泄露**。根据判断结果，按以下指导进行处理。

## 一、 如何屏蔽误报（指纹屏蔽法）

**适用场景**：被识别的信息是 Mock 数据、测试 Token 或不具安全风险的随机字符串。
**核心机制**：通过 `.gitleaksignore` 文件，利用唯一指纹（Fingerprint）精确跳过特定误报。

### 操作步骤：

1. **获取指纹 (Fingerprint)**
在本地或 CI/CD 的扫描日志中，找到报错的具体条目。每个结果都会包含一个 `Fingerprint` 字段。
*例：`418edf165dbb63d6f46993ae8f8818ffd87ea582:cmd/generate/config/rules/jwt.go:jwt:17*`
2. **创建/编辑屏蔽文件**
在项目的**根目录**下创建或打开名为 `.gitleaksignore` 的文件。
3. **添加指纹**
将获取到的指纹直接复制并粘贴到文件中，每个指纹占一行。
```text
# 忽略测试环境的 Mock Token (误报)
418edf165dbb63d6f46993ae8f8818ffd87ea582:cmd/generate/config/rules/jwt.go:jwt:17

# 忽略前端示例代码中的随机 ID
418edf165dbb63d6f46993ae8f8818ffd87ea582:cmd/generate/config/rules/jwt.go:jwt:17

```


4. **提交生效**
将 `.gitleaksignore` 文件提交至仓库。后续扫描将自动跳过这些已记录的“已知误报”。

---

## 二、 发现真实密钥泄露的处理流程

如果被扫描出的内容是**真实的、具有访问权限的秘密**（如阿里云 AccessKey、数据库密码、生产环境 Token 等），**严禁直接屏蔽**。必须按照以下“三步走”方案处理：

### 1. 立即吊销与重置（最重要！）

* **吊销**：立即在服务提供商后台禁用该泄露的密钥。
* **重置**：生成新的密钥，并更新到受保护的配置中心（如 Apollo、Nacos 或环境变量）中。
* *注意：一旦密钥进入过 Git 历史，它就不再安全，必须作废旧密钥。*

### 2. 清理 Git 历史记录

仅仅“删除代码再提交”是不够的，因为密钥仍存在于 Git 的历史版本中。

* **推荐工具**：使用 [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) 或 `git-filter-repo`。
* **命令示例**（使用 BFG）：
```bash
# 彻底从所有提交记录中删除包含该密钥的文件或敏感词
bfg --replace-text passwords.txt my-repo.git

```



### 3. 规范后续存储

* **本地开发**：使用 `.env` 文件存储密钥，并确保 `.env` 已列入 `.gitignore`。
* **生产环境**：使用公司统一的秘密管理系统或 CI/CD 变量功能，严禁将明文密钥写入任何代码文件（包括注释）。

---

> [!WARNING]
> **安全警示**：如果不确定是否为误报，请咨询组织内的信息安全负责人（Security Team），切勿擅自屏蔽。
