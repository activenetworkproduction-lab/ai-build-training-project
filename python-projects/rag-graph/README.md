# 项目三 · 图数据库分支：Neo4j 实现 RAG（教学项目）

用 Docker 起一个 Neo4j，把一段描述"公司组织架构"的文本拆成实体和关系存进图里，
再用图查询回答"谁向谁汇报""某个人和某个产品有什么关系"这类问题。

## 与向量库分支（python-projects/rag-vector）的区别

| | 向量库分支 | 本项目（图数据库分支） |
|---|---|---|
| 数据结构 | 每段文字 → 一个向量 | 每句话 → 若干 (实体, 关系, 实体) 三元组 |
| "拆分"的含义 | 把长文本切成短文本块 | 把一句话拆成结构化的实体和关系 |
| 擅长回答 | "哪段内容和问题最相关" | "A 和 B 之间是什么关系" |
| 查询方式 | 向量相似度 / BM25 关键词 | Cypher 图查询（沿关系边遍历） |

## 当前状态：已完整实现，实体拆分核心留作课堂实操

| 文件 | 状态 |
|---|---|
| `docker-compose.yml` | ✅ 已验证可用（Neo4j 5 社区版，HTTP 端口 7475，Bolt 端口 7688） |
| `src/db.py` | ✅ 已实现（Neo4j driver 连接） |
| `src/init_db.py` | ✅ 已实现（建唯一约束） |
| `src/extraction.py` | ⏳ `extract_triples()` 目前是占位报错。真正调用 Gemini 把一句话拆成三元组的实现**已经写完并验证跑通**，代码在方法下方的注释块里，课堂上现场重写 |
| `src/ingest.py` | ✅ 已实现（依赖 `extract_triples`，本身逻辑完整） |
| `src/query_graph.py` | ✅ 已实现并验证（Cypher 查询 + `startNode`/`endNode` 修正关系方向显示） |

`extraction.py` 一旦被课堂现场实现，`ingest.py` 不需要改任何代码就能直接跑通。

## 环境准备

```bash
# 1. 启动 Neo4j（首次会拉取 neo4j:5-community 镜像）
docker compose up -d
# Neo4j Browser 可视化界面：http://localhost:7475　账号 neo4j / raggraph123

# 2. 建 Python 虚拟环境并装依赖
python -m venv .venv
.venv\Scripts\activate        # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt

# 3. 复制环境变量（需要 GEMINI_API_KEY 才能跑实体拆分）
copy .env.example .env        # Windows；macOS/Linux 用 cp

# 4. 初始化约束
python src/init_db.py
```

## 实测效果（课堂讲解素材）

用 `sample-data/company.txt` 里的一句话测试拆分效果：

```
输入："李娜是启明科技的技术总监，向张伟汇报。"
输出：[
  {"subject": "李娜", "relation": "就职公司", "object": "启明科技"},
  {"subject": "李娜", "relation": "担任职务", "object": "技术总监"},
  {"subject": "李娜", "relation": "汇报对象", "object": "张伟"}
]
```

把全部 8 句话都拆分导入后（共写入 17 条关系），查询"李娜"：

```
和 "李娜" 相关的关系：
  (李娜) -[负责]-> (云记的技术架构设计)
  (王芳) -[汇报给]-> (李娜)
  (李娜) -[汇报给]-> (张伟)
  (李娜) -[职位]-> (技术总监)
  (李娜) -[任职于]-> (启明科技)
```

## 课堂实操：手写实体拆分

在 `src/extraction.py` 里删掉 `extract_triples()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"拼 prompt → 调用模型 → 解析 JSON"的过程。实现完之后：

```bash
python src/ingest.py           # 导入 sample-data/company.txt
python src/query_graph.py "李娜"
```

## 踩坑记录（写代码时遇到的问题，值得课堂上提一下）

**Cypher 无向查询会掩盖关系的真实方向**：查询语句用 `-[r]-`（不关心方向，只要跟目标实体有连接
就匹配），如果直接 `RETURN a.name, r.type, b.name`，显示方向会被"固定成从查询实体出发"，
可能和数据里存的真实方向相反（比如"王芳汇报给李娜"存的方向是 王芳→李娜，查李娜时若直接用
a/b 会显示成"李娜汇报给王芳"，正好反了）。解决方法是用 `startNode(r)`/`endNode(r)` 取关系
真实存储的两端，而不是依赖模式匹配时 a/b 的绑定顺序。见 `src/query_graph.py` 里的注释。

## 为什么端口是 7475/7688 而不是默认的 7474/7687？

本机默认端口已经被别的 Neo4j 实例占用了，所以改用 7475（HTTP/Browser）和
7688（Bolt/驱动连接），`.env.example` 里的 `NEO4J_URI` 已经对应改好。
