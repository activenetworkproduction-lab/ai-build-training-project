# 项目二：RAG 数据管道（教学项目）

三个阶段，把"公开网页"变成"能被 rag-query 查询的数据"：

```
维基百科词条                data/raw/*.txt              数据库
────────────               ────────────                ──────────
crawler/crawl.py     →     每个词条一个 .txt 文件
                              │
                              ├──→ vector-ingest/ingest.py ──→ Postgres documents 表
                              │       （分段 + embedding）      （VECTOR(768) 列）
                              │
                              └──→ graph-ingest/ingest.py  ──→ Neo4j
                                      （拆三元组）              （Entity 节点 + RELATED_TO 关系）
```

## 当前状态

| 文件 | 状态 |
|---|---|
| `crawler/crawl.py` | ✅ 完整实现（纯网页抓取，不涉及模型调用，不留白） |
| `vector-ingest/ingest.py` | ✅ 完整实现（依赖 `common/embedding.py`） |
| `graph-ingest/ingest.py` | ✅ 完整实现（依赖 `common/extraction.py`） |
| `common/embedding.py` | ⏳ 课堂留白：`embed_text()` 已验证跑通（71 条段落全部导入成功），核心代码注释在文件底部 |
| `common/extraction.py` | ⏳ 课堂留白：`extract_triples()` 已验证跑通（20 段文本抽取出 194 条关系），核心代码注释在文件底部 |

## 为什么爬维基百科？

选了几个和本项目主题直接相关的中文维基百科词条（检索增强生成/向量数据库/图数据库/
PostgreSQL），这样做出来的效果很应景——最后可以问系统"什么是 RAG""向量数据库和
图数据库有什么区别"，答案就来自这里抓的内容，边讲边验证。

## 运行顺序

```bash
python data-pipeline/crawler/crawl.py         # 产出 data/raw/*.txt
python data-pipeline/vector-ingest/ingest.py  # 需要先实现 embed_text
python data-pipeline/graph-ingest/ingest.py   # 需要先实现 extract_triples
```

也可以用根目录 `scripts/` 下的一键脚本（会自动用 `.venv` 里的 Python）。

## 设计上的几个取舍

- **分块方式很简单**：直接按段落（爬虫已按自然换行切好）切分，没有做滑动窗口/
  重叠切分这类更复杂的策略——教学场景下"看懂流程"比"处理长文档的最优策略"更重要。
- **图谱抽取只取每篇文章前 5 段**（`graph-ingest/ingest.py` 的 `MAX_PARAGRAPHS_PER_FILE`）：
  控制模型调用次数，避免"简单导入样例"变成一次要跑几十次模型调用。
- **每次运行都会清空重导**（`TRUNCATE` / `DETACH DELETE`）：教学场景下"随时能重跑"
  比"增量更新"更重要，重复运行不会导致数据翻倍。
