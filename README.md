# project040 — AI 应用教学项目集

8 个教学项目（编号 00-07），共用一套 Docker 基础设施（Postgres+pgvector / Neo4j / pgAdmin）。
涉及"调用 AI 模型"的核心部分（视觉识别、embedding、实体抽取、Agent 决策）采用
**"先完整实现并用真实数据验证跑通，再注释掉核心代码留给课堂现场实操"**的方式组织：
搜索文件里的 `TODO(课堂实操)` 就能找到这些留白点，紧跟着的注释块就是验证通过的参考实现。

## 项目总览

| # | 项目 | 位置 | 说明 |
|---|---|---|---|
| 00 | 爬虫 | `00_crawler/` | 共用的数据来源（不算在"7个项目"里），抓 [AI News](https://ai-news.tayoru-kun.com/) 网站的新闻 |
| 01 | AI OCR | `01_ai-ocr/` | 图片文字解析，NestJS + React，Gemini/Qwen-VL |
| 02 | AI RAG | `02_ai-rag/` | Agentic 查询：模型自己决定调用 03/04 里的哪种查询方式 |
| 03 | Vector | `03_vector/` | 数据怎么"切块"存向量 + 向量查询 + BM25 查询 |
| 04 | Graph | `04_graph/` | 数据怎么"切块"抽三元组存图谱 + 图查询（Neo4j） |
| 05 | Harness | `05_harness/` | 通用 Agent 六大组件：工具/上下文/权限/状态/恢复/评估 |
| 06 | Loop | `06_loop/` | 通用 Agent 最基础的 ReAct 循环 |
| 07 | Graph Engineering | `07_graph-engineering/` | Agent 编排图：研究员→写手→评论者，条件边+环路 |

02~04 是一组（RAG 全流程：爬虫→切块入库→查询），05~07 是另一组（通用 agent 架构模式，
不绑定 RAG 场景，参照 [Graph Engineering Guide 2026](https://www.aibuilderclub.com/blog/graph-engineering-guide-2026)
的 `Prompt → Context → Harness → Loop → Graph` 技术栈）。

## 目录结构

```
├── docker/                       # 02~04 共用的基础设施
│   ├── docker-compose.yml        # Postgres(pgvector) + Neo4j + pgAdmin
│   ├── postgres-init/01-init.sql # 首次启动自动建 vector 扩展 + documents 表
│   └── pgadmin/servers.json      # pgAdmin 预注册的 Postgres 连接
├── scripts/                      # 一键安装 / 一键启动
│   ├── setup.ps1                     # 一键装Docker+Node+Python，起容器，装依赖，建.env
│   ├── start-ocr.ps1                 # 01
│   ├── start-crawler.ps1             # 00
│   ├── start-vector-ingest.ps1       # 03 入库
│   ├── start-vector-visualize.ps1    # 03 embedding 可视化 demo
│   ├── start-graph-ingest.ps1        # 04 入库
│   ├── start-graph-visualize.ps1     # 04 图谱可视化 demo
│   ├── start-rag-query.ps1           # 02/03/04 查询（-Mode bm25|vector|graph|agentic）
│   ├── start-harness.ps1             # 05
│   ├── start-loop.ps1                # 06
│   └── start-graph-engineering.ps1   # 07
├── 00_crawler/                   # 爬虫
├── 01_ai-ocr/                     # OCR：server(NestJS) + web(React)
├── 02_ai-rag/                     # Agentic 查询
├── 03_vector/                     # 向量入库 + 向量/BM25 查询
├── 04_graph/                      # 图谱入库 + 图查询
├── 05_harness/                    # Agent Harness 样例
├── 06_loop/                       # Agent Loop 样例
├── 07_graph-engineering/          # Agent 编排图样例
├── common/                        # 02~04 共用的 Python 模块
│   ├── db_postgres.py / db_neo4j.py   # 数据库连接（已完整实现）
│   ├── embedding.py               # 【课堂留白】embedding 手写调用
│   └── extraction.py              # 【课堂留白】实体关系拆分手写调用
├── data/raw/                      # 爬虫产出（不进版本库，随时可重新生成）
├── requirements.txt               # 所有 Python 组件共用一份依赖
└── .env.example                   # 所有 Python 组件共用一份配置
```

## 快速开始

### 第 1 步：一键搭建整个环境

新拉下代码后，只需要跑这一个脚本，不需要额外手动装任何东西
（Docker/Node.js/pnpm/Python 已经装过的话会自动跳过，不会重复安装）：

```powershell
powershell -File scripts/setup.ps1
```

它会依次完成：

1. 检测/安装 Docker → 启动 Postgres(pgvector)、Neo4j、pgAdmin 三个容器 →
   Postgres 首次启动时自动建好 `vector` 扩展和 `documents` 表
   （`docker/postgres-init/01-init.sql`，不需要额外手动建库）
2. 检测/安装 Node.js + pnpm → `pnpm install`（01_ai-ocr 用）
3. 检测 Python → 建 `.venv` 虚拟环境 → `pip install -r requirements.txt`
   （00/02/03/04/05/06/07 这些 Python 项目共用这一个虚拟环境）
4. 从 `.env.example` 复制出 `.env`（如果还没有的话，不会覆盖已有配置）

完成后打印各个管理界面的地址、账号密码，以及接下来该做什么。

> 如果本机完全没装过 Docker/Node.js/Python，脚本会尝试用 `winget` 自动安装；
> 装完之后有的软件需要重新打开一个终端（刷新 PATH）才能继续，脚本会提示你
> 重新运行一次。

唯一还需要手动做的一步：编辑 `.env`，填入 `GEMINI_API_KEY`（或 `OPENAI_API_KEY`）——
这个不能自动化，需要你自己去 [Google AI Studio](https://aistudio.google.com/apikey)
申请。

### 第 2 步：跑 RAG 全流程（00 → 03/04 → 02）

```powershell
powershell -File scripts/start-crawler.ps1         # 00：抓取 AI News 新闻到 data/raw/
powershell -File scripts/start-vector-ingest.ps1   # 03：分段 + embedding，写入 Postgres
powershell -File scripts/start-graph-ingest.ps1    # 04：拆三元组，写入 Neo4j
powershell -File scripts/start-rag-query.ps1       # 02/03/04：交互式选查询方式
```

> 注意：`vector-ingest` 和 `graph-ingest` 依赖 `common/embedding.py` /
> `common/extraction.py` 里的核心调用（课堂留白，目前是占位报错）。这两步需要
> 先完成对应的课堂实操才能真正跑起来——BM25 查询和图查询不依赖它们，可以直接用。

入库跑完之后，还可以看两个可视化 demo（不涉及调用模型，随时能跑，会自动打开浏览器）：

```powershell
powershell -File scripts/start-vector-visualize.ps1   # 03：768 维 embedding 降到 2 维的散点图
powershell -File scripts/start-graph-visualize.ps1    # 04：实体关系的力导向节点图
```

### 01（OCR）单独运行

```powershell
powershell -File scripts/start-ocr.ps1
# 或分开手动跑：
pnpm dev:ocr:server   # 后端 http://localhost:3040
pnpm dev:ocr:web      # 前端 http://localhost:5102
```

### 05/06/07（Agent 架构样例）单独运行

```powershell
powershell -File scripts/start-harness.ps1
powershell -File scripts/start-loop.ps1
powershell -File scripts/start-graph-engineering.ps1 "自定义主题"
```

## 管理界面

| 服务 | 地址 | 账号 |
|---|---|---|
| pgAdmin | http://localhost:5050 | admin@training-project.com / admin123（已预注册 Postgres 连接，首次连接输入密码 rag_password） |
| Neo4j Browser | http://localhost:7475 | neo4j / raggraph123 |
| Postgres | localhost:5532 | rag / rag_password，数据库 ragdb |

> 本机常用端口 3000/5432/7474/7687 等已被其他服务占用，所以本项目分别改用
> 3040（OCR后端）/5532（Postgres）/7475+7688（Neo4j）/5050（pgAdmin）。

## 各项目详细说明

- [00_crawler/README.md](00_crawler/README.md)
- [01_ai-ocr/web/README.md](01_ai-ocr/web/README.md)
- [02_ai-rag/README.md](02_ai-rag/README.md)
- [03_vector/README.md](03_vector/README.md)
- [04_graph/README.md](04_graph/README.md)
- [05_harness/README.md](05_harness/README.md)
- [06_loop/README.md](06_loop/README.md)
- [07_graph-engineering/README.md](07_graph-engineering/README.md)

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
- **重试装饰器要排除"不会因重试而恢复"的错误**：`05_harness/recovery.py` 一开始用裸
  `except Exception`，会把课堂留白的 `NotImplementedError` 也当瞬时性错误重试，
  浪费几秒——只应该重试网络抖动/限流这类真正的瞬时性错误。
- **跨项目 Python import 用 `sys.path.insert`，注意路径深度**：`02_ai-rag/query_agentic.py`
  需要导入 `03_vector`/`04_graph` 里的查询函数，靠 `sys.path.insert(0, repo_root / "03_vector")`
  这种方式；把文件挪动目录层级后，所有 `Path(__file__).resolve().parents[N]` 里的 N
  都要跟着重新核对，挪错一层不会报错，但会静默地找错 `.env`/`data` 路径。
