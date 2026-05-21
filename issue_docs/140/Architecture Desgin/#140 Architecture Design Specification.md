# #1 使用Trivy扫描社区代码仓库并创建漏洞Issue 架构设计说明书

---

## 1. 基础信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/140
* **需求名称**: 使用Trivy工具定时扫描社区代码仓库并自动创建漏洞Issue
* **开发责任人**: **yangwei999**
* **设计目标**: 引入 Trivy 开源工具替代商用漏洞扫描服务，通过定时任务直接扫描社区代码仓库，将扫描结果（CVE漏洞）转换为平台Issue，实现全流程自动化，消除误报率高、无优化反馈通道等痛点。

---

## 2. 功能设计

### 2.1 架构图

**设计说明:** 本功能在现有 cve-manager-ng 架构中新增 `LocalTrivyService` 模块，作为独立的扫描触发层，复用已有的 `IssueService` 应用层、`IssueHandler` 多社区适配层及平台 API 客户端，不改变现有系统拓扑。

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#4caf50',
    'primaryBorderColor': '#2e7d32',
    'primaryTextColor': '#ffffff',
    'fontSize': '14px'
  }
}}%%
graph TB
    subgraph "调度层"
        Cron["⏱️ Cron Job\n定时调度器"]
    end

    subgraph "扫描层 issue/local_trivy.go"
        LTS["LocalTrivyService\nCreateIssueByLocalTrivy()"]
        UpdateDB["updateDB()\n下载/更新漏洞DB"]
        ScanRepo["scanResult()\n执行Trivy扫描"]
        HandleResult["handleScanResults()\n处理扫描结果"]
    end

    subgraph "Trivy 工具"
        TrivyBin["🔍 trivy CLI\n本地二进制"]
        TrivyDB["📦 漏洞数据库\n本地Cache"]
    end

    subgraph "应用层 issue/app"
        IS["IssueService\nHandleCveFromTrivy()\nCloseIssue()"]
    end

    subgraph "适配层 issue/app/{org}"
        IH["IssueHandler\nCreateIssue() / UpdateIssue()\n各社区实现"]
    end

    subgraph "基础设施层"
        DB["💾 PostgreSQL\nIssue 持久化"]
        GitCode["GitCode API"]
        Gitee["Gitee API"]
        GitHub["GitHub API"]
    end

    subgraph "外部代码仓库"
        Repos["📁 社区代码仓库\n(Orgs + Infra)"]
    end

    Cron -->|"触发"| LTS
    LTS --> UpdateDB
    LTS --> ScanRepo
    UpdateDB -->|"trivy image --download-db-only"| TrivyBin
    TrivyBin <-->|"读写"| TrivyDB
    ScanRepo -->|"trivy repo --skip-db-update"| TrivyBin
    TrivyBin -->|"HTTPS + Token"| Repos
    ScanRepo --> HandleResult
    HandleResult -->|"HandleCveFromTrivy()"| IS
    HandleResult -->|"CloseIssue()"| IS
    IS --> IH
    IH --> DB
    IH --> GitCode
    IH --> Gitee
    IH --> GitHub
```

### 2.2 数据流图

**设计说明:** 描述从代码仓库到漏洞 Issue 的完整数据生命周期，以及去重与关闭旧 Issue 的分支逻辑。

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#1976d2',
    'primaryBorderColor': '#0d47a1',
    'primaryTextColor': '#ffffff',
    'fontSize': '14px'
  }
}}%%
graph LR
    subgraph "数据源"
        R["📁 代码仓库\n源代码 & 依赖清单"]
        VDB["📦 Trivy漏洞DB\n(本地Cache)"]
    end

    subgraph "扫描处理"
        Scan["Trivy 扫描\nSBOM分析 + 漏洞匹配"]
        Parse["JSON结果解析\nCveScanResults"]
        Filter["漏洞过滤\n- 排除Dockerfile\n- 仅处理CVE编号\n- 仅处理直接依赖"]
    end

    subgraph "Issue 处理"
        Dedup["去重查询\nissueRepo.Find()\nCVE + 包名 + 仓库"]
        Create["创建 Issue\nhandler.CreateIssue()"]
        Update["更新 Issue\nhandler.UpdateIssue()"]
        Close["关闭 Issue\n本次未扫描到的CVE"]
    end

    subgraph "持久化 & 输出"
        PG["💾 PostgreSQL\nissue 表"]
        Platform["代码平台\nIssue 列表"]
    end

    R -->|"HTTPS克隆"| Scan
    VDB -->|"本地读取"| Scan
    Scan -->|"JSON stdout"| Parse
    Parse --> Filter
    Filter -->|"Vulnerability{}"| Dedup
    Dedup -->|"不存在"| Create
    Dedup -->|"已存在 & 有变更"| Update
    Filter -->|"activeCves 集合"| Close
    Create --> PG
    Update --> PG
    Close --> PG
    Create --> Platform
    Update --> Platform
    Close --> Platform
```

