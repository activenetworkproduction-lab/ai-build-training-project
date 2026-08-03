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
| `visualize_graph.py` | ✅ 完整实现（力导向布局 + 生成可视化 HTML，不涉及调用模型，不是课堂留白点） |

`extraction.py` 一旦被课堂现场实现，`ingest.py` 不需要改任何代码就能直接跑通。

## 调试：在哪里能看到数据被拆分/转换

想在调试器里打断点、单步观察"一条新闻怎么变成几条三元组"，看这几个精确位置：

| 步骤 | 位置 | 说明 |
|---|---|---|
| 取段落（chunking） | [`04_graph/ingest.py:36`](ingest.py#L36)（`load_paragraphs()` 里 `[line.strip() for line in file.read_text(...).splitlines() ...]`） | 按行拆出候选段落，这里能看到"一篇文章"变成"若干行文本"的原始输入 |
| 只取前 N 段 | [`04_graph/ingest.py:37`](ingest.py#L37)（`paragraphs.extend(lines[:MAX_PARAGRAPHS_PER_FILE])`） | 为控制模型调用次数，每个分类文件只取前 `MAX_PARAGRAPHS_PER_FILE`（5）行——想改抽取范围就改这里 |
| 转换成三元组 | [`04_graph/ingest.py:58`](ingest.py#L58)（`triples = extract_triples(text)`） | 调用点：一段文本在这一行变成若干条 `{subject, relation, object}` |
| 三元组抽取的实际逻辑 | [`common/extraction.py:26`](../common/extraction.py#L26)（`extract_triples()`，课堂留白，当前是占位报错）；参考实现在文件第 32~68 行的注释块里 | 想看真实的"拼 prompt → 调用模型 → 解析 JSON"过程，去掉这行的占位报错、临时取消注释块即可跑通调试 |
| 拆完之后长什么样 | [`04_graph/visualize_graph.py`](visualize_graph.py) 的 `build_graph()` 函数 | 所有三元组在这里被汇总成节点/边列表，配合[图谱可视化 demo](#图谱可视化-demo)直接肉眼看效果 |

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

## 图谱可视化 demo

`visualize_graph.py` 把 Neo4j 里所有 (实体, 关系, 实体) 三元组导出成一张力导向节点图：

```bash
python 04_graph/visualize_graph.py    # 或 scripts/start-graph-visualize.ps1（会自动打开浏览器）
```

生成的 `04_graph/graph_visualization.html` 是单文件（数据直接内嵌，双击打开即可）。
节点位置由页面里手写的力导向布局算法（Fruchterman-Reingold 简化版）实时计算——节点之间
互相排斥、有关系的节点之间用"弹簧"拉近，可以拖动节点、点击节点看它的完整关系列表，
也可以在搜索框输入实体名快速定位。实测 213 个实体、189 条关系导出后，图上能直接看到
几个连接数明显更多的"枢纽"实体（比如 Qwen3.8-Max、OpenAI），这正是"文本被结构化成图"
之后才能一眼看出来的信息——单纯读原始新闻文本是看不出这种全局关系密度分布的。

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
