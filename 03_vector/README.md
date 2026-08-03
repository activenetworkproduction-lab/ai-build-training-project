# 03 · 向量：数据怎么切块，怎么查（教学项目）

这个项目演示向量检索的完整闭环：**文本怎么被切块、embedding、存进 Postgres**，
以及**两种不同原理的查询方式**（语义向量 vs 关键词 BM25）之间的效果差异。

## 当前状态

| 文件 | 状态 |
|---|---|
| `ingest.py` | ✅ 完整实现（依赖 `common/embedding.py`） |
| `query_vector.py` | ✅ 完整实现并验证（pgvector 的 `<=>` 余弦距离排序） |
| `query_bm25.py` | ✅ 完整实现并验证（`rank_bm25`，按字符切分中文） |
| `common/embedding.py` | ⏳ 课堂留白：`embed_text()` 已验证跑通（71 条爬虫段落全部导入成功），核心代码注释在文件底部 |

`embedding.py` 一旦被课堂现场实现，`ingest.py` 和 `query_vector.py` 不需要改任何代码
就能直接跑通——它们已经按照"依赖 embed_text() 存在"的假设写完整了。

## 数据怎么"被清晰切块"的

1. **切块（chunking）**：[00_crawler](../00_crawler) 爬下来的维基百科正文，本身已经
   按自然段落换行分好了；`ingest.py` 直接按行切分——每段几十到几百字，长度适中，
   不需要再做更复杂的滑动窗口/重叠切分
2. **embedding**：每个切块调用 `common/embedding.py` 的 `embed_text()`，转成 768 维向量
3. **存储**：连同来源文件名（`source`）一起存进 Postgres 的 `documents` 表
   （`docker/postgres-init/01-init.sql` 里定义的 `VECTOR(768)` 列）

## 两种查询方式的实测效果对比

同样搜"pgvector 扩展"/"什么是向量检索"，两种检索给出的排序完全不同：

**BM25**（关键词命中越多分数越高）：
```
1. [得分 13.31] Postgres 是一个开源的关系型数据库，支持通过 pgvector 扩展存储向量并做相似度检索。
2. [得分  3.15] Docker 可以把数据库、依赖环境打包成容器，本地一条命令就能启动，不用手动安装配置。
```

**向量检索**（即使原文没有完全一样的措辞也能找到语义相关内容）：
```
1. [距离 0.1557] 向量检索的核心思路：把文本变成一串数字（embedding），语义相近的文本在向量空间里距离也相近。
2. [距离 0.2238] 向量检索擅长找"意思相近"的内容，BM25 擅长找"关键词精确匹配"的内容，实际系统里常把两者结合使用。
```

## 运行

```bash
python 00_crawler/crawl.py       # 先爬数据（如果还没跑过）
python 03_vector/ingest.py       # 需要先实现 common/embedding.py 的 embed_text
python 03_vector/query_vector.py "什么是向量检索？"
python 03_vector/query_bm25.py "pgvector 扩展"
```

也可以用根目录 `scripts/start-vector-ingest.ps1` 和 `scripts/start-rag-query.ps1 -Mode bm25|vector`。

## 课堂实操：手写 embedding 调用

在 `common/embedding.py` 里删掉 `embed_text()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"拼 HTTP 请求 → 调用 Gemini embedding 接口 → 取出向量"的过程。

## 踩坑记录

1. **`text-embedding-004` 模型已下线**：实测能用的是 `gemini-embedding-001`（默认输出
   3072 维，用 `outputDimensionality` 参数截断成 768 维）。
2. **pgvector 查询要显式 `::vector` 类型转换**：`INSERT` 有隐式转换能直接存，但
   `SELECT ... embedding <=> %s` 里没有目标列类型，必须写成 `%s::vector`。
3. **BM25Okapi 对空语料会直接除零崩溃**：如果 `documents` 表还是空的（没跑过
   `ingest.py`）就调 `query_bm25.py`，已经加了判断提前返回空结果，不会看到
   `ZeroDivisionError`。

## 谁在用这里的查询函数

[02_ai-rag](../02_ai-rag) 的 Agentic 查询会把这里的 `search_bm25()`/`search_vector()`
当作工具函数调用。
