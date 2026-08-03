# project040 Monorepo — AI 应用教学项目集

一个多项目 monorepo，作为一套完整的 AI 应用开发教学项目：Node/React 前端 + NestJS 共用后端，
外加独立的 MCP 项目和 Python RAG 项目。涉及"调用 AI 模型/核心算法"的部分采用
"先完整实现并验证跑通、再注释掉核心代码留给课堂现场实操"的方式组织，周边的 UI、
参数校验、数据库连接等基础设施代码都是直接写完整的。

## 项目总览

| # | 项目 | 位置 | 状态 |
|---|---|---|---|
| — | 示例模板 | `apps/project1-web` / `apps/project2-web` | 完整跑通 |
| 一 | 图片文字解析（OCR，Gemini/Qwen-VL） | `apps/ocr-web` | ✅ 完整实现 |
| 一 | 图片内容识别与分析（Gemini/OpenAI 视觉） | `apps/vision-analysis-web` | ✅ 已验证跑通，AI 调用核心留作课堂实操 |
| 二 | MCP 查询 Excel | `mcp-projects/excel-mcp-server` | ✅ 完整实现（含手写 MCP 连接演示） |
| 三 | RAG · 向量库（Postgres + pgvector） | `python-projects/rag-vector` | ✅ 已验证跑通，embedding 调用核心留作课堂实操 |
| 三 | RAG · 图数据库（Neo4j） | `python-projects/rag-graph` | ✅ 已验证跑通，实体拆分核心留作课堂实操 |

## 目录结构

```
├── apps/                         # Node/React 项目（pnpm workspace）
│   ├── server/                   # 共用后端（NestJS，端口 3040，可用 PORT 环境变量覆盖）
│   │   └── src/modules/
│   │       ├── project1/         # 示例模板
│   │       ├── project2/         # 示例模板
│   │       ├── ocr/              # 项目一：OCR
│   │       └── vision-analysis/  # 项目一：图片内容识别与分析
│   ├── project1-web/             # 示例模板前端（端口 5100）
│   ├── project2-web/             # 示例模板前端（端口 5101）
│   ├── ocr-web/                  # 项目一·OCR 前端（端口 5102）
│   └── vision-analysis-web/      # 项目一·内容识别与分析前端（端口 5103）
├── packages/
│   └── shared/                   # 前后端共享的 TypeScript 类型（@app/shared）
├── mcp-projects/                 # 项目二：MCP（也在 pnpm workspace 里）
│   └── excel-mcp-server/
├── python-projects/               # 项目三：RAG（独立于 pnpm workspace，各自用 venv）
│   ├── rag-vector/                # Postgres + pgvector
│   └── rag-graph/                 # Neo4j
└── pnpm-workspace.yaml
```

## 快速开始：Node/React 部分（示例模板 + 项目一 + MCP）

```bash
# 安装所有 Node 依赖（覆盖 apps/*、packages/*、mcp-projects/*）
pnpm install

# 先构建共享包（首次或修改 packages/shared 后必须执行）
pnpm build:shared

# 分别启动（各开一个终端）
pnpm dev:server   # 共用后端 http://localhost:3040
pnpm dev:p1       # 示例模板1 http://localhost:5100
pnpm dev:p2       # 示例模板2 http://localhost:5101
pnpm dev:ocr      # 项目一·OCR http://localhost:5102
pnpm dev:vision   # 项目一·内容识别与分析 http://localhost:5103
```

开发时前端通过 Vite proxy 把 `/api` 转发到 `http://localhost:3040`，无跨域问题。

> 注：本机 3000、5173、5040、5432、7474、7687 等常用端口已被其他服务占用，
> 因此各项目改用了 3040/510x（Node 服务）、5532（Postgres）、7475/7688（Neo4j）。
> Vite 配置了 `strictPort`——端口被占时直接报错而不是静默换端口。

## 项目二：MCP 查询 Excel

不需要 `pnpm install`（已包含在根目录的 install 里）。详见
[mcp-projects/excel-mcp-server/README.md](mcp-projects/excel-mcp-server/README.md)，
重点是里面的"手写演示" `client-demo.ts`，把 AI 客户端连接 MCP Server 的握手过程完整展开来看：

```bash
pnpm --filter excel-mcp-server demo
```

## 项目三：RAG（Python，独立于 pnpm workspace）

两个分支分别用 Docker 起数据库，各自有独立的 `README.md` 说明环境搭建和后续步骤：

- 向量库分支：[python-projects/rag-vector/README.md](python-projects/rag-vector/README.md)
- 图数据库分支：[python-projects/rag-graph/README.md](python-projects/rag-graph/README.md)

## 新增一个 Node/React 项目（projectN）

1. 后端：在 `apps/server/src/modules/` 下新建 `projectN` 模块（module/controller/service），
   然后在 `app.module.ts` 的 `RouterModule.register` 中追加
   `{ path: 'projectN', module: ProjectNModule }`。
2. 前端：复制 `apps/project1-web` 为 `apps/projectN-web`，改 `package.json` 的 `name`、
   `vite.config.ts` 的端口，接口统一请求 `/api/projectN/...`。
3. 根 `package.json` 中加一条 `dev:pN` 脚本。

## 生产部署建议

各前端独立构建出静态文件，由 Nginx 按域名/路径分别托管；`/api` 统一反向代理到同一个后端进程，
后端内部再按 `/api/projectN` 前缀路由到对应模块。Python RAG 项目和 MCP 项目是独立的教学演示，
不参与这套前后端的生产部署流程。
