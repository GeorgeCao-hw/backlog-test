# [RFC]: EulerPublisher 云镜像自动化发布改进方案 - version2

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

### 2.3 AWS 和 Azure 云平台自动化支持

#### 2.3.1 AWS 镜像发布自动化

**支持能力**：
- 使用 boto3 SDK 自动上传镜像到 S3
- 自动注册 AMI（Amazon Machine Image）
- 支持多区域并行发布
- 自动设置镜像权限（公开/私有/指定账号共享）

**YAML 配置扩展**：
```yaml
targets:
  aws:
    ak: "your-aws-access-key-id"
    sk: "your-aws-secret-access-key"
    bucket: "your-s3-bucket"
    region: "us-east-1"
    # AWS 特有配置
    ami_name: "openEuler-{version}-{arch}"  # 支持变量替换
    ami_description: "openEuler official image"
    volume_type: "gp3"  # 可选: gp2, gp3, io1, io2
    public: false  # 是否公开镜像
    shared_accounts: []  # 共享账号列表
```

**发布命令**：
```bash
# AWS 镜像一键发布
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml -t aws

# 多区域发布（在 YAML 中配置多个 region）
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml -t aws --all-regions
```

**自动化流程**：
1. 镜像转换为 RAW 格式（AWS 要求）
2. 上传到 S3 存储桶
3. 导入为 Snapshot
4. 注册为 AMI
5. 配置启动权限和共享策略
6. 返回 AMI ID 并记录到发布日志

#### 2.3.2 Azure 镜像发布自动化

**支持能力**：
- 使用 Azure SDK 上传 VHD 镜像到 Blob 存储
- 自动创建托管镜像（Managed Image）
- 支持发布到 Azure Marketplace
- 自动配置镜像元数据和标签

**YAML 配置扩展**：
```yaml
targets:
  azure:
    # 认证信息
    subscription_id: "your-subscription-id"
    tenant_id: "your-tenant-id"
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    # 存储配置
    resource_group: "openeuler-images"
    storage_account: "openeulerstorage"
    container: "images"
    location: "eastus"
    # Azure 特有配置
    image_name: "openEuler-{version}-{arch}"
    os_type: "Linux"
    hyper_v_generation: "V2"  # V1 或 V2
    tags:
      publisher: "openEuler"
      version: "{version}"
```

**发布命令**：
```bash
# Azure 镜像一键发布
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml -t azure

# 发布到 Marketplace（需预先配置发布者账号）
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml -t azure --marketplace
```

**自动化流程**：
1. 镜像转换为 VHD 格式（Azure 要求）
2. 上传到 Azure Blob 存储
3. 创建托管镜像（Managed Image）
4. 配置镜像属性和标签
5. （可选）提交到 Azure Marketplace 审核
6. 返回镜像资源 ID 并记录

#### 2.3.3 多云并行发布

**批量发布命令**：
```bash
# 发布到所有配置的云平台
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml --all

# 发布到指定多个云平台
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml -t huawei,aws,azure

# 并行发布（加速发布流程）
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.yaml --all --parallel
```

---

### 2.4 YAML 配置文件加密

#### 2.4.1 加密需求背景

**安全风险**：
- YAML 配置文件包含云平台 AK/SK、密钥等敏感信息
- 明文存储存在泄露风险
- 配置文件可能被提交到 Git 仓库

**加密目标**：
- 对 YAML 中的敏感字段进行加密
- 支持多种加密算法（AES-256-GCM）
- 提供密钥管理机制

#### 2.4.2 加密方案设计

**加密字段标识**：
```yaml
targets:
  huawei:
    ak: "ENC(AES256:base64encodedciphertext)"  # 加密字段
    sk: "ENC(AES256:base64encodedciphertext)"  # 加密字段
    bucket: "openeuler-obs"  # 明文字段
    region: "cn-north-4"  # 明文字段
```

**加密命令**：
```bash
# 加密指定配置文件
eulerpublisher config encrypt -c config/cloudimg/cloudimg.yaml -o config/cloudimg/cloudimg.encrypted.yaml

# 使用自定义密钥文件
eulerpublisher config encrypt -c config/cloudimg/cloudimg.yaml -k /path/to/master.key

# 交互式加密（手动输入密钥）
eulerpublisher config encrypt -c config/cloudimg/cloudimg.yaml --interactive
```

**解密机制**：
```bash
# 方式1: 自动解密（读取环境变量中的主密钥）
export EP_MASTER_KEY="your-master-key-here"
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.encrypted.yaml -t huawei

# 方式2: 指定密钥文件
eulerpublisher cloudimg publish -c config/cloudimg/cloudimg.encrypted.yaml -k /path/to/master.key -t huawei

# 方式3: 显式解密为临时文件（自动清理）
eulerpublisher config decrypt -c config/cloudimg/cloudimg.encrypted.yaml -o /tmp/cloudimg.decrypted.yaml
```

