# backlog 仓的 k8s self-hosted runner 清单

本目录管 **backlog 仓自己注册的 GitHub Actions self-hosted runner**：

| Runner | label | 跑什么 workflow | PVC | replicas |
|--------|-------|----------------|-----|----------|
| `ai-design-runner` | `self-hosted,ai-design-runner` | `.github/workflows/analyze-requirement.yml`（需求分析，Workflow A） | `ai-design-workspaces` (20Gi RWX) | 1 |
| `ai-develop-runner` | `self-hosted,ai-develop-runner` | `.github/workflows/implement.yml`（对抗实现 + 预览，Workflow B） | `ai-develop-workspaces` (30Gi RWX) | 1 |

## 文件清单

```
deploy/runners/
├── rbac.yaml                ServiceAccount + RoleBinding + Role 定义（preview-deployer）
├── ai-design-runner.yaml    PVC + Deployment
├── ai-develop-runner.yaml   PVC + Deployment
└── README.md                本文件
```

> **Role `preview-deployer` 由本文件 own**：om-datacenter 仓 `deploy/runners/rbac.yaml` 里的
> `ai-dev-runner` / `k8s-deployer` 的 RoleBinding 也引用同 ns 同名 Role —— 修改 Role 权限范围时
> 务必同步两个仓的预期（实际只能由一个文件维护 Role 定义；当前是本仓）。

## 部署 / 重建步骤

```bash
export KUBECONFIG=...    # ai-test ns 有 admin 权限的 kubeconfig

# 1) 创建两个 runner 的 Secret（需要先到 GitHub 拉 RUNNER_TOKEN）
for r in backlog-runner-secrets:ai-design-runner ai-develop-runner-secrets:ai-develop-runner; do
  S=${r%:*}; LABEL=${r#*:}
  TOKEN=$(gh api -X POST repos/opensourceways/backlog/actions/runners/registration-token -q .token)
  kubectl -n ai-test create secret generic "$S" \
    --from-literal=GITHUB_URL=https://github.com/opensourceways/backlog \
    --from-literal=RUNNER_TOKEN="$TOKEN" \
    --dry-run=client -o yaml | kubectl -n ai-test apply -f -
done

# 2) 应用 RBAC + 两个 runner
kubectl apply -f deploy/runners/rbac.yaml
kubectl apply -f deploy/runners/ai-design-runner.yaml
kubectl apply -f deploy/runners/ai-develop-runner.yaml

# 3) 等 runner 注册成功
kubectl -n ai-test logs deploy/ai-design-runner | tail -20
gh api repos/opensourceways/backlog/actions/runners | jq '.runners[] | {name, status, busy}'
```

## 依赖的外部资源

- `ConfigMap runner-bootstrap`（ai-test ns）—— bootstrap.sh 装 kubectl + actions-runner agent。由
  `opensourceways/om-datacenter:deploy/runners/runner-bootstrap.yaml` 维护，**两边 runner 共享**。
- `Secret huawei-swr-image-pull-secret`（ai-test ns）—— 拉镜像凭据。已手工创建，不在 IaC 里。
- 镜像 `ghcr.io/opensourceways-test/om-datacenter:latest` —— 通用 runner 镜像，含 opencode/gh/git/node/python 等。