### 2.3 组件职责与接口

**设计说明:** 新增 `LocalTrivyService`，复用并扩展已有接口，无对外暴露的新 HTTP API。

#### 2.3.1 新增组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `LocalTrivyService` | `issue/local_trivy.go` | 调度入口，遍历 Orgs/Infra 配置，协调扫描与 Issue 处理 |
| `localTrivyService.updateDB()` | `issue/local_trivy.go` | 调用 `trivy image --download-db-only` 更新本地漏洞数据库 |
| `localTrivyService.scanResult()` | `issue/local_trivy.go` | 调用 `trivy repo` 扫描单个仓库，返回 `CveScanResults` |
| `localTrivyService.handleScanResults()` | `issue/local_trivy.go` | 过滤漏洞、驱动 Issue 创建/关闭 |
| `LocalTrivyOrg.reposOfOrg()` | `issue/config.go` | 获取组织仓库列表（静态配置或平台 API 动态拉取） |
| `LocalTrivyOrg.repoUrl()` | `issue/config.go` | 拼接带 Token 认证的 HTTPS 仓库 URL |

#### 2.3.2 复用组件（已有，无需修改）

| 组件 | 接口 / 方法 | 复用点 |
|------|-------------|--------|
| `IssueService` | `HandleCveFromTrivy(CmdToHandleCveFromTrivy)` | 接收 Trivy 漏洞命令，驱动 Issue 创建/更新 |
| `IssueService` | `CloseIssue(org, repo string, cves sets.String)` | 关闭本次扫描中未出现的旧 CVE Issue |
| `IssueHandler` | `CreateIssue() / UpdateIssue()` | 各社区平台适配（Gitee/GitCode/GitHub） |
| `triggerdomain.GetOrgAllRepos()` | - | 分页拉取组织下所有仓库 |
| `utils.RunCmd()` | - | 执行 Trivy CLI 命令，捕获 stdout/stderr |

#### 2.3.3 关键数据结构

```
LocalTrivy (配置)
├── Orgs  []LocalTrivyOrg    # 社区业务组织
└── Infra []LocalTrivyOrg    # 基础设施组织

LocalTrivyOrg
├── Name         string      # 组织名称
├── Token        string      # 访问凭证（运行时从环境变量读取）
├── TokenName    string      # 环境变量名
├── Repos        []string    # 指定扫描仓库（为空则全量）
└── ExcludeRepos []string    # 排除仓库列表

CveScanResults
└── Results []Result
        ├── Target          string         # 扫描目标（文件/镜像）
        ├── Packages        []Package      # 依赖包列表
        └── Vulnerabilities []Vulnerability
                ├── VulnerabilityID  string          # CVE编号
                ├── PkgName          string          # 包名
                ├── InstalledVersion string          # 当前版本
                ├── FixedVersion     string          # 修复版本
                ├── CVSS             map[string]CVSS # 评分信息
                ├── Severity         string          # 严重程度
                └── PublishedDate    string          # 发布时间
```

#### 2.3.4 Trivy CLI 调用参数说明

**更新漏洞数据库：**
```
trivy image --cache-dir cache --download-db-only
```

**扫描代码仓库：**
```
trivy repo \
  --quiet \
  -f json \
  --skip-db-update \
  --scanners vuln \
  --cache-dir cache \
  --pkg-relationships direct \
  <repo_url>
```

| 参数 | 说明 |
|------|------|
| `--skip-db-update` | 扫描时不更新 DB，与 `updateDB()` 分离，避免每次扫描重复下载 |
| `--scanners vuln` | 仅启用漏洞扫描，关闭 secret/misconfig 等扫描器，降低误报 |
| `--pkg-relationships direct` | 仅扫描直接依赖，过滤间接依赖噪音 |
| `-f json` | 结构化输出，便于程序解析 |

