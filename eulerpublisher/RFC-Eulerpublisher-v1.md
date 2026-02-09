# [RFC]: EulerPublisher 云镜像自动化发布改进方案 - version1

## 摘要

本提案针对 EulerPublisher 云镜像发布流程中的两大痛点问题，提出了自动化检测更新和统一配置管理的改进方案。通过引入 Jenkins 定时触发机制和 YAML 统一配置文件，实现了云镜像的"零人工介入"自动发布，大幅提升发布效率。

---

## 1. 痛点分析

### 1.1 Jenkins 触发设计缺失

**问题描述**：
- 现有云镜像发布完全依赖人工操作，需要手动监控 `https://repo.openeuler.org/` 仓库是否有新版本发布
- 缺少自动化检测机制，无法及时发现新版本
- 发布存在滞后性，新版本镜像无法第一时间同步到公有云平台

**期望目标**：
- Jenkins 每日定时自动扫描仓库新增版本
- 检测到新版本后自动触发构建和发布流程

---

### 1.2 镜像一键化上传能力不足

**问题描述**：

#### 1.2.1 多云厂商配置分散
- 原有设计要求在**命令行**通过 `-b`（bucket）、`-r`（region）、`-f`（file）等参数逐个指定
- 发布一个版本到 1 个云厂商需执行多次命令，每次手动输入参数
- 缺乏统一配置文件，多次发布时需重复输入相同参数

**示例（旧流程）**：
```bash
# 准备
eulerpublisher cloudimg prepare -v 24.03-LTS-SP2 -a x86_64

# 构建
eulerpublisher cloudimg build -t huawei -v 24.03-LTS-SP2 -a x86_64

# 推送到华为云
eulerpublisher cloudimg push -t huawei -v 24.03-LTS-SP2 -a x86_64 \
  -b openeuler-obs -r cn-north-4 -f openEuler-24.03-LTS-SP2-x86_64-20230802.qcow2
```

#### 1.2.2 镜像文件名手动指定
- 构建脚本生成的文件名包含时间戳（如 `openEuler-24.03-LTS-SP2-x86_64-20230802_010324.qcow2`）
- 用户需先查看 `/tmp/eulerpublisher/cloudimg/data/output/` 目录确定文件名
- 每次 `push` 都要手动填写 `-f` 参数，容易出错

**期望目标**：
- **统一配置文件**管理所有云厂商参数（bucket、region、ak、sk）
- **一键发布**命令支持自动遍历所有云厂商
- **自动检测**最新镜像文件，无需手动指定文件名
---

## 2. 改进方案

### 2.1 Jenkins 定时触发机制

**文件**：`update/container/image/update.py`

**关键函数**：

| 函数名 | 功能 |
|-------|------|
| `get_repo_versions()` | 爬取 repo.openeuler.org 获取所有 `openEuler-*` 目录 |
| `check_virtual_machine_img(version)` | 检查版本是否包含 `virtual_machine_img/` 子目录 |
| `load_published_versions(filepath)` | 从本地文件加载已发布版本列表 |
| `save_published_versions(filepath, versions)` | 保存已发布版本列表到本地文件 |
| `update_config_version(config_file, new_version)` | 修改 YAML 配置文件中的 version 字段 |
| `get_targets(config_file)` | 读取配置文件中的云厂商列表 |
| `publish_cloudimg(config_file, target)` | 调用 `eulerpublisher cloudimg publish` 发布 |

**检测逻辑**：
```python
# 1. 获取 repo 中所有版本
repo_versions = get_repo_versions()  # ["24.03-LTS-SP2", "25.03-LTS", ...]

# 2. 过滤含虚拟机镜像的版本
vm_versions = [v for v in repo_versions if check_virtual_machine_img(v)]

# 3. 加载已发布记录
published = load_published_versions("/tmp/.../published_versions.txt")

# 4. 计算新增版本
new_versions = [v for v in vm_versions if v not in published]

# 5. 发布新版本
for version in new_versions:
    update_config_version(config_file, version)
    for target in get_targets(config_file):
        publish_cloudimg(config_file, target)
    published.add(version)

# 6. 保存记录
save_published_versions(filepath, published)
```

**已发布版本记录文件格式**：
```
# /tmp/eulerpublisher/cloudimg/published_versions.txt
20.03-LTS-SP4
22.03-LTS
22.03-LTS-SP3
22.03-LTS-SP4
24.03-LTS
24.03-LTS-SP1
24.03-LTS-SP2
```

