# 项目三 · 向量库分支：Postgres + pgvector 实现 RAG（教学项目）

用 Docker 起一个带 pgvector 扩展的 Postgres，把一批文本做 embedding 存进去，
再分别用**向量检索**和 **BM25 检索**两种方式查询，直观对比两者的差异。

## 当前状态：已完整实现，embedding 核心留作课堂实操

| 文件 | 状态 |
|---|---|
| `docker-compose.yml` | ✅ 已验证可用（Postgres + pgvector，端口 5532） |
| `src/db.py` | ✅ 已实现（数据库连接） |
| `src/init_db.py` | ✅ 已实现（建扩展 + 建表，`notes.embedding` 是 768 维向量） |
| `src/embedding.py` | ⏳ `embed_text()` 目前是占位报错。真正调用 Gemini embedding 接口的实现**已经写完并验证跑通**（返回 768 维向量），代码在方法下方的注释块里，课堂上现场重写 |
| `src/ingest.py` | ✅ 已实现（依赖 `embed_text`，本身逻辑完整） |
| `src/query_vector.py` | ✅ 已实现并验证（pgvector 的 `<=>` 余弦距离排序） |
| `src/query_bm25.py` | ✅ 已实现并验证（`rank_bm25`，按字符切分中文） |

`embedding.py` 一旦被课堂现场实现，`ingest.py` 和 `query_vector.py` 不需要改任何代码就能直接跑通
——它们已经按照"依赖 embed_text() 存在"的假设写完整了。

## 环境准备

```bash
# 1. 启动数据库（首次会拉取 pgvector/pgvector:pg16 镜像）
docker compose up -d

# 2. 建 Python 虚拟环境并装依赖
python -m venv .venv
.venv\Scripts\activate        # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt

# 3. 复制环境变量（需要 GEMINI_API_KEY 才能跑 embedding）
copy .env.example .env        # Windows；macOS/Linux 用 cp

# 4. 初始化数据库结构
python src/init_db.py
```

## 实测效果对比（课堂讲解素材）

同样搜"pgvector 扩展"，两种检索给出的排序完全不同：

**BM25**（关键词命中越多分数越高）：
```
1. [得分 13.31] Postgres 是一个开源的关系型数据库，支持通过 pgvector 扩展存储向量并做相似度检索。
2. [得分  3.15] Docker 可以把数据库、依赖环境打包成容器，本地一条命令就能启动，不用手动安装配置。
```

**向量检索**（问"什么是向量检索？"，即使原文没有完全一样的措辞也能找到语义相关内容）：
```
1. [距离 0.1557] 向量检索的核心思路：把文本变成一串数字（embedding），语义相近的文本在向量空间里距离也相近。
2. [距离 0.2238] 向量检索擅长找"意思相近"的内容，BM25 擅长找"关键词精确匹配"的内容，实际系统里常把两者结合使用。
```

## 课堂实操：手写 embedding 调用

在 `src/embedding.py` 里删掉 `embed_text()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"拼 HTTP 请求 → 调用 Gemini embedding 接口 → 取出向量"的过程。实现完之后：

```bash
python src/ingest.py                    # 导入 sample-data/notes.txt
python src/query_vector.py "什么是向量检索？"
python src/query_bm25.py "pgvector 扩展"
```

## 踩坑记录（写代码时遇到的两个问题，值得课堂上提一下）

1. **`text-embedding-004` 模型已下线**：2026 年这个曾经很常见的模型名已经不可用了，
   实测能用的是 `gemini-embedding-001`（默认输出 3072 维，用 `outputDimensionality`
   参数截断成 768 维）。AI 模型的可用性会随时间变化，写死的模型名要留意过期风险。
2. **pgvector 查询要显式 `::vector` 类型转换**：`INSERT` 时 psycopg2 把 Python list
   转成 `numeric[]`，pgvector 定义了 `numeric[]` 到 `vector` 的赋值级隐式转换，所以
   `INSERT` 不用显式转换就能存进去；但 `SELECT ... embedding <=> %s` 里没有目标列类型
   可以触发隐式转换，必须写成 `embedding <=> %s::vector` 才能用 `<=>` 运算符。

## 为什么端口是 5532 而不是默认的 5432？

本机 5432 端口已经被别的 Postgres 实例占用了，所以 docker-compose 里把容器的
5432 映射到宿主机的 5532，`.env.example` 里的 `DATABASE_URL` 已经对应改好。
