# Agent 工程模式：Harness / Loop / Graph（教学项目）

三个通用的 AI Agent 架构模式样例，不绑定任何具体业务场景（RAG 项目本身也是这些模式
的一个应用实例——`rag-query/query_agentic.py` 本质上就是一个"Loop"）。

参照 [Graph Engineering Guide (2026)](https://www.aibuilderclub.com/blog/graph-engineering-guide-2026)
的说法，一个完整的 agent 技术栈从下到上是：

```
Prompt → Context → Harness → Loop → Graph
```

- **Harness**：让单个 agent 节点足够可靠的那圈脚手架——工具、上下文、权限、状态、恢复、评估
- **Loop**：模型自己反复"决策 → 执行 → 观察"的循环，是"最小的图"（只有一个自己指向自己的节点）
- **Graph**：当一个循环不够用、需要拆成多个专业节点协作时，人为声明节点之间怎么路由

## 三个样例

| # | 位置 | 演示什么 | 状态 |
|---|---|---|---|
| Harness | `harness/` | 六大组件：工具注册、上下文裁剪、权限确认、状态记录、失败重试、结果评估 | ✅ 已验证跑通，核心 `call_model` 课堂留白 |
| Loop | `loop/` | 最基础的 ReAct 循环，两个工具（计算器+汇率转换），模型自己决定要串联几步 | ✅ 已验证跑通，核心 `call_model` 课堂留白 |
| Graph | `graph/` | 研究员→写手→评论者三节点，评论者可以打回写手重写（条件边+环），有最大修改次数保护 | ✅ 已验证跑通，核心 `call_model` 课堂留白 |

## 运行

```bash
python agent-engineering/harness/main.py
python agent-engineering/loop/main.py
python agent-engineering/graph/main.py "RAG（检索增强生成）"
```

也可以用根目录 `scripts/start-harness.ps1` / `start-loop.ps1` / `start-graph.ps1`。

## 三者的实测对比

**Harness**：问"帮我算一下 (23+19)*3，然后查一下北京天气，最后给我发个通知说完成了"，
可以清楚看到 `[Context]`/`[Permissions]`/`[State]`/`[Eval]` 几个组件依次介入——
尤其是 `send_notification` 触发了权限确认（其它两个只读工具直接放行）。

**Loop**：问"85美元的15%是多少？换算成欧元是多少？"，模型自己判断要先 `calculate`
再 `convert_currency`，两步之间没有任何人为编排，全靠模型自己规划。

**Graph**：给定主题后，评论者第一轮就 `APPROVE` 时 0 次修改直接结束；用一个"永远
要求修改"的模拟评论者单独测试过 REVISE 环路，3 轮后被 `MAX_REVISIONS` 正确拦停，
不会死循环——这是 Harness/Loop 里没有、只有 Graph 这种"多节点+环"结构才需要考虑的问题。

## 为什么三个样例都不做前端界面

参照你的要求："可以只有项目代码的实现，画面上稍微能看出来大概的意思就行"——
每个样例跑起来会在终端打印出每一步在做什么（哪个组件/节点被调用、传了什么参数、
拿到什么结果），足够看懂机制本身，不需要额外包一层 UI。
