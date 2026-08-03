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
`trace_report.py`/`demo_tool_error.py` 是纯展示/演示脚本，不涉及调用模型，不是课堂留白点。

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

也可以用根目录 `scripts/start-loop.ps1`。每次运行结束都会在
`06_loop/trace_visualization.html` 生成这次真实过程的可视化时间线（自动打开）。

## 调试：在哪里能看到 Agent 的决策/执行过程

| 步骤 | 位置 | 说明 |
|---|---|---|
| 模型决策的调用点 | [`agent_loop.py:30`](agent_loop.py#L30)（`call_model()`，课堂留白，当前是占位报错） | 参考实现在文件第 67~93 行的注释块里 |
| 工具调用分发（含错误处理） | [`agent_loop.py:51-62`](agent_loop.py#L51-L62)（`for call in tool_calls:` 循环） | `try/except` 包住 `dispatch()`——工具报错不会让循环崩溃，会变成一条工具"观察结果"传回模型 |
| 循环终止条件 | [`agent_loop.py:47-49`](agent_loop.py#L47)（`if not tool_calls:`） | 模型不再请求工具调用时，循环在这里结束并返回最终文字回答 |

## 可视化：这次运行的完整执行轨迹

和 [05_harness](../05_harness) 一样，用 `common/trace.py` 共用的记录器把每一轮的
决策/工具调用记下来，运行结束后 `trace_report.py` 渲染成 `trace_visualization.html`
（单文件，双击打开即可看）。

## 边界情况演示：工具报错不该让循环崩溃

之前 `dispatch()` 没有 `try/except`：如果模型传了一个工具处理不了的参数（比如
`convert_currency` 遇到不支持的币种），会直接抛出未捕获的异常，让整个循环崩溃。
现在改成把错误信息包装成这次工具调用的"观察结果"传回模型，模型可以自己决定怎么应对。

用真实 Gemini 复现（问一个真实存在但工具不支持的币种）：

```bash
python 06_loop/main.py "把100加元换算成欧元"
```

```
第 1 轮：调用 convert_currency({'amount': 100, 'from_currency': 'CAD', 'to_currency': 'EUR'}) 失败 → 不支持的币种，可选：['USD', 'EUR', 'CNY', 'JPY', 'GBP']
=== 第 2 轮：给出最终回答 ===
最终回答：抱歉，由于系统中的货币转换工具目前不支持加元（CAD）……
```

模型没有因为工具报错而卡死，而是如实告诉用户哪些币种支持。也可以用固定假函数
确定性复现这个过程（不需要 API Key，方便下断点单步调试）：

```bash
python 06_loop/demo_tool_error.py
```

## 课堂实操

在 `agent_loop.py` 里删掉 `call_model()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"把 messages + TOOLS 发给模型、拿到它的决策"的过程。循环本身（`for` 循环 +
工具分发）已经完整实现。
