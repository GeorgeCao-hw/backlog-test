# #1 SEO优化功能 架构设计说明书 (Architecture Design Document)

---

## 1. 基础信息

- **需求链接**: https://github.com/opensourceways/backlog/issues/209
- **需求名称**: MindSpore社区GEO优化
- **开发责任人**: zjwmiao
- **设计目标**: 通过 Nuxt 模块和 Vite 插件在构建阶段自动生成并注入 SEO 配置（sitemap.xml、TDK meta 标签、JSON-LD 结构化数据），无需运行时动态处理。

---

## 2. 功能设计

> **说明**：描述系统的组件构成、职责划分及交互逻辑。

### 2.1 架构图

> 不涉及复杂组件交互，为纯构建阶段静态生成功能。

```
┌─────────────────────────────────────────────────────────────────┐
│                        构建流程 (Build Pipeline)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ lastModifiedPlugin│────▶│ last-modified.json│                 │
│  │ (Vite 插件)        │     │ (git提交时间映射)   │                 │
│  └──────────────────┘     └──────────────────┘                 │
│         │                              │                        │
│         │ 分析模块依赖                   │ 读取                    │
│         ▼                              ▼                        │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ 构建产物生成       │────▶│ .output/public/   │                 │
│  │                   │     │ (index.html文件)   │                 │
│  └──────────────────┘     └──────────────────┘                 │
│                                    │                            │
│                                    │ 扫描                        │
│                                    ▼                            │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ generate-sitemap │────▶│ sitemap.xml       │                 │
│  │ (Nuxt Module)     │     │                   │                 │
│  └──────────────────┘     └──────────────────┘                 │
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ auto-set-tdks    │────▶│ HTML meta标签      │                 │
│  │ (路由中间件)       │     │ (title/desc/keywords)│              │
│  └──────────────────┘     └──────────────────┘                 │
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ auto-set-jsonld  │────▶│ JSON-LD script    │                 │
│  │ (路由中间件)       │     │ (结构化数据)        │                 │
│  └──────────────────┘     └──────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

> 不涉及敏感数据流转，仅处理静态文件元数据。

**Sitemap 生成数据流**:

```
Git Repository ──▶ lastModifiedPlugin ──▶ last-modified.json
                                              │
.output/public ──▶ generate-sitemap ────────▶│
                                              ▼
                                          sitemap.xml
```

**TDK/JSONLD 注入数据流**:

```
tdks/*.ts / jsonlds/*.ts ──▶ 路由中间件 ──▶ useSeoMeta/useHead ──▶ HTML head
```

### 2.3 组件职责与接口

| 组件                   | 文件路径                             | 职责                                                                                                         |
| ---------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| **lastModifiedPlugin** | `vite-plugins/lastModifiedPlugin.ts` | Vite 插件，分析模块依赖关系，基于 git log 获取各源文件的最后提交时间，输出 `last-modified.json`              |
| **generate-sitemap**   | `modules/generate-sitemap.ts`        | Nuxt 模块，构建完成后扫描 `.output/public` 下所有 `index.html`，结合 `last-modified.json` 生成 `sitemap.xml` |
| **auto-set-tdks**      | `modules/auto-set-tdks/`             | Nuxt 模块 + 全局路由中间件，预渲染阶段根据路由路径匹配 TDK 配置并注入 meta 标签                              |
| **auto-set-jsonld**    | `modules/auto-set-jsonld/`           | Nuxt 模块 + 全局路由中间件，预渲染阶段根据路由路径匹配 JSONLD 配置并注入 script 标签                         |

**关键实现细节**:

1. **lastModifiedPlugin**:
   - 使用 Vite 的 `buildEnd` hook 分析模块依赖图
   - 通过 `git log -1 --format=%ct <file>` 获取文件最后提交时间戳
   - 输出格式: `{ "pages/index.vue": { lastmod: "2026-04-14", changefreq: "weekly" } }`

2. **generate-sitemap**:
   - 通过 `nuxt.hook('close')` 在构建结束时执行
   - 递归扫描 `.output/public` 目录收集所有 `index.html` 路径
   - 支持 `ignore` 配项排除特定路径（如 `/api/`, `/docs/`）
   - 输出标准 sitemap.xml 格式

3. **auto-set-tdks 中间件**:

   ```ts
   export default defineNuxtRouteMiddleware((to) => {
     if (!import.meta.prerender) return; // 仅预渲染时执行
     const locale = /(?:\/en\/?$|\/en\/)/g.test(to.path) ? 'en' : 'zh';
     const tdkInfo = tdks[locale]?.[to.path];
     useSeoMeta({ title, description, keywords, ogDescription });
   });
   ```

4. **auto-set-jsonld 中间件**:
   ```ts
   export default defineNuxtRouteMiddleware((to) => {
     if (!import.meta.prerender) return;
     const jsonldInfo = jsonlds[locale]?.[to.path];
     useHead({
       script: [
         { type: 'application/ld+json', innerHTML: JSON.stringify(jsonldInfo) },
       ],
     });
   });
   ```

### 2.4 UX设计

> 不涉及用户交互界面变更，仅影响搜索引擎爬虫和页面 HTML head 内容。

### 2.5 SOD设计

> 不涉及权限变更。

### 2.6 功能设计分解TASK清单

| 任务 ID   | 可服务性任务描述                                   | 责任人  |
| --------- | -------------------------------------------------- | ------- |
| **TASK1** | 实现 lastModifiedPlugin Vite 插件分析 git 提交时间 | zjwmiao |
| **TASK2** | 实现 generate-sitemap Nuxt 模块生成 sitemap.xml    | zjwmiao |
| **TASK3** | 使用 agent skill 扫描网站并生成 TDK 配置文件       | zjwmiao |
| **TASK4** | 实现 auto-set-tdks 路由中间件注入 TDK              | zjwmiao |
| **TASK5** | 使用 agent skill 扫描网站并生成 JSONLD 配置文件    | zjwmiao |
| **TASK6** | 实现 auto-set-jsonld 路由中间件注入 JSONLD         | zjwmiao |

---

## 3. 非功能设计

### 3.1 安全与隐私设计评估和设计

> 不涉及安全相关变更，无需填写。

### 3.2 可靠性与韧性设计评估和设计

> 不涉及核心服务变更，无需填写。

### 3.3 可服务性与可观测性评估和设计

> 构建产物可通过检查 sitemap.xml 和 HTML head 内容验证。

**验证方法**:

- 检查 `.output/public/sitemap.xml` 是否包含所有页面路径
- 检查构建产物 HTML 的 `<head>` 是否包含正确的 meta 标签和 JSON-LD script

### 3.4 性能与伸缩性评估和设计

> 所有 SEO 配置在构建阶段生成，无运行时性能影响。

**性能说明**:

- lastModifiedPlugin 在 Vite 构建阶段异步执行，不阻塞构建流程
- 路由中间件仅在预渲染（`import.meta.prerender`）时执行，不影响客户端渲染性能
