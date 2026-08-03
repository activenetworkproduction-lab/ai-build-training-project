# 06 · Agent Loop（教学项目）

最基础、最通用的 Agent 架构模式：模型自己反复"决策 → 执行 → 观察"，不绑定任何
具体业务场景（对比 [02_ai-rag](../02_ai-rag) 的 Agentic 查询——那是 Loop 模式
在 RAG 场景下的一个应用实例）。

按 [Graph Engineering Guide (2026)](https://www.aibuilderclub.com/blog/graph-engineering-guide-2026)
的说法，"a single loop is the smallest possible graph"——一个循环就是只有一个
（会自己指向自己的）节点的图。

## 和 05_harness 的区别

刻意写得很"薄"，不像 [05_harness](../05_harness) 那样有权限/状态/恢复/评估——这是
有意的对比：Loop 只是"循环机制"本身，Harness 是让这个循环里每一步都可靠可控的
那圈脚手架。

## 两个工具

`tools.py` 里的 `calculate`（算术计算）和 `convert_currency`（货币转换，固定汇率）
刻意设计成"经常需要连续用两个才能回答问题"——如果一次工具调用就能回答，根本不需要循环。

## 当前状态

✅ 已用真实 Gemini 调用验证跑通，⏳ 核心的 `call_model()`（`agent_loop.py` 里）课堂留白。

## 实测效果

问"85美元的15%是多少？换算成欧元是多少？"：

```
第 1 轮：调用 calculate({'expression': '85 * 0.15'}) → 12.75
第 2 轮：调用 convert_currency({'amount': 12.75, 'from_currency': 'USD', 'to_currency': 'EUR'}) → 11.73
第 3 轮：给出最终回答——"85美元的15%是12.75美元，换算成欧元大约是11.73欧元"
```

一次工具调用不够用，模型自己决定"还要再调用一次、换个工具"——这就是"循环"存在的意义。

## 运行

```bash
python 06_loop/main.py
python 06_loop/main.py "自定义问题"
```

也可以用根目录 `scripts/start-loop.ps1`。

## 课堂实操

在 `agent_loop.py` 里删掉 `call_model()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"把 messages + TOOLS 发给模型、拿到它的决策"的过程。循环本身（`for` 循环 +
工具分发）已经完整实现。