---

### 2.2 统一 YAML 配置文件

#### 2.2.1 配置文件设计

**文件路径**：`config/cloudimg/cloudimg.yaml`

**配置结构**：
```yaml
# openEuler 云镜像发布配置
version: "24.03-LTS-SP2"  # 镜像版本号（自动更新）
arch: "x86_64"             # 架构类型
rpmlist: ""                # 自定义软件包列表（可选）

# 各云厂商推送配置（仅需配置实际使用的云厂商）
targets:
  huawei:
    ak: "your-huaweicloud-ak"
    sk: "your-huaweicloud-sk"
    bucket: "your-obs-bucket"
    region: "cn-north-4"
    
    ...
```

**配置说明**：
- `version`: 当前构建版本号（自动化流程会动态修改此字段）
- `arch`: 目标架构，限定 `x86_64` 或 `aarch64`
- `targets`: 多云厂商配置，每个厂商包含 `ak`、`sk`、`bucket`、`region` 四个字段
- 不需要的云厂商可直接删除对应配置块

#### 2.2.2 CLI 命令改进

**新增 `publish` 命令**（一键发布）：
```bash
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml -t huawei
```

**改进后的分步命令**：
```bash
# 准备基础镜像
eulerpublisher cloudimg prepare -c config/cloudimg/cloudimg.yaml

# 构建云镜像
eulerpublisher cloudimg build -c config/cloudimg/cloudimg.yaml -t huawei

# 推送云镜像（自动检测最新镜像文件）
eulerpublisher cloudimg push -c config/cloudimg/cloudimg.yaml -t huawei
```

**命令对比**：

| 旧命令 | 新命令 | 改进点 |
|-------|-------|--------|
| `-v` `--version` | `-c` `--config` | 版本号从 YAML 读取 |
| `-a` `--arch` | 从 YAML 读取 | 架构从 YAML 读取 |
| `-b` `--bucket` | 从 YAML 读取 | bucket 从 YAML 读取 |
| `-r` `--region` | 从 YAML 读取 | region 从 YAML 读取 |
| `-f` `--file` | **自动检测** | 自动检测 output/ 目录下最新文件 |
| `-p` `--rpmlist` | 从 YAML 读取 | 软件包列表从 YAML 读取 |
| 环境变量 `HUAWEICLOUD_SDK_AK` | YAML `targets.huawei.ak` | 凭证从 YAML 读取 |
| 环境变量 `HUAWEICLOUD_SDK_SK` | YAML `targets.huawei.sk` | 凭证从 YAML 读取 |
---

## 4. 实施路径

### 4.1 已完成工作

- [x] 重写 `update/container/image/build.sh` 自动化脚本
- [x] 重写 `update/container/image/update.py` 版本检测与发布逻辑
- [x] 新建 `config/cloudimg/cloudimg.yaml` 统一配置文件
- [x] 重构 `CloudimgPublisher` 类支持 YAML 配置
- [x] 修改所有 vendor 函数（huawei/alibaba/tencent/aws）从参数接收凭证
- [x] 新增 `cloudimg publish` 一键发布命令
- [x] 实现自动镜像文件检测（`_detect_image` 方法）
- [x] 更新 README.md 文档

### 4.2 待完成工作

- [ ] Jenkins Pipeline 配置
  ```groovy
  rm -rf eulerpublisher
  git clone https://gitcode.com/openeuler/eulerpublisher.git
  cd eulerpublisher   
  bash update/image/build.sh
  ```

---

## 5. 结论

该方案已在 EulerPublisher 项目中完成实施，经过代码审查和语法验证，可直接投入生产环境使用。建议后续配套完成 Jenkins Pipeline 配置、监控告警和凭证加密等辅助工作，进一步提升系统稳定性和安全性。

---

## 附录

### A. 相关链接

- openEuler 官方仓库：https://repo.openeuler.org/
- 华为云 IMS API：https://support.huaweicloud.com/api-ims/
- 阿里云 ECS API：https://help.aliyun.com/product/25365.html
- AWS EC2 API：https://docs.aws.amazon.com/ec2/

### B. 变更记录

| 日期 | 版本 | 作者 | 变更说明 |
|------|------|------|---------|
| 2026-02-06 | v1.0 | sunshuang1866 | 初始版本 |
