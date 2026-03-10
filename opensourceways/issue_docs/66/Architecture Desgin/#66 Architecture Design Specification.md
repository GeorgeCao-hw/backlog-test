# #66 cve-manager支持riscv架构update发布 架构设计说明书

---

## 1. 基础信息

* **需求链接**: https://github.com/opensourceways/backlog/issues/66
* **需求名称**: cve-manager支持riscv架构update发布
* **开发责任人**: yangwei999
* **设计目标**: 新增 `POST /releaseMultiArch` 接口，传入参数完成全流程自动化发布。

---

## 2. 功能设计

> **说明**：描述系统的组件构成、职责划分及交互逻辑。

### 2.1 架构图

**设计说明/归档：**

本需求在现有 manage 服务分层架构中新增一条调用链路，不改变任何拓扑结构。新增内容用 `[NEW]` 标注，复用内容用 `[REUSE]` 标注：

```
┌─────────────────────────────────────────────────────────────────┐
│                     cve-sa-backend (manage)                     │
│                                                                 │
│  routers/manage/router.go                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  POST /releaseMultiArch  [NEW]                           │   │
│  │  ── managerAuth + managerLimit 中间件 [REUSE] ──          │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                         │
│  controllers/manage/  │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │  ReleaseMultiArch()  [REUSE] 参数解析 → ArchParam{        │   │
│  │                               Arch: split[2], ...}       │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │  调用相同的 handle 函数                  │
│  handles/manage/      │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │          ReleaseMultiArch(param ArchParam)  [REUSE]      │   │
│  │                                                          │   │
│  │  getRpms()          → CSV 下载 + 解析 RPM 包列表          │   │
│  │  checkWhetherReleased() → 幂等检查                        │   │
│  │  DownloadFile()     → OBS 下载 CVRF XML                  │   │
│  │  updateCvrfWithNewArch() → 追加 riscv64 Branch           │   │
│  │  UploadFile()       → OBS 覆盖上传                        │   │
│  │  SyncSA()           → 公告重新发布                        │   │
│  │  uploadUpdateFixed() → 更新 update-fixed 文件             │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │  dao层 [REUSE]                                           │   │
│  │  DefaultSecurityNotice.NoticeForMultiArch()              │   │
│  │  DefaultReleaseMultiArch.Find() / Create()               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

外部依赖（均为现有依赖，无新增）：
  dailybuild 站点  →  CSV 文件（riscv64 RPM 包列表）
  OBS（对象存储）  →  CVRF XML 文件读写
  MySQL 数据库    →  cve_security_notice / cve_release_multi_arch 表
```

### 2.2 数据流图

**设计说明/归档：**

以下描述调用 `POST /releaseMultiArch` 后 `ReleaseMultiArch` 的完整执行流，标注关键函数与数据结构：