### 2.4 UX设计

**设计说明:** 本需求为后台自动化任务，无用户界面交互。Issue 内容本身即为唯一输出形态，其可读性和准确性即用户体验。以下规范约束 Issue 的输出格式：

- **Issue 标题格式**：`[CVE-YYYY-XXXXX] <包名> <版本> 存在漏洞`
- **Issue 正文**：包含 CVE 编号、严重等级、CVSS 评分、受影响版本、修复版本、来源仓库、发布时间、NVD 链接
- **Issue 标签**：自动打 `CVE`、严重等级标签（如 `Critical`/`High`/`Medium`/`Low`）
- **重复抑制**：同一 CVE + 包名组合不重复创建 Issue，已修复时自动关闭

### 2.5 SOD设计

**设计说明:** 不涉及权限模型变更。Token 凭证通过 `LocalTrivyOrg.TokenName` 指定环境变量名称，运行时由 `usernameOfToken()` 从环境变量读取，不存储于配置文件或数据库。权限边界：Trivy 扫描使用只读 Token（仅需仓库读权限）；Issue 创建使用具有 Issue 写权限的机器人账号 Token，两者独立配置，互不影响。

### 2.6 功能设计分解TASK清单

| 任务 ID | 可服务性任务描述 | 责任人        |
|---------|----------------|------------|
| TASK1 | 完成 `LocalTrivy` / `LocalTrivyOrg` 配置结构定义及 `repoUrl()` / `reposOfOrg()` 方法实现 | yangwei999 |
| TASK2 | 实现 `updateDB()` 漏洞数据库更新逻辑 | yangwei999     |
| TASK3 | 实现 `scanResult()` 扫描逻辑及 `CveScanResults` / `Vulnerability` 等数据结构解析 | yangwei999     |
| TASK4 | 实现 `handleScanResults()` 漏洞过滤、`activeCves` 收集、`HandleCveFromTrivy` / `CloseIssue` 调用 | yangwei999     |
| TASK5 | 实现 `IssueService.CloseIssue()` 方法，根据 `activeCves` 差集关闭已修复的 Issue | yangwei999    |
| TASK6 | 接入 Cron Job 调度，配置定时触发周期 | yangwei999     |
| TASK7 | 编写单元测试（覆盖率 ≥ 80%）及集成测试 | yangwei999     |

---

## 3. 非功能设计

### 3.1 安全与隐私设计评估和设计

> 需求判定含 `need_security` 标签，本章节为必填项。

#### 3.1.1 威胁分析 (Threat Modeling)

**设计说明:** 基于 STRIDE 模型，对本功能涉及的数据流和信任边界进行威胁分析。系统存在两类信任边界：内部服务边界（cve-manager-ng 进程内）和外部边界（代码平台 API、Trivy 漏洞数据库）。

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e91e63',
    'primaryBorderColor': '#c2185b',
    'primaryTextColor': '#ffffff',
    'fontSize': '14px'
  }
}}%%
graph TB
    subgraph "信任边界1: cve-manager-ng 内部"
        Config["⚙️ LocalTrivy 配置\n(TokenName 环境变量)"]
        LTS["LocalTrivyService"]
        IS["IssueService"]
        IH["IssueHandler"]
        RepoDB["issueRepo\nPostgreSQL"]
    end

    subgraph "信任边界2: 本地文件系统"
        Cache["📦 Trivy Cache\n漏洞DB + 扫描缓存"]
        TrivyBin["🔍 trivy 二进制"]
    end

    subgraph "信任边界3: 外部网络"
        CodePlatform["GitCode / Gitee / GitHub\n代码仓库 & Issue API"]
        TrivyDBRemote["ghcr.io\nTrivy漏洞数据库镜像"]
    end

    Config -->|"环境变量读取 Token"| LTS
    LTS -->|"exec.Command()"| TrivyBin
    TrivyBin <-->|"读写"| Cache
    TrivyBin -->|"HTTPS + Token\n跨信任边界"| CodePlatform
    TrivyBin -->|"HTTPS Pull\n跨信任边界"| TrivyDBRemote
    LTS --> IS
    IS --> IH
    IH -->|"HTTPS + Token\n跨信任边界"| CodePlatform
    IH --> RepoDB
