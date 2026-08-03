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
| `eval.py` | 结果评估 | 检查回答的基本质量（非空、够长） |

## 当前状态

✅ 已用真实 Gemini 调用验证跑通，⏳ 核心的 `call_model()`（`harness.py` 里）课堂留白。

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

也可以用根目录 `scripts/start-harness.ps1`。

## 课堂实操

在 `harness.py` 里删掉 `call_model()` 的占位报错，参考文件底部注释掉的参考实现，
自己手写"把 messages + tools 发给模型、拿到它的决策"的过程。

## 踩坑记录

重试装饰器（`recovery.py`）一开始用裸 `except Exception`，会把"还没实现"的
`NotImplementedError` 也当成瞬时性错误重试 2 次（浪费几秒）。已加判断：
`NotImplementedError` 不是"重试几次可能会好"的错误，直接往上抛，只重试真正的
网络抖动/限流类错误。