```
运维人员
   │  POST /releaseMultiArch
   │  dir=openEuler_24.03_riscv64 & date=... & version=openEuler-24.03-LTS
   ▼
releaseMultiArch() [controller]
   版本/日期/dir 非空，dir 按"_"拆分 → split[2]="riscv64"
   构造 ArchParam{Dir, Arch:"riscv64", Date:[]string, Version}
   │
   ▼
releaseMultiArch(param ArchParam) [handle]
   │
   ├─[Step1] getRpms(param)
   │   ArchParam.CsvOfPackagesUrl()
   │     → "https://dailybuild.../openEuler-24.03-LTS/openEuler_24.03_riscv64/openEuler-24.03-LTS-riscv64.csv"
   │   ArchParam.CsvOfEpolPackagesUrl()
   │     → "https://dailybuild.../EPOL/openEuler_24.03_riscv64/openEuler-24.03-LTS-riscv64.csv"
   │   parseCsv() → map[组件名][]rpm{Name, IsEpol}
   │   若 map 为空 → 返回 error，终止
   │
   ├─[Step2] dao.DefaultSecurityNotice.NoticeForMultiArch(version, components, dates)
   │   查询 cve_security_notice 表
   │   → []CveSecurityNotice
   │
   └─[Step3] 逐条公告循环处理：
       │
       ├─ ContainsProduct(version) 精确过滤（防模糊查询误匹配）
       │
       ├─ checkWhetherReleased(noticeNo, param)
       │   dao.DefaultReleaseMultiArch.Find(
       │     {Arch:"riscv64", SecurityNoticeNo, AffectedProduct}
       │   )
       │   已存在记录 → 跳过（幂等）
       │
       ├─ localutils.DownloadFile(n.PathOfObs())
       │   OBS 路径: "{DownloadCvrf}{year}/cvrf-{noticeNo}.xml"
       │   → []byte（XML 内容）
       │
       ├─ xml.Unmarshal → Cvrf 结构体
       │   Cvrf.ProductTree.OpenEulerBranch[]
       │     Branch{Type:"Package Arch", Name:"aarch64/x86_64", FullProductName[]}
       │
       ├─ updateCvrfWithNewArch(&cvrf, param, packages)
       │   generateFullProductName(version, rpms)
       │     cpe = "cpe:/a:openEuler:openEuler:24.03-LTS"
       │     FullProductName{ProductId, Cpe, IsEpol, FullProductName(rpm包名)}
       │   若已存在 Name="riscv64" Branch → append FullProductName
       │   否则 → 新建 OpenEulerBranch{Type:"Package Arch", Name:"riscv64"}
       │
       ├─ cvrfToXml(&cvrf)
       │   setNamespaceOfXml()  ← 手动补全 XML 命名空间属性
       │   xml.MarshalIndent → []byte
       │
       ├─ localutils.UploadFile(obsPath, bytes.NewReader(updatedXml))
       │   覆盖写回 OBS 原路径
       │
       ├─ SyncSA(n.PathToSyncSA())
       │   解析 CVRF → 数据库事务：
       │     DeleteSecurityByNo + CreateSecurity
       │     DeletePackagesByNo + CreatePackage
       │     DeleteReferencesByNo + CreateReference
       │
       └─ dao.DefaultReleaseMultiArch.Create(CveReleaseMultiArch{
             Arch:             "riscv64",
             AffectedComponent: n.AffectedComponent,
             AffectedProduct:   param.Version,
             SecurityNoticeNo:  n.SecurityNoticeNo,
           })

   uploadUpdateFixed(updatedFilename)
     将本次发布的文件列表写入 OBS update-fixed 文件
   │
   ▼
返回 []string（成功发布的 CVRF 相对路径列表）
```

### 2.3 组件职责与接口

**设计说明/归档：**

#### 2.3.1 变更范围

| 层次 | 文件路径 | 变更类型 | 说明 |
|------|---------|---------|------|
| Router | `routers/manage/router.go` | **新增 1 行** | 注册 `POST /releaseMultiArch` 路由，复用现有中间件 |
| Controller | `controllers/manage/multi_arch.go` | **新增函数** | 新增 `releaseMultiArch()` |
| Handle | `handles/manage/multi_arch.go` | **不修改** | `ReleaseMultiArch(param ArchParam)` 已支持任意 `param.Arch`，直接复用 |
| Handle | `handles/manage/cvrf.go` | **不修改** | `Cvrf`、`OpenEulerBranch`、`FullProductName` 等结构体已定义 |
| DAO | `dao/cve_release_multi_arch.go` | **不修改** | `Find()`、`Create()` 已实现 |
| DAO | `dao/cve_security_notice.go` | **不修改** | `NoticeForMultiArch()` 已实现 |
| Model | `models/cve_release_multi_arch.go` | **不修改** | `CveReleaseMultiArch` 结构体已定义 |

#### 2.3.2 API 规范

**接口**：`POST /cve-security-notice-server/releaseMultiArch`

