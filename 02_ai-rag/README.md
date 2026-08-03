# 02 · AI RAG：Agentic 查询（教学项目）

展示 RAG 系统里最"智能"的一种查询方式：不是人决定用哪种检索方式，而是**大模型自己
决定"查几次、每次用什么方式查"**，最后综合所有结果给出回答。数据来源是
[00_crawler](../00_crawler) 抓的 [AI News](https://ai-news.tayoru-kun.com/) 新闻。

依赖 [03_vector](../03_vector)（`search_bm25`/`search_vector`）和 [04_graph](../04_graph)
（`search_graph`）已经写好的查询函数，本项目只负责"决策"这一层——把三种查询包装成
工具（tools），让模型自己选。

## 和另外两种查询方式的关系

| | BM25 / 向量（03_vector） | 图（04_graph） | Agentic（本项目） |
|---|---|---|---|
| 决策者 | 人 | 人 | 模型自己 |
| 查询次数 | 1 次 | 1 次 | 1~4 次，模型自己决定 |
| 适合 | 已经确定用哪种方式最合适 | 同上 | 复杂问题，一种方式不够时自动换/组合 |

## 当前状态

| 文件 | 状态 |
|---|---|
| `query_agentic.py` | ✅ 循环/工具分发框架完整实现并验证；⏳ 核心的 `call_model()`（发请求给大模型拿决策）课堂留白 |

## 实测效果

问"阿里巴巴和英伟达最近有什么相关的AI新闻？"，模型自己规划了 4 轮工具调用：

```
第 1 轮：bm25_search("阿里巴巴 英伟达")     → 查到几条阿里巴巴 Qwen3.8-Max 的新闻
第 2 轮：vector_search(同样的问题)          → 补充语义相关内容（AI安全联盟、融资等）
第 3 轮：graph_search("阿里巴巴")           → 查到 阿里巴巴-[发布]->Qwen3.8-Max 等关系
第 4 轮：graph_search("英伟达")             → 没有查到结果
```

最后一轮 `graph_search("英伟达")` 没查到东西（说明图谱里这个实体名没有精确匹配上，
见 [04_graph/README.md](../04_graph/README.md) 的踩坑记录），但模型没有因此卡住，
而是如实告诉用户"知识库里没有两家公司直接相关的新闻"，同时分别列出了两家公司各自
的最新动态（阿里巴巴发布 Qwen3.8-Max；英伟达牵头成立开放安全AI联盟、和 OpenAI 谈
2500 亿美元融资），并注明结论主要来自哪种查询方式——这正是 Agentic 查询的价值所在：
**某个工具没查到东西不代表整个流程失败，模型会用其它工具的结果拼出一个诚实的回答**，
这是固定单一查询方式做不到的。

## 怎么搭起来的

工具定义（`TOOLS`）用的是和 OpenAI function calling 完全一样的格式，Gemini 的
OpenAI 兼容接口也认这套格式。整个流程：

1. 把问题 + 工具定义发给模型
2. 模型要么返回"调用某个工具"（`tool_calls`），要么直接返回文字答案
3. 如果是工具调用：本地执行对应的 `search_bm25`/`search_vector`/`search_graph`
   （从 `03_vector`/`04_graph` 导入），把结果当作一条 `role: tool` 的消息加回对话历史，再问模型一次
4. 重复最多 `MAX_ROUNDS`（4）轮，模型觉得信息够了就会直接给出文字答案

`dispatch_tool()` 和整个多轮循环已经完整实现，唯一留白的是 `call_model()`。

## 运行

前提：[00_crawler](../00_crawler) 已爬数据，[03_vector](../03_vector)/[04_graph](../04_graph)
已完成对应的 ingest（否则查到的都是空结果）。

```bash
python 02_ai-rag/query_agentic.py "阿里巴巴和英伟达最近有什么相关的AI新闻？"
```

也可以用根目录 `scripts/start-rag-query.ps1 -Mode agentic`。

## 课堂实操

在 `query_agentic.py` 里删掉 `call_model()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"把 messages + TOOLS 发给模型、拿到它的决策"的过程。