```

**威胁分析表：**

| 威胁类别 | 攻击场景描述 | 风险等级 | 对应减缓措施 |
|---------|------------|---------|------------|
| **信息泄露 (Information Disclosure)** | Token 明文写入配置文件或打印到日志，导致凭证泄露 | 高 | Token 仅通过环境变量注入（`TokenName` 指定变量名）；日志输出屏蔽 Token 字段；禁止 Token 写入持久化存储 |
| **信息泄露 (Information Disclosure)** | Trivy Cache 目录权限过松，其他进程读取漏洞 DB 或扫描结果 | 中 | 限制 `cache/` 目录权限为进程所有者只读（chmod 700）；容器部署时挂载为私有 Volume |
| **篡改 (Tampering)** | 供应链攻击：Trivy 二进制被替换或漏洞 DB 被投毒，导致扫描结果失实 | 高 | 通过包管理器（官方渠道）安装 Trivy，并校验 SHA256；漏洞 DB 来源限定为官方 `ghcr.io/aquasecurity/trivy-db`；镜像签名验证（Cosign） |
| **篡改 (Tampering)** | `utils.RunCmd()` 执行时，`repoUrl` 中含有特殊字符导致命令注入 | 高 | `repoUrl` 通过 `go-gitcode` SDK 生成，不拼接用户输入；`exec.Command()` 使用参数列表（非 shell 字符串），天然防注入 |
| **拒绝服务 (Denial of Service)** | 扫描大型仓库时 Trivy 占用大量 CPU/内存，影响主服务 | 中 | 为 Trivy 子进程设置资源限制（cgroup/ulimit）；串行扫描仓库，避免并发放大资源消耗 |
| **权限提升 (Elevation of Privilege)** | 扫描用 Token 权限过大，具有 Push/Admin 权限，被利用写入恶意代码 | 高 | 扫描 Token 仅授予仓库读（read-only）权限；Issue 写入使用独立机器人 Token，两类凭证分离管理 |
| **否认 (Repudiation)** | 扫描任务执行情况无法追溯，Issue 创建/关闭原因不明 | 低 | 每次扫描记录结构化日志（触发时间、组织、仓库、CVE 数量、操作结果）；日志含足够的 4W 信息 |

#### 3.1.2 安全设计实现 (Security Mechanisms)

**凭证管理：**
- 代码仓库访问 Token 和 Issue 写入 Token **严禁硬编码**，均通过 `LocalTrivyOrg.TokenName` 指定的环境变量名在运行时读取。
- 部署时通过 Kubernetes Secret 或等价密钥管理系统注入环境变量，不在 ConfigMap 或镜像中明文存储。
- 建议 Token 设置有效期并定期轮转（Rotation），轮转时仅需更新 Secret，无需重新部署应用。

**供应链安全：**
- Trivy 二进制通过官方发布渠道（`aquasecurity/trivy` GitHub Release）获取，集成到 Dockerfile 时验证 SHA256。
- 漏洞数据库更新来源固定为 `ghcr.io/aquasecurity/trivy-db`，不允许自定义镜像源（除非通过官方镜像机制）。
- `go.mod` 中 `go-gitcode` 等直接依赖须经过版本锁定，不使用浮动版本。

**命令注入防御：**
- `utils.RunCmd()` 使用 `exec.Command(name, args...)` 形式，参数列表与命令名分离，操作系统不经过 shell 解析，不存在命令注入风险。
- `repoUrl` 由 SDK 方法生成（含 URL 编码），不直接拼接用户输入。

**日志脱敏：**
- `logrus` 日志输出时，包含 Token 的 URL（`https://[user]:[token]@...`）须在记录前脱敏，替换为 `https://***:***@...`。
- 扫描错误日志仅记录仓库名和错误类型，不记录完整 URL。

**运行时隔离：**
- 容器以非 Root 用户运行（`USER nonroot`）。
- `cache/` 目录挂载为 `emptyDir` 或临时 PVC，不与主应用共享文件系统。

**数据传输安全：**
- 所有外部通信（代码平台 API、漏洞 DB 下载）均使用 TLS 1.2+，不支持 HTTP 降级。

#### 3.1.3 安全任务分解 (Security Task Breakdown)

