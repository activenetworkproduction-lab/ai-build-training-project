# project040 — AI 应用教学项目集

三个教学项目，共用一套 Docker 基础设施（Postgres+pgvector / Neo4j / pgAdmin）：

| # | 项目 | 位置 | 技术栈 |
|---|---|---|---|
| 一 | 图片文字解析（OCR） | `ocr/` | NestJS + React，Gemini/Qwen-VL |
| 二 | RAG 数据管道 | `data-pipeline/` | Python：爬虫 → 向量入库 → 图谱入库 |
| 三 | RAG 统一查询 | `rag-query/` | Python：BM25 / 向量 / 图 / Agentic 四种查询方式 |

涉及"调用 AI 模型"的核心部分（视觉识别、embedding、实体抽取、Agent 决策）采用
**"先完整实现并用真实数据验证跑通，再注释掉核心代码留给课堂现场实操"**的方式组织：
搜索文件里的 `TODO(课堂实操)` 就能找到这些留白点，紧跟着的注释块就是验证通过的参考实现。

## 目录结构

```
├── docker/                       # 项目二三共用的基础设施
│   ├── docker-compose.yml        # Postgres(pgvector) + Neo4j + pgAdmin
│   ├── postgres-init/01-init.sql # 首次启动自动建 vector 扩展 + documents 表
│   └── pgadmin/servers.json      # pgAdmin 预注册的 Postgres 连接
├── scripts/                      # 一键安装 / 一键启动
│   ├── setup.ps1                 # 检测装Docker → 起容器 → 等数据库就绪
│   ├── start-ocr.ps1
│   ├── start-crawler.ps1
│   ├── start-vector-ingest.ps1
│   ├── start-graph-ingest.ps1
│   └── start-rag-query.ps1
├── ocr/                           # 项目一
│   ├── server/                   # NestJS 后端
│   └── web/                      # React 前端
├── common/                       # 项目二三共用的 Python 模块
│   ├── db_postgres.py / db_neo4j.py   # 数据库连接（已完整实现）
│   ├── embedding.py               # 【课堂留白】embedding 手写调用
│   └── extraction.py              # 【课堂留白】实体关系拆分手写调用
├── data-pipeline/                # 项目二：爬虫 → 向量入库 → 图谱入库
│   ├── crawler/crawl.py
│   ├── vector-ingest/ingest.py
│   └── graph-ingest/ingest.py
├── rag-query/                    # 项目三：BM25 / 向量 / 图 / Agentic 四种查询
│   ├── query_bm25.py
│   ├── query_vector.py
│   ├── query_graph.py
│   └── query_agentic.py          # 【课堂留白】Agent 的模型调用
├── data/raw/                      # 爬虫产出（不进版本库，随时可重新生成）
├── requirements.txt               # 所有 Python 组件共用一份依赖
└── .env.example                   # 所有 Python 组件共用一份配置
```

## 快速开始

### 第 1 步：一键搭建基础设施

```powershell
powershell -File scripts/setup.ps1
```

这一步会：检测/安装 Docker → 启动 Postgres(pgvector)、Neo4j、pgAdmin 三个容器 →
Postgres 首次启动时自动建好 `vector` 扩展和 `documents` 表（见
`docker/postgres-init/01-init.sql`，不需要额外手动建库）。完成后打印各个管理
界面的地址和账号密码。

### 第 2 步：装依赖

