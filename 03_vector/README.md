# 03 · 向量：数据怎么切块，怎么查（教学项目）

这个项目演示向量检索的完整闭环：**文本怎么被切块、embedding、存进 Postgres**，
以及**两种不同原理的查询方式**（语义向量 vs 关键词 BM25）之间的效果差异。
数据来源是 [00_crawler](../00_crawler) 抓的 [AI News](https://ai-news.tayoru-kun.com/) 新闻。

## 当前状态

| 文件 | 状态 |
|---|---|
| `ingest.py` | ✅ 完整实现（依赖 `common/embedding.py`） |
| `query_vector.py` | ✅ 完整实现并验证（pgvector 的 `<=>` 余弦距离排序） |
| `query_bm25.py` | ✅ 完整实现并验证（`rank_bm25`，按字符切分中文） |
| `common/embedding.py` | ⏳ 课堂留白：`embed_text()` 已验证跑通（61 条新闻全部导入成功），核心代码注释在文件底部 |
| `visualize_embeddings.py` | ✅ 完整实现（PCA 降维 + 生成可视化 HTML，不涉及调用模型，不是课堂留白点） |

`embedding.py` 一旦被课堂现场实现，`ingest.py` 和 `query_vector.py` 不需要改任何代码
就能直接跑通——它们已经按照"依赖 embed_text() 存在"的假设写完整了。

## 数据怎么"被清晰切块"的

1. **切块（chunking）**：[00_crawler](../00_crawler) 按分类（模型/工具/协议/平台/研究）
   汇总出 5 个文件，每个文件一行一条新闻（标题+摘要）；`ingest.py` 直接按行切分——
   每条新闻本身长度适中，不需要再做更复杂的滑动窗口/重叠切分
2. **embedding**：每一行调用 `common/embedding.py` 的 `embed_text()`，转成 768 维向量
3. **存储**：连同来源分类（`source`，比如"模型"）一起存进 Postgres 的 `documents` 表
   （`docker/postgres-init/01-init.sql` 里定义的 `VECTOR(768)` 列）

## 两种查询方式的实测效果对比

同样围绕"阿里巴巴 Qwen"这类问题，两种检索给出的排序完全不同：

**BM25**（关键词命中越多分数越高，问"阿里巴巴 Qwen"）：
```
1. [得分 32.29] 阿里巴巴Qwen3.8-Max全球发布，开放权重即将推出：...
2. [得分 31.95] 阿里巴巴发布迄今为止最强大的AI模型Qwen3.8-Max：...
3. [得分  5.96] Anthropic Claude AI 在后量子安全测试中取得突破：...
```

**向量检索**（问"有哪些关于AI安全和监管的新闻？"，原文没有一模一样的措辞也能找到）：
```
1. [距离 0.323] 特朗普政府接近敲定AI公司自愿监管框架：...
2. [距离 0.324] 科技员工呼吁全球合作管理AI风险："Pacing the Frontier"倡议...
3. [距离 0.334] 中国谴责美国AI制裁威胁为"AI霸权"，誓言反击：...
```

## 运行

```bash
python 00_crawler/crawl.py              # 先爬数据（如果还没跑过）
python 03_vector/ingest.py              # 需要先实现 common/embedding.py 的 embed_text
python 03_vector/query_vector.py "有哪些关于AI安全和监管的新闻？"
python 03_vector/query_bm25.py "阿里巴巴 Qwen"
```

也可以用根目录 `scripts/start-vector-ingest.ps1` 和 `scripts/start-rag-query.ps1 -Mode bm25|vector`。

## embedding 可视化 demo

768 维向量人没法直接看懂，`visualize_embeddings.py` 用手写的 PCA（SVD 实现，见文件里的
`pca_2d()`）把它压缩到 2 维画成散点图，直观展示"语义相近的新闻会聚在一起"这件事：

```bash
python 03_vector/visualize_embeddings.py    # 或 scripts/start-vector-visualize.ps1（会自动打开浏览器）
```

生成的 `03_vector/embeddings_visualization.html` 是单文件（数据直接内嵌，双击打开即可），
点击下方的分类标签可以高亮某一类新闻，鼠标悬停能看到具体内容。实测 61 条向量降到 2 维后，
前两个主成分只解释了原始 768 维里约 12.6% 的方差——这是正常的取舍：2 维图看到的只是
高维语义空间的一个粗略投影，不代表两个点离得远就一定不相关。

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
