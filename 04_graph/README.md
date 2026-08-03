# 04 · 图谱：数据怎么切块，怎么查（教学项目）

和 [03_vector](../03_vector) 演示的是同一件事的另一种做法：**文本怎么被"切块"**——
只是这里的"切块"不是简单切段落，而是把一句话拆成结构化的 `(主体, 关系, 客体)` 三元组，
存进 Neo4j 图数据库，再用 Cypher 查询实体之间的关系。

## 与 03_vector 的区别

| | 03_vector | 04_graph（本项目） |
|---|---|---|
| 数据结构 | 每段文字 → 一个向量 | 每句话 → 若干 (实体, 关系, 实体) 三元组 |
| "切块"的含义 | 把长文本切成短文本块 | 把一句话拆成结构化的实体和关系 |
| 擅长回答 | "哪段内容和问题最相关" | "A 和 B 之间是什么关系" |
| 查询方式 | 向量相似度 / BM25 关键词 | Cypher 图查询（沿关系边遍历） |

## 当前状态

| 文件 | 状态 |
|---|---|
| `ingest.py` | ✅ 完整实现（依赖 `common/extraction.py`） |
| `query_graph.py` | ✅ 完整实现并验证（Cypher 查询 + `startNode`/`endNode` 修正关系方向显示） |
| `common/extraction.py` | ⏳ 课堂留白：`extract_triples()` 已验证跑通（20 段爬虫文本共抽取出 194 条关系），核心代码注释在文件底部 |

`extraction.py` 一旦被课堂现场实现，`ingest.py` 不需要改任何代码就能直接跑通。

## 实测效果

用 [00_crawler](../00_crawler) 爬来的一句话测试拆分效果：

```
输入："李娜是启明科技的技术总监，向张伟汇报。"
输出：[
  {"subject": "李娜", "relation": "就职公司", "object": "启明科技"},
  {"subject": "李娜", "relation": "担任职务", "object": "技术总监"},
  {"subject": "李娜", "relation": "汇报对象", "object": "张伟"}
]
```

导入全部数据后查询"RAG"：

```
和 "RAG" 相关的关系：
  (RAG) -[最常见的实现方式]-> (向量数据库)
  (检索增强生成) -[缩写]-> (RAG)
  (RAG) -[数据来源]-> (网络资源)
  ...
```

## 运行

```bash
python 00_crawler/crawl.py    # 先爬数据（如果还没跑过）
python 04_graph/ingest.py     # 需要先实现 common/extraction.py 的 extract_triples
python 04_graph/query_graph.py "RAG"
```

也可以用根目录 `scripts/start-graph-ingest.ps1` 和 `scripts/start-rag-query.ps1 -Mode graph`。

## 课堂实操：手写实体拆分

在 `common/extraction.py` 里删掉 `extract_triples()` 的占位报错，参考文件底部注释掉的
参考实现，自己手写"拼 prompt → 调用模型 → 解析 JSON"的过程。

## 踩坑记录

**Cypher 无向查询会掩盖关系的真实方向**：查询语句用 `-[r]-`（不关心方向，只要跟目标实体有
连接就匹配），如果直接 `RETURN a.name, r.type, b.name`，显示方向会被"固定成从查询实体出发"，
可能和数据里存的真实方向相反。解决方法是用 `startNode(r)`/`endNode(r)` 取关系真实存储的
两端，而不是依赖模式匹配时 a/b 的绑定顺序。见 `query_graph.py` 里的注释。

## 谁在用这里的查询函数

[02_ai-rag](../02_ai-rag) 的 Agentic 查询会把这里的 `search_graph()` 当作工具函数调用。