**鉴权**：`managerAuth`（`username` + `password` 表单字段）

**限流**：`managerLimit`（同一 IP 30 秒内仅允许调用一次）

**请求（Content-Type: application/x-www-form-urlencoded）**：

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `version` | string | 是 | openEuler 版本号 | `openEuler-24.03-LTS` |
| `date` | string | 是 | 日期范围，逗号分隔 | `2025-03-01,2025-03-07` |
| `dir` | string | 是 | dailybuild 构建目录，格式 `{os}_{ver}_{arch}` | `openEuler_24.03_riscv64` |

**CSV URL 拼接规则**（`ArchParam` 方法，代码已实现）：

```
主仓：https://dailybuild.openeuler.openatom.cn/repo.openeuler.org/{version}/{dir}/{version}-riscv64.csv
EPOL：https://dailybuild.openeuler.openatom.cn/repo.openeuler.org/{version}/EPOL/{dir}/{version}-riscv64.csv
```

**OBS 路径规则**（`CveSecurityNotice` 方法，代码已实现）：

```go
// PathOfObs()  用于下载/上传 CVRF XML
// SecurityNoticeNo 格式：openEuler-SA-2025-1001
// split[2] 取年份 "2025"
fmt.Sprintf("%s%s/cvrf-%s.xml", iniconf.Obs.DownloadCvrf, split[2], SecurityNoticeNo)

// PathToSyncSA()  用于 SyncSA 调用
fmt.Sprintf("%s/cvrf-%s.xml", split[2], SecurityNoticeNo)
```

**响应（成功）**：

```json
{
  "success": true,
  "data": [
    "2025/cvrf-openEuler-SA-2025-1001.xml",
    "2025/cvrf-openEuler-SA-2025-1002.xml"
  ]
}
```

**响应（失败/参数错误）**：

```json
{
  "success": false,
  "msg": "param is empty"
}
```

> `data` 为本次成功发布的 CVRF 相对路径列表（即 `PathToSyncSA()` 返回值）；单条公告处理失败时跳过，不计入 `data`，错误写入日志。

#### 2.3.4 CVRF XML 关键结构（代码已定义，无变更）

```
Cvrf
└── ProductTree
    └── OpenEulerBranch[]           ← Branch 列表（每个架构一个 Branch）
        ├── Type = "Package Arch"
        ├── Name = "aarch64"        ← 现有架构
        │   └── FullProductName[]
        ├── Name = "x86_64"         ← 现有架构
        │   └── FullProductName[]
        └── Name = "riscv64"        ← 本需求新追加
            └── FullProductName[]
                ├── ProductID       ← rpm包名去掉末3段（arch.ver.release）
                ├── CPE             ← "cpe:/a:openEuler:openEuler:24.03-LTS"
                ├── EPOL            ← 是否来自 EPOL 仓
                └── (innerXML)      ← 完整 rpm 包名（如 xxx-1.0-1.riscv64.rpm）
```

#### 2.3.5 数据库表（无 DDL 变更）

**`cve_release_multi_arch`** — 发布记录（查询 + 写入）

| 字段 | 说明 | 本需求写入值 |
|------|------|------------|
| `arch` | 架构名 | `riscv64` |
| `security_notice_no` | 公告编号 | 如 `openEuler-SA-2025-1001` |
| `affected_product` | 产品版本 | 如 `openEuler-24.03-LTS` |
| `affected_component` | 影响组件 | 如 `kernel` |
| `created_at` | 创建时间 | 自动填充 |

幂等检查条件：`{arch, security_notice_no, affected_product}` 三字段联合唯一。

### 2.4 UX设计

**设计说明/归档：** 不涉及，原因：本需求为纯后台管理 API，无前端页面或 CLI 交互变更。

### 2.5 SOD设计

**设计说明/归档：** 不涉及，原因：沿用现有 `managerAuth` 单一管理员角色鉴权，不涉及权限模型变更。

