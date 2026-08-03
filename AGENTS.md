# AGENTS.md — 给 AI coding agent 看的安装/运行说明

这份文档是写给 **自动执行安装步骤的 AI agent**（比如 OpenAI Codex）看的：目标是让 agent
不需要人在旁边逐句解释，就能照着下面的命令把环境跑起来、验证各个子项目能正常工作。
面向人类读者的完整说明在 [README.md](README.md)，两份文档描述的是同一个仓库，
这份只是把关键信息整理成"可以直接执行的步骤 + 明确的成功判定标准"。

## 在做任何事之前：这是一个"教学留白"项目，不要擅自补全

这个仓库里凡是标着 `TODO(课堂实操)` 并 `raise NotImplementedError(...)` 的函数，
是**故意留空**的教学练习点，不是未完成的бug。文件里紧跟着的
`# ===== 参考实现 =====` 注释块就是验证过能跑通的答案，只是被注释掉了。

**除非用户明确要求"帮我实现 XXX"或"取消注释参考实现"，否则不要主动删掉
`NotImplementedError` 或取消注释参考实现块。** 判定这些是不是"bug"的标准很简单：
搜索 `NotImplementedError("` 或 `TODO(课堂实操)`，凡是匹配到的都是有意为之的留白，
运行到这里报错是**预期行为**，不是环境没装好。

当前的留白点（一共 5 处 `call_model`/`embed_text`/`extract_triples`）：

| 文件 | 函数 |
|---|---|
| `common/embedding.py` | `embed_text()` |
| `common/extraction.py` | `extract_triples()` |
| `02_ai-rag/query_agentic.py` | `call_model()` |
| `05_harness/harness.py` | `call_model()` |
| `06_loop/agent_loop.py` | `call_model()` |
| `07_graph-engineering/nodes.py` | `call_model()` |

如果任务是"验证环境装好了""跑一下测试"这类目的，遇到这些点报
`NotImplementedError` 就是**验证通过**，不需要也不应该去"修复"它。

## 这个仓库大致是什么

