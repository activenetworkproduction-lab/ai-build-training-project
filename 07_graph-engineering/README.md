# 07 · Graph Engineering（Agent 编排图，教学项目）

**注意**：这里的"图"是 agent 编排图（研究员→写手→评论者，节点+边+共享状态），
和 [04_graph](../04_graph) 的 Neo4j 知识图谱是完全不同的两回事——这也是为什么
这个项目单独编号叫 `graph-engineering` 而不是简单叫 `graph`。

## 概念来源

参照 [Graph Engineering Guide (2026)](https://www.aibuilderclub.com/blog/graph-engineering-guide-2026)：
把多个专业化的智能体或步骤连成一张图——**节点**做具体工作，**边**决定路由，
**共享状态**沿着边流动。当一个 [06_loop](../06_loop) 那样的单一循环不够用（工作需要
拆成不同专业领域、需要显式可审计的路由、需要失败隔离）时才需要升级到图；
文章原话是 "most tasks never need it"——多数任务用循环就够，图是过度工程的常见来源。

## 三个节点

```
研究员 ──→ 写手 ──→ 评论者
             ↑           │
             └── REVISE ─┘（条件边，构成一个环）
                      APPROVE → 结束（另一条条件边）
```

| 节点 | 职责 |
|---|---|
| `research_node` | 针对主题列出 3-5 条关键要点 |
| `writer_node` | 基于要点（以及评论者的反馈，如果有）写一段短文 |
| `critic_node` | 审阅草稿，决定 APPROVE（结束）或 REVISE（打回写手重写） |

`MAX_REVISIONS` 是"失败隔离"的体现：环不能无限转下去。

## 当前状态

✅ 已用真实 Gemini 调用验证跑通（APPROVE 路径 + 真实触发的 REVISE 环路），
⏳ 核心的 `call_model()`（`nodes.py` 里，三个节点共用）课堂留白。

## 实测效果

主题"RAG（检索增强生成）"：评论者第一轮就 APPROVE，0 次修改结束——质量把关到位时
图不一定要经过环路。

换个主题"向量数据库"则真实触发了一次 REVISE：评论者指出草稿把"向量数据库"和
"嵌入模型"的职责搞混了（"向量数据库本身不负责把数据转成向量，那是 embedding 模型的活，
向量数据库只管存储和检索"），写手看到反馈后改写，第二版才被 APPROVE：

```
[Node: 评论者] 决定：REVISE，反馈：...向量数据库本身并不负责"将非结构化数据转化为高维向量"...
[Edge] 评论者：REVISE → 打回写手节点（第 1 次修改）
[Node: 写手] 第 2 版草稿：...它并不负责将非结构化数据转化为向量，而是通过高效存储与检索...
[Node: 评论者] 决定：APPROVE，反馈：这段草稿定义精准...
```

另外用一个模拟的"永远要求修改"评论者单独测试过 `MAX_REVISIONS` 保护，3 轮后正确停止，
不会死循环。

## 运行

```bash
python 07_graph-engineering/main.py "RAG（检索增强生成）"
```

也可以用根目录 `scripts/start-graph-engineering.ps1`。

## 课堂实操

在 `nodes.py` 里删掉 `call_model()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"把 prompt 发给模型、拿到纯文本回答"的过程。三个节点、`graph.py` 里的
路由逻辑（条件边+环+`MAX_REVISIONS`保护）都已经完整实现。
