"""最通用、最基础的 Agent Loop：感知 → 决策 → 执行 → 观察，循环往复。

刻意写得很"薄"，不像 harness 那样有权限/状态/恢复/评估——这是有意的对比：
Loop 只是"循环机制"本身（一个模型决策 + 工具执行的反复过程），
Harness 是让这个循环里每一步都可靠可控的那圈脚手架。
按 https://www.aibuilderclub.com/blog/graph-engineering-guide-2026 的说法，
"a single loop is the smallest possible graph"——一个循环就是只有一个
（会自己指向自己的）节点的图。

【课堂实操说明】唯一留白的是 call_model()，已用真实问题验证跑通（见文件底部
注释），课堂上现场重写。循环本身（下面的 for 循环 + 工具分发）是完整实现。
"""

import json

from tools import TOOLS, dispatch

from common.trace import record

MAX_ROUNDS = 5
MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = (
    "你可以调用两个工具：calculate（算术计算）和 convert_currency（货币转换，固定汇率）。"
    "有些问题需要连续调用两次工具才能算出来（比如先算出金额再换算货币），"
    "自己判断需要几步，都算完了再用文字给出最终答案。"
)


def call_model(messages: list[dict]) -> dict:
    # TODO(课堂实操)：删掉下面这行占位报错，参考本文件底部注释掉的参考实现，
    # 自己实现"把 messages + TOOLS 发给模型，拿到它的决策"的过程。
    raise NotImplementedError("call_model 将在课堂上现场实现，见本文件顶部/底部的说明")


def run_loop(question: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for round_no in range(1, MAX_ROUNDS + 1):
        message = call_model(messages)
        messages.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            record("loop", f"\n=== 第 {round_no} 轮：给出最终回答 ===")
            return message.get("content") or ""

        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            try:
                result = dispatch(name, args)
                record("loop", f"第 {round_no} 轮：调用 {name}({args}) → {result}")
            except Exception as err:
                # 工具报错不该让整个循环崩溃——把错误信息当成这次工具调用的"观察结果"
                # 传回给模型，让它自己决定怎么应对（换个参数重试、换个工具、或者向用户说明失败原因）
                result = f"工具调用失败：{err}"
                record("loop", f"第 {round_no} 轮：调用 {name}({args}) 失败 → {err}")
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": str(result)})

    return "（已达最大轮数，未能给出最终回答）"


# ===== 参考实现（已用真实问题验证跑通，课堂上现场重写）=====
#
# 实测效果：问"85美元的15%是多少？换算成欧元是多少？"，
# 第 1 轮调用 calculate("85 * 0.15") 得到 12.75，
# 第 2 轮调用 convert_currency(12.75, "USD", "EUR") 得到 11.73，
# 第 3 轮给出文字回答，把两步结果都讲清楚——这就是"循环"存在的意义：
# 一次工具调用不够用，模型自己决定"还要再调用一次、换个工具"。
#
# import os
# import requests
#
# def call_model(messages: list[dict]) -> dict:
#     api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         raise RuntimeError("缺少 GEMINI_API_KEY 环境变量，请在 .env 里配置")
#
#     response = requests.post(
#         "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
#         headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
#         json={"model": MODEL, "messages": messages, "tools": TOOLS},
#         timeout=30,
#     )
#     if not response.ok:
#         raise RuntimeError(f"调用模型失败（HTTP {response.status_code}）：{response.text[:500]}")
#     return response.json()["choices"][0]["message"]
#
# ===== 参考实现结束 =====