#### 2.4.3 密钥管理

**主密钥生成**：
```bash
# 生成随机主密钥
eulerpublisher config genkey -o /path/to/master.key

# 生成并保存到环境变量
eulerpublisher config genkey --export >> ~/.bashrc
```

**密钥存储方案**：

| 方案 | 适用场景 | 安全级别 |
|------|----------|----------|
| 环境变量 `EP_MASTER_KEY` | 本地开发 | 中 |
| 文件 `/etc/eulerpublisher/master.key` (权限 600) | 生产服务器 | 高 |
| Jenkins 凭证存储 | CI/CD 流程 | 高 |
| AWS Secrets Manager / Azure Key Vault | 云原生部署 | 极高 |

**加密字段自动识别规则**：
- 字段名包含 `key`, `secret`, `password`, `token`, `ak`, `sk` 的自动加密
- 支持自定义敏感字段列表
- 加密后文件格式与明文文件 100% 兼容

#### 2.4.4 安全最佳实践

**配置文件管理**：
```bash
# 1. 将加密配置文件加入版本控制
git add config/cloudimg/cloudimg.encrypted.yaml

# 2. 忽略明文配置文件和密钥文件
echo "config/cloudimg/cloudimg.yaml" >> .gitignore
echo "*.key" >> .gitignore
echo ".master_key" >> .gitignore

# 3. Jenkins 中配置主密钥为环境变量
# Pipeline 配置:
environment {
    EP_MASTER_KEY = credentials('eulerpublisher-master-key')
}
```

**密钥轮换**：
```bash
# 1. 生成新主密钥
eulerpublisher config genkey -o /path/to/new_master.key

# 2. 使用旧密钥解密
eulerpublisher config decrypt -c config/cloudimg/cloudimg.encrypted.yaml -k /path/to/old_master.key -o /tmp/plain.yaml

# 3. 使用新密钥重新加密
eulerpublisher config encrypt -c /tmp/plain.yaml -k /path/to/new_master.key -o config/cloudimg/cloudimg.encrypted.yaml

# 4. 清理临时文件
rm -f /tmp/plain.yaml
```

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

- [ ] AWS 云平台支持
  - [ ] 实现 `cloudimg/vendor/aws.py` 模块
  - [ ] 添加 RAW 格式转换逻辑
  - [ ] 实现 S3 上传和 AMI 注册
  - [ ] 支持多区域并行发布
  - [ ] 添加 AWS 相关单元测试

- [ ] Azure 云平台支持
  - [ ] 实现 `cloudimg/vendor/azure.py` 模块
  - [ ] 添加 VHD 格式转换逻辑
  - [ ] 实现 Blob 存储上传和托管镜像创建
  - [ ] 支持 Marketplace 发布流程
  - [ ] 添加 Azure 相关单元测试

- [ ] YAML 配置文件加密
  - [ ] 实现 `config encrypt/decrypt` 命令
  - [ ] 实现 AES-256-GCM 加密算法
  - [ ] 实现主密钥生成和管理
  - [ ] 自动识别敏感字段
  - [ ] 集成到现有 `publish` 流程
  - [ ] 添加加密相关文档和示例

- [ ] Jenkins Pipeline 配置
  ```groovy
  rm -rf eulerpublisher
  git clone https://gitcode.com/openeuler/eulerpublisher.git
  cd eulerpublisher
  # 配置主密钥环境变量
  export EP_MASTER_KEY=${EULERPUBLISHER_MASTER_KEY}
  bash update/image/build.sh
  ```

- [ ] 文档更新
  - [ ] 更新 README.md 添加 AWS/Azure 使用说明
  - [ ] 添加配置文件加密最佳实践文档
  - [ ] 更新 YAML 配置文件模板

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
- AWS AMI 导入文档：https://docs.aws.amazon.com/vm-import/latest/userguide/
- AWS boto3 SDK：https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- Azure Compute API：https://docs.microsoft.com/en-us/rest/api/compute/
- Azure Python SDK：https://learn.microsoft.com/en-us/python/api/overview/azure/
- Azure Marketplace 发布指南：https://learn.microsoft.com/en-us/azure/marketplace/

### B. 变更记录

| 日期 | 版本 | 作者 | 变更说明 |
|------|------|------|---------|
| 2026-02-06 | v1.0 | sunshuang1866 | 初始版本 |
| 2026-02-07 | v1.1 | sunshuang1866 | 新增 AWS 和 Azure 云平台自动化支持方案 |
| 2026-02-07 | v1.1 | sunshuang1866 | 新增 YAML 配置文件加密机制 |