### 2.6 功能设计分解TASK清单

**设计说明/归档：**

**任务清单:**

| 任务 ID     | 功能设计任务描述                                                                                    | 责任人      |
|-----------|-----------------------------------------------------------------------------------------------|----------|
| **TASK1** | 确认 dailybuild riscv64 CSV 文件的目录结构与现有架构是否一致，验证 `CsvOfPackagesUrl()` / `CsvOfEpolPackagesUrl()` 拼接结果可正常下载 | yangwei999 |
| **TASK2** | 在 `controllers/manage/multi_arch.go` 中新增 `ReleaseMultiArch()` controller | yangwei999 |
| **TASK3** | 在 `routers/manage/router.go` 中注册 `manager.POST("/releaseRiscvArch", controllers.releaseMultiArch)` | yangwei999 |
| **TASK4** | 编写 controller 单元测试（参照 `multi_arch_test.go`），覆盖参数为空、dir 格式非法、handle 返回错误、正常成功等分支，statement 覆盖率 ≥ 80% | yangwei999 |
| **TASK5** | 端到端联调：使用真实 riscv64 转测数据触发接口，验证 CSV 解析 → CVRF 修改 → OBS 上传 → SyncSA → 数据库写入全链路正确 | yangwei999 |

---

## 3. 非功能设计

### 3.1 安全与隐私设计评估和设计

> 需求判定标签为 `need_design`，未判定 `need_security`，本章节不适用，删除。

---

### 3.2 可靠性与韧性设计评估和设计（可选）

**设计说明/归档：**

以下可靠性机制均已在 `ReleaseMultiArch` 中实现，新接口通过复用自动继承：

**幂等性**：`checkWhetherReleased()` 在处理每条公告前查询 `cve_release_multi_arch` 表，已有 `{arch=riscv64, security_notice_no, affected_product}` 记录则跳过，重复触发不产生副作用。

**单条失败容错**：循环体内任一步骤（OBS 下载/XML 解析/OBS 上传/SyncSA）失败均调用 `multiArchLog()` 记录错误后 `continue`，不中断后续公告处理。

**外部依赖失效处理**（已实现）：

| 依赖 | 失效行为 |
|------|---------|
| dailybuild CSV 均为空 | `getRpms()` 返回空 map，`ReleaseMultiArch` 返回 error，接口返回失败 |
| OBS 下载失败 | `multiArchLog` 记录，`continue` 跳过该公告 |
| XML 解析失败 | `multiArchLog` 记录，`continue` 跳过该公告 |
| OBS 上传失败 | `multiArchLog` 记录，`continue`（不触发 SyncSA，避免发布未更新文件） |
| SyncSA 失败 | `multiArchLog` 记录，`continue`（不写发布记录） |
| 发布记录写入失败 | `multiArchLog` 记录，不影响已发布结果 |
| `uploadUpdateFixed` 失败 | `multiArchLog` 记录，不影响已发布公告 |

---

### 3.3 可服务性与可观测性评估和设计（可选）

**设计说明/归档：**

**日志**：`multiArchLog()` 在各关键步骤失败时输出包含公告编号、操作类型和错误详情的日志，运维人员可按公告编号在日志中定位失败环节。

**接口响应**：`data` 字段返回本次成功发布的 CVRF 相对路径列表，运维人员可直接从响应确认哪些公告已处理，未出现在 `data` 中的公告需查日志排障。

**排障路径**：某公告未在 `data` 中 → 查 `cve-sa-backend` 日志，按 `security_notice_no` 搜索，定位是 CSV 无对应组件、OBS 操作失败还是 SyncSA 异常。

---

### 3.4 性能与伸缩性评估和设计（可选）

**设计说明/归档：** 不涉及，原因：本接口为低频手动触发的管理操作（每次 riscv64 转测后触发一次），单次处理公告数量有限，现有顺序处理模式可满足需求，无高并发或水平扩展需求。

---
