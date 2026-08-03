# 05 · Agent Harness（教学项目）

通用的 Agent 架构模式样例，不绑定任何具体业务场景。演示让单个 agent 节点足够可靠的
六个组件：工具注册、上下文管理、权限确认、状态记录、失败重试、结果评估。

参照 [Graph Engineering Guide (2026)](https://www.aibuilderclub.com/blog/graph-engineering-guide-2026)
的说法，一个完整的 agent 技术栈从下到上是 `Prompt → Context → Harness → Loop → Graph`；
Harness 就是让 [06_loop](../06_loop) 那个循环里每一步都可靠、可控、可观测的那圈脚手架。

## 六个组件

| 文件 | 组件 | 作用 |
|---|---|---|
| `tools.py` | 工具注册 | 每个工具 = 一个函数 + 一份 schema；区分只读工具（直接放行）和有副作用的工具 |
| `context.py` | 上下文管理 | 对话历史窗口裁剪，避免无限增长 |
| `permissions.py` | 权限确认 | 有副作用的操作（`send_notification`）需要确认，只读操作直接放行 |
| `state.py` | 状态记录 | 跨轮次的结构化数据，比如"上一次查询的结果" |
| `recovery.py` | 失败重试 | 指数退避重试瞬时性错误，但不重试"还没实现"这类编程错误 |
| `eval.py` | 结果评估 | 检查回答的基本质量（非空、够长）；不通过时 `harness.py` 会打回模型重新回答一次 |

## 当前状态

✅ 已用真实 Gemini 调用验证跑通，⏳ 核心的 `call_model()`（`harness.py` 里）课堂留白。
`trace_report.py`/`demo_edge_cases.py` 是纯展示/演示脚本，不涉及调用模型，不是课堂留白点。

## 实测效果

问"帮我算一下 (23+19)*3，然后查一下北京天气，最后给我发个通知说完成了"：

```
[Context] 用户输入加入对话历史
[Harness] 模型请求调用 calculate({'expression': '(23 + 19) * 3'})
  [State] last_calculate_result = 126
[Harness] 模型请求调用 get_weather({'city': '北京'})
  [State] last_get_weather_result = {...}
[Harness] 模型请求调用 send_notification(...)
  [Permissions] 自动批准敏感操作 send_notification(...)（演示模式）
  [通知已发送]（模拟）：...
[Eval] 评估最终回答质量… 结果：{'passed': True, 'issues': []}
```

三个工具依次触发，`send_notification` 还真实走通了权限确认流程（只读的
`calculate`/`get_weather` 直接放行，没有额外确认）。

## 运行

```bash
python 05_harness/main.py
python 05_harness/main.py "自定义问题"
```

也可以用根目录 `scripts/start-harness.ps1`。每次运行结束都会在
`05_harness/trace_visualization.html` 生成这次真实过程的可视化时间线（自动打开）。

## 调试：在哪里能看到 Agent 的决策/执行过程

想在调试器里打断点、单步观察 harness 六个组件具体做了什么，看这几个精确位置：

| 步骤 | 位置 | 说明 |
|---|---|---|
| 模型决策的调用点 | [`harness.py:35`](harness.py#L35)（`call_model()`，课堂留白，当前是占位报错） | 参考实现在文件第 105~129 行的注释块里 |
| 工具调用分发 | [`harness.py:89-97`](harness.py#L89-L97)（`for call in tool_calls:` 循环） | 模型决定调用哪个工具后，这里执行权限确认 → 调用工具 → 记录状态 |
| 评估打回重答 | [`harness.py:67-87`](harness.py#L67-L87)（`if result["passed"] or eval_retry_used:` 之后的分支） | 质量检查没通过时，在这里把一条"重新回答"的消息塞回对话历史，`continue` 到下一轮 |
| 上下文窗口裁剪 | [`context.py:18-23`](context.py#L18)（`_trim()`） | 历史消息超过 `max_messages` 时在这里裁剪 |
| 权限确认 | [`permissions.py:11-22`](permissions.py#L11)（`check_permission()`） | 敏感工具在这里被拦截，等待确认或自动批准 |
| 失败重试 | [`recovery.py:11-35`](recovery.py#L11)（`with_retry()` 装饰器） | 网络抖动等瞬时性错误在这里按指数退避重试 |

## 可视化：这次运行的完整执行轨迹

`common/trace.py`（05/06/07 共用）提供了一个轻量的记录器：六个组件原本的 `print()`
全部换成了 `record(kind, message)`——终端输出完全不变，只是同时多存一份结构化数据。
每次运行结束后，`trace_report.py` 会把这些记录渲染成一个单文件 HTML 时间线
（`trace_visualization.html`，数据直接内嵌，双击打开即可看），每条记录都同时带着
颜色徽标和文字标签（颜色只是辅助识别，不是唯一的区分手段），可以直观看到
"上下文 → 工具调用 → 权限确认 → 状态记录 → 失败重试 → 结果评估"这六类事件
交替发生的真实顺序。

## 边界情况演示：不需要 API Key 就能跑

`demo_edge_cases.py` 用固定的假函数替换掉真实模型调用，确定性地演示三个不容易用
真实模型稳定复现的场景，方便随时跑、方便下断点单步调试：

```bash
python 05_harness/demo_edge_cases.py
```

1. **失败重试**：一个"前两次失败、第三次成功"的假函数，验证 `recovery.py` 的指数退避重试确实生效
2. **评估打回重答**：模拟模型第一次给出过短的回答（没通过 `eval.py` 的质量检查），
   被打回后第二次给出合格回答——这是 `harness.py` 新加的行为：评估不通过不再是
   "打印一下就算了"，而是真的会驱动模型重新回答一次（只重试一次，避免死循环）
3. **权限拒绝**：模拟用户在确认提示里输入 "n"，验证敏感操作会被真的拒绝执行

## 课堂实操

在 `harness.py` 里删掉 `call_model()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"把 messages + tools 发给模型、拿到它的决策"的过程。

## 踩坑记录

1. 重试装饰器（`recovery.py`）一开始用裸 `except Exception`，会把"还没实现"的
   `NotImplementedError` 也当成瞬时性错误重试 2 次（浪费几秒）。已加判断：
   `NotImplementedError` 不是"重试几次可能会好"的错误，直接往上抛，只重试真正的
   网络抖动/限流类错误。
2. `eval.py` 判断质量的逻辑很简单（非空、够长），真实调用 Gemini 时几乎不会触发
   "不通过"分支，所以这条路径没法稳定地用真实 API 复现——`demo_edge_cases.py`
   用固定假函数代替真实调用来确定性验证这个分支，而不是反复调真实 API 赌运气。
