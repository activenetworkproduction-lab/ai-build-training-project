# 04 · 图谱：数据怎么切块，怎么查（教学项目）

和 [03_vector](../03_vector) 演示的是同一件事的另一种做法：**文本怎么被"切块"**——
只是这里的"切块"不是简单切段落，而是把一句话拆成结构化的 `(主体, 关系, 客体)` 三元组，
存进 Neo4j 图数据库，再用 Cypher 查询实体之间的关系。数据来源是 [00_crawler](../00_crawler)
抓的 [AI News](https://ai-news.tayoru-kun.com/) 新闻。

## 与 03_vector 的区别

| | 03_vector | 04_graph（本项目） |
|---|---|---|
| 数据结构 | 每条新闻 → 一个向量 | 每条新闻 → 若干 (实体, 关系, 实体) 三元组 |
| "切块"的含义 | 把新闻按行切成短文本块 | 把一条新闻拆成结构化的实体和关系 |
| 擅长回答 | "哪条新闻和问题最相关" | "A 和 B 之间是什么关系" |
| 查询方式 | 向量相似度 / BM25 关键词 | Cypher 图查询（沿关系边遍历） |

## 当前状态

| 文件 | 状态 |
|---|---|
| `ingest.py` | ✅ 完整实现（依赖 `common/extraction.py`） |
| `query_graph.py` | ✅ 完整实现并验证（Cypher 查询 + `startNode`/`endNode` 修正关系方向显示） |
| `common/extraction.py` | ⏳ 课堂留白：`extract_triples()` 已验证跑通（25 条新闻共抽取出 190 条关系），核心代码注释在文件底部 |

`extraction.py` 一旦被课堂现场实现，`ingest.py` 不需要改任何代码就能直接跑通。

## 实测效果

用一条真实抓取的新闻测试拆分效果：

```
输入："阿里巴巴Qwen3.8-Max全球发布，开放权重即将推出：阿里巴巴集团控股已将其下一代
      旗舰人工智能模型Qwen3.8-Max向全球用户广泛开放……"
输出：[
  {"subject": "阿里巴巴", "relation": "发布", "object": "Qwen3.8-Max"},
  {"subject": "阿里巴巴", "relation": "重新开放开源", "object": "顶级AI模型"},
  {"subject": "阿里巴巴", "relation": "发布平台", "object": "Arena.AI"}
]
```

导入全部数据后（25 条新闻，抽取出 190 条关系）查询"阿里巴巴"：

```
和 "阿里巴巴" 相关的关系：
  (阿里巴巴) -[发布平台]-> (Arena.AI)
  (阿里巴巴) -[重新开放开源]-> (顶级AI模型)
  (阿里巴巴) -[发布]-> (Qwen3.8-Max)
```

## 运行

```bash
python 00_crawler/crawl.py    # 先爬数据（如果还没跑过）
python 04_graph/ingest.py     # 需要先实现 common/extraction.py 的 extract_triples
python 04_graph/query_graph.py "阿里巴巴"
```

也可以用根目录 `scripts/start-graph-ingest.ps1` 和 `scripts/start-rag-query.ps1 -Mode graph`。

## 课堂实操：手写实体拆分

在 `common/extraction.py` 里删掉 `extract_triples()` 的占位报错，参考文件底部注释掉的
参考实现，自己手写"拼 prompt → 调用模型 → 解析 JSON"的过程。

## 踩坑记录

1. **Cypher 无向查询会掩盖关系的真实方向**：查询语句用 `-[r]-`（不关心方向，只要跟目标
   实体有连接就匹配），如果直接 `RETURN a.name, r.type, b.name`，显示方向会被"固定成
   从查询实体出发"，可能和数据里存的真实方向相反。解决方法是用 `startNode(r)`/`endNode(r)`
   取关系真实存储的两端，而不是依赖模式匹配时 a/b 的绑定顺序。见 `query_graph.py` 里的注释。
2. **同一实体可能被抽成不同的名字变体**：比如"英伟达"这个实体名，如果某条新闻抽取时
   模型写成了"NVIDIA"或"英伟达公司"，图里就会出现好几个指向同一家公司的节点，查询时
   按精确字符串匹配可能查不到——这是"手写实体拆分"这一步教学时值得展开讨论的真实坑，
   生产级系统通常还需要一步"实体对齐/归一化"。

## 谁在用这里的查询函数

[02_ai-rag](../02_ai-rag) 的 Agentic 查询会把这里的 `search_graph()` 当作工具函数调用。