| 任务 ID | 安全任务描述 | 责任人 |
|---------|------------|--------|
| SEC-TASK1 | 实现 `usernameOfToken()` 从环境变量读取 Token，确保不从配置文件读取明文；添加 Token 为空时的启动校验 | yangwei999 |
| SEC-TASK2 | 在 `repoUrl()` 生成带 Token 的 URL 后，确保此 URL 不被打印到任何日志；实现日志脱敏工具函数 | yangwei999 |
| SEC-TASK3 | 更新 Dockerfile：固定 Trivy 版本，校验 SHA256；以非 Root 用户运行容器 | yangwei999 |
| SEC-TASK4 | 编写安全测试：验证空 Token、无效 Token、超大仓库等异常场景的错误处理边界 | yangwei999 |

---

### 3.2 可靠性与韧性设计评估和设计

**设计说明:** 本功能为定时批处理任务，非在线服务，无 SLA 强约束。以下设计保证单次失败不影响整体：

- **单仓库隔离失败**：`createByOrg()` 对每个仓库的 `scanResult()` 和 `handleScanResults()` 单独 `try-catch`（Go 中为 `error` 检查），单仓库扫描失败只记录错误日志，继续处理下一个仓库，不中断整体任务。
- **DB 更新失败容错**：`updateDB()` 失败仅记录错误日志，不阻断后续扫描（使用上次更新的本地缓存继续工作）。
- **Issue 幂等性**：`HandleCveFromTrivy()` 在写入前查询已有 Issue（按 CVE + 包名 + 仓库），避免重复创建，支持任务重跑。
- **平台 API 失败重试**：Issue 创建/更新调用平台 API 失败时，由 `IssueService` 层记录失败状态到 DB，通过 `RecreateIssue()` 定时重试，不依赖本次扫描任务重跑。

| 任务 ID | 可靠性与韧性任务描述 | 责任人 |
|---------|------------------|--------|
| REL-TASK1 | 确认 `createByOrg()` 对单仓库错误的隔离逻辑，添加完整的 `continue` 处理（已有，验证覆盖完整性） | yangwei999 |
| REL-TASK2 | 为 Trivy 子进程设置执行超时（`context.WithTimeout`），防止单仓库扫描无限阻塞 | yangwei999 |

---

### 3.3 可服务性与可观测性评估和设计

**设计说明:** 本功能为后台批处理，观测重点为任务执行结果的可追溯性。

- **结构化日志**：每次扫描记录 `orgName`、`repo`、`CVE数量`、`操作类型`（created/skipped/closed）、`耗时`，使用 `logrus` 结构化字段输出。
- **错误分类**：区分可重试错误（网络超时、API 限流）和不可重试错误（Token 无效、仓库不存在），日志中标注错误类型。
- **扫描摘要**：每次全量扫描结束后，输出 Summary 日志：`扫描仓库总数 / 成功数 / 失败数 / 新建Issue数 / 关闭Issue数`。

| 任务 ID | 可服务性任务描述 | 责任人 |
|---------|----------------|--------|
| OBS-TASK1 | 在 `CreateIssueByLocalTrivy()` 入口和出口添加结构化日志，记录触发时间和扫描摘要统计 | yangwei999 |
| OBS-TASK2 | 区分 `scanResult()` 的错误类型（网络/超时/解析错误），在日志中标注，便于排查 | yangwei999 |

---

### 3.4 性能与伸缩性评估和设计

**设计说明:** 本功能为串行批处理，当接入社区和仓库数量增多时，单次扫描耗时线性增长。当前阶段采用串行方案，后续可按需演进。

- **当前方案（串行）**：`createByOrg()` 串行遍历仓库，Trivy 扫描 CPU 密集，串行可避免资源争抢，保护主服务稳定性。适用于仓库数量 < 100 的场景。
- **扩展方向（按需）**：当仓库数量增大导致单次扫描窗口超出调度间隔时，可引入有界并发（`semaphore`），控制最大并发扫描数（如 3），在资源消耗和速度间取得平衡。无需现在实现。
- **Trivy Cache 复用**：`--cache-dir cache` 参数使多次扫描复用本地漏洞 DB 缓存，避免重复网络下载，是主要性能优化点。

| 任务 ID | 性能任务描述 | 责任人 |
|---------|------------|--------|
| PERF-TASK1 | 确认 `cache/` 目录在 Pod 重启后可持久化（PVC 挂载），避免每次 Pod 重建后重新下载完整漏洞 DB | yangwei999 |

---