```powershell
# Node（项目一 OCR）
pnpm install

# Python（项目二三共用一个虚拟环境）
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

### 第 3 步：跑数据管道（项目二），再查询（项目三）

```powershell
powershell -File scripts/start-crawler.ps1         # 抓取维基百科词条到 data/raw/
powershell -File scripts/start-vector-ingest.ps1   # 分段 + embedding，写入 Postgres
powershell -File scripts/start-graph-ingest.ps1    # 拆三元组，写入 Neo4j
powershell -File scripts/start-rag-query.ps1       # 交互式选查询方式
```

> 注意：`vector-ingest` 和 `graph-ingest` 依赖 `common/embedding.py` /
> `common/extraction.py` 里的核心调用（课堂留白，目前是占位报错）。这两步需要
> 先完成对应的课堂实操才能真正跑起来——BM25 查询和图查询不依赖它们，可以直接用。

### 项目一（OCR）单独运行

```powershell
powershell -File scripts/start-ocr.ps1
# 或分开手动跑：
pnpm dev:ocr:server   # 后端 http://localhost:3040
pnpm dev:ocr:web      # 前端 http://localhost:5102
```

## 管理界面

| 服务 | 地址 | 账号 |
|---|---|---|
| pgAdmin | http://localhost:5050 | admin@training-project.com / admin123（已预注册 Postgres 连接，首次连接输入密码 rag_password） |
| Neo4j Browser | http://localhost:7475 | neo4j / raggraph123 |
| Postgres | localhost:5532 | rag / rag_password，数据库 ragdb |

> 本机常用端口 3000/5432/7474/7687 等已被其他服务占用，所以本项目分别改用
> 3040（OCR后端）/5532（Postgres）/7475+7688（Neo4j）/5050（pgAdmin）。

## 项目二：RAG 数据管道（详见 `data-pipeline/README.md`）

三个阶段，一个接一个跑：

1. **爬虫**（`data-pipeline/crawler/crawl.py`）：抓取中文维基百科上"检索增强生成"
   "向量数据库""图数据库""PostgreSQL"等词条正文，作为教学语料
2. **向量入库**（`data-pipeline/vector-ingest/ingest.py`）：按段落切分 → 调用
   embedding 接口 → 存进 Postgres 的 `documents` 表（`VECTOR(768)` 列）
3. **图谱入库**（`data-pipeline/graph-ingest/ingest.py`）：每段文字调用大模型拆成
   `(主体, 关系, 客体)` 三元组 → 用 `MERGE` 写入 Neo4j

## 项目三：RAG 统一查询（详见 `rag-query/README.md`）

同一份数据，四种查询方式，直观对比差异：

| 方式 | 原理 | 擅长 |
|---|---|---|
| BM25 | 关键词匹配 + 词频统计，纯算法不需要模型 | 问题包含明确专有名词 |
| 向量 | embedding 语义相似度（pgvector `<=>`） | 意思相近但没有相同关键词 |
| 图 | Cypher 遍历实体关系 | "A 和 B 是什么关系"这类问题 |
| Agentic | 大模型自己决定调用哪个/哪几个工具，多轮迭代后综合回答 | 复杂问题，一种方式不够时自动换/组合 |

## 常见踩坑记录

- **Gemini 模型名会过期**：`gemini-2.5-flash`、`text-embedding-004` 已对新用户下线，
  本项目统一改用验证可用的 `gemini-3.5-flash`（聊天/视觉）和 `gemini-embedding-001`
  （embedding，用 `outputDimensionality` 截断到 768 维）。
- **pgvector 查询要显式 `::vector` 类型转换**：`INSERT` 有隐式转换能直接存，但
  `SELECT ... embedding <=> %s` 里没有目标列类型，必须写成 `%s::vector`。
- **Neo4j 无向 Cypher 查询会掩盖关系真实方向**：要用 `startNode(r)`/`endNode(r)`，
  不能直接用模式匹配里 a/b 的绑定顺序。
- **pgAdmin 的默认邮箱不能用 `.local` 等保留域名**，会被邮箱格式校验拒绝。
- **本机系统 locale 是日文（cp932）**：带中文字符的 `.ps1` 脚本必须存成带 BOM 的
  UTF-8，否则 PowerShell 5.1 会用 cp932 解码导致语法错误；Python 脚本打印中文
  在某些终端（比如 Git Bash）下也需要设置 `PYTHONUTF8=1`。
