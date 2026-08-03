"""工具报错被送回模型这个边界情况的确定性演示：不需要 GEMINI_API_KEY，也不需要
先实现课堂留白的 call_model()——用一个固定的假函数模拟"模型先用了一个不支持的
币种，看到报错后换成正确参数重试"的过程，方便随时跑、结果可复现、方便下断点
单步调试。

背景：dispatch() 之前没有 try/except，任何工具报错（比如 convert_currency 遇到
不支持的币种）都会让整个循环崩溃。现在 dispatch() 的报错会变成一条工具"观察结果"
传回模型，模型可以自己决定怎么应对——这个脚本演示的就是这条路径。

用法：
    python 06_loop/demo_tool_error.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent_loop
import trace_report

from common import trace

# 模拟模型：第一次选了一个不支持的币种（CAD），dispatch() 会报错；
# 模型"看到"错误信息后，第二次换成支持的币种（USD）重新调用；
# 第三次工具都成功了，给出最终文字回答。
_responses = iter(
    [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "name": "convert_currency",
                        "arguments": '{"amount": 100, "from_currency": "CAD", "to_currency": "EUR"}',
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "2",
                    "function": {
                        "name": "convert_currency",
                        "arguments": '{"amount": 100, "from_currency": "USD", "to_currency": "EUR"}',
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": "加元（CAD）暂不支持，我改用美元（USD）为你估算：100 USD 约等于 92 EUR。",
        },
    ]
)
agent_loop.call_model = lambda messages: next(_responses)


if __name__ == "__main__":
    trace.reset()
    question = "把100加元换算成欧元（演示：先用不支持的币种触发工具报错）"
    answer = agent_loop.run_loop(question)

    print("\n=== 最终回答 ===")
    print(answer)
    assert "工具调用失败" not in answer, "工具报错不应该泄漏成最终回答，应该被模型消化掉"
    print("断言通过：工具报错被当作观察结果处理，循环没有崩溃。")

    trace_report.render(question, answer, Path(__file__).resolve().parent / "trace_visualization.html")