8 个编号的教学子项目（`00_crawler` ~ `07_graph-engineering`），共用一套
Docker 基础设施（Postgres+pgvector / Neo4j / pgAdmin）。`01_ai-ocr` 是唯一有
Web 前端的子项目（NestJS + React），其余都是命令行 Python 脚本。完整目录结构见
[README.md](README.md#目录结构)。

## 环境安装（Linux/macOS shell，agent 沙箱环境用这份）

> 如果是在真实 Windows 机器上手动装，直接跑 `powershell -File scripts/setup.ps1`
> 一键完成下面所有步骤（含 winget 自动装 Docker/Node/Python），见 README.md。
> 下面这份是给**没有 winget、大概率是 Linux 容器沙箱**的 agent 环境准备的等价步骤。

### 第 1 步：确认可用的运行时

```bash
python3 --version   # 需要 3.11+
node --version      # 需要 18+（01_ai-ocr 用）
docker --version    # 02/03/04 需要（Postgres+Neo4j），01/05/06/07 不需要
```

如果 `docker` 不可用，跳过第 2 步，直接看下面「Docker 不可用时能测什么」——
不要因为 Docker 装不上就判定整个环境失败，大部分子项目不依赖它。

### 第 2 步：起 Docker 基础设施（02_ai-rag / 03_vector / 04_graph 需要）

```bash
cd docker
docker compose up -d
# 等 Postgres 健康检查通过（首次启动会自动建好 vector 扩展 + documents 表）
docker compose ps   # 确认 training-postgres 是 healthy
cd ..
```

服务地址：Postgres `localhost:5532`（用户 `rag`/密码 `rag_password`/库 `ragdb`），
Neo4j Bolt `localhost:7688`（用户 `neo4j`/密码 `raggraph123`），
pgAdmin `http://localhost:5050`。这些都是**仅供本地/沙箱内部使用的教学默认密码**，
不要把这套 compose 原样跑在能被外部访问的机器上。

### 第 3 步：Python 虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` 是 `00_crawler`/`02_ai-rag`/`03_vector`/`04_graph`/
`05_harness`/`06_loop`/`07_graph-engineering` 这 7 个 Python 子项目共用的一份依赖，
装一次就够。

### 第 4 步：Node 依赖（仅 01_ai-ocr 需要）

```bash
# 优先用 corepack（Node 16.9+ 自带）启用 pnpm；corepack 不可用时退回 npm 全局安装
corepack enable && corepack prepare pnpm@latest --activate || npm install -g pnpm
pnpm install
```

### 第 5 步：环境变量

```bash
cp .env.example .env
```

`GEMINI_API_KEY`/`OPENAI_API_KEY` 默认是空的——涉及"调用 AI 模型"的功能
（embedding、实体抽取、Agentic 查询、01_ai-ocr 的图片解析、05/06/07 的
`call_model`）都需要真实 key 才能跑通，agent 环境里通常没有，属于**预期限制**，
不是安装失败。不需要 AI 调用的部分（爬虫、BM25 查询、图查询、05/06/07 的
`demo_*.py`）不受影响。

## 安装完成后怎么验证（按"需不需要 API key / Docker"分层）

### 不需要 Docker、不需要 API key（最适合验证环境是否装对）

```bash
# 爬虫：纯 HTTP 调用外部 API，不需要数据库/模型
python 00_crawler/crawl.py 3

# 05/06/07 的确定性边界情况演示：用固定假函数代替真实模型调用
python 05_harness/demo_edge_cases.py
python 06_loop/demo_tool_error.py
python 07_graph-engineering/demo_max_revisions.py
```

这四个跑起来没有报错、并且各自生成一个 `trace_visualization.html`
（05/06/07）就说明 Python 环境装对了。

### 需要 Docker、不需要 API key

```bash
# 前提：docker compose up -d 已经跑起来，且 00_crawler/crawl.py 已经跑过一次
python 03_vector/query_bm25.py "阿里巴巴 Qwen"     # 需要先跑过 03_vector/ingest.py 才有数据
python 04_graph/query_graph.py "阿里巴巴"          # 需要先跑过 04_graph/ingest.py 才有数据
```

注意 `ingest.py` 本身依赖 `embed_text()`/`extract_triples()`（留白点），
没有 API key 就没法把新数据导入数据库——如果数据库是空的，
这两个查询会得到"没有找到"这类结果而不是报错，属于正常的空数据表现。

### 需要 Docker 且需要真实 API key（完整闭环）

```bash
python 03_vector/ingest.py       # 需要先在 common/embedding.py 实现 embed_text
python 04_graph/ingest.py        # 需要先在 common/extraction.py 实现 extract_triples
python 02_ai-rag/query_agentic.py "阿里巴巴和英伟达最近有什么相关的AI新闻？"
python 05_harness/main.py
python 06_loop/main.py
python 07_graph-engineering/main.py "RAG（检索增强生成）"
```

这些命令在留白点还是 `NotImplementedError` 时会报错——**这是预期行为**，
不代表环境没装好（见文档开头）。只有明确被要求实现这些函数时才去改代码。

### 01_ai-ocr（Node，不需要 Docker，需要真实 API key 才能真正解析图片）

```bash
pnpm --filter ocr-server build
node 01_ai-ocr/server/dist/main.js &   # 后端 http://localhost:3040
pnpm --filter ocr-web build            # 前端构建产物在 01_ai-ocr/web/dist
```

后端启动成功、打印 `Server is running on http://localhost:3040` 就说明这部分装对了；
真正调用 `/api/ocr/parse` 解析图片需要一个真实的 `GEMINI_API_KEY` 或
`DASHSCOPE_API_KEY`（可以在请求里传，也可以设成环境变量，见
[01_ai-ocr/web/README.md](01_ai-ocr/web/README.md)）。

## 已知环境相关的坑（agent 沙箱里大概率遇不到，但如果遇到了别误判成安装失败）

- 如果 agent 跑在 **Windows** 沙箱里：`.ps1` 脚本必须是带 UTF-8 BOM 的文件才能被
  PowerShell 5.1 正确解析中文，仓库里现有的 `.ps1` 都已经处理过；新增 `.ps1`
  文件时如果要写中文，参考 `scripts/` 目录下现有文件的做法补 BOM，不要用
  PowerShell 的 `Get-Content` 读取内容再写回（会在 cp932 locale 下把中文读成乱码），
  改用 Python 的 `open(f, encoding='utf-8')` 读 + `open(f, 'w', encoding='utf-8-sig')` 写。
- Docker 容器名前缀是 `training-`（`training-postgres`/`training-neo4j`/`training-pgadmin`），
  如果沙箱里同时跑着其他项目的容器，用这个前缀区分，不要按端口号或裸容器名笼统操作。
- `pip install -r requirements.txt` 如果因为网络问题重试，不代表依赖列表有问题——
  这份 `requirements.txt` 本身内容很少，都是常规包（psycopg2-binary/neo4j/requests/
  rank-bm25/numpy/python-dotenv）。
