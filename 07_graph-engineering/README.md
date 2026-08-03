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
`visualize_flow.py`/`demo_max_revisions.py` 是纯展示/演示脚本，不涉及调用模型，不是课堂留白点。

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
不会死循环——见下面的[边界情况演示](#边界情况演示max_revisions-保护)，现在是一个
真正能跑起来复现的脚本，不再只是 README 里的一句描述。

## 运行

```bash
python 07_graph-engineering/main.py "RAG（检索增强生成）"
```

也可以用根目录 `scripts/start-graph-engineering.ps1`。每次运行结束都会在
`07_graph-engineering/trace_visualization.html` 生成这次真实过程的图结构 + 时间线（自动打开）。

## 调试：在哪里能看到 Agent 的决策/执行过程

| 步骤 | 位置 | 说明 |
|---|---|---|
| 模型决策的调用点 | [`nodes.py:20`](nodes.py#L20)（`call_model()`，课堂留白，当前是占位报错） | 参考实现在文件第 80~107 行的注释块里，三个节点共用 |
| 三个节点各自的职责 | [`nodes.py:26`](nodes.py#L26) `research_node()` / [`nodes.py:33`](nodes.py#L33) `writer_node()` / [`nodes.py:50`](nodes.py#L50) `critic_node()` | 每个节点单独一个函数，prompt 互不干扰 |
| 评论者输出的解析 | [`nodes.py:66`](nodes.py#L66)（`_parse_critic_response()`） | 把模型返回的"决定：.../反馈：..."文本拆成结构化的 `(decision, feedback)` |
| 图的路由逻辑（条件边+环） | [`graph.py:30-46`](graph.py#L30-L46)（`run_graph()` 里的 `while True:` 循环） | APPROVE 就 `break`，REVISE 就 `state.revision_count += 1` 再继续，`MAX_REVISIONS` 保护也在这里 |

## 可视化：图结构 + 这次运行实际走过的路径

`visualize_flow.py` 把这次运行画成两部分：上半部分是研究员→写手→评论者的静态流程图，
REVISE 环路上标出这次真实走了几次、结束边标出是 APPROVE 通过还是撞到 `MAX_REVISIONS`
强制结束；下半部分是每个节点/边事件的时间线（复用 `common/trace.py`，和 05/06 一样的
组件）。生成的 `trace_visualization.html` 是单文件，双击打开即可看。

## 边界情况演示：MAX_REVISIONS 保护

```bash
python 07_graph-engineering/demo_max_revisions.py
```

用一个固定返回 REVISE 的假评论者（不需要 GEMINI_API_KEY，也不需要先实现课堂留白的
`call_model()`），确定性地验证"评论者永远不满意时，环不会无限转下去"：脚本最后会
断言 `revision_count == MAX_REVISIONS`，跑起来直接看到断言通过，而不是只在 README
里读到这句描述。

## 课堂实操

在 `nodes.py` 里删掉 `call_model()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"把 prompt 发给模型、拿到纯文本回答"的过程。三个节点、`graph.py` 里的
路由逻辑（条件边+环+`MAX_REVISIONS`保护）都已经完整实现。
