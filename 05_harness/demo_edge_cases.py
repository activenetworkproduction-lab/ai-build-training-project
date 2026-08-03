"""三个边界情况的确定性演示：不需要 GEMINI_API_KEY，也不需要先实现课堂留白的
call_model()——全部用固定/模拟的假函数替换掉真实模型调用，方便随时跑、结果可复现。

用法：
    python 05_harness/demo_edge_cases.py

演示的三件事：
    1. 失败重试（recovery.py）：一个"前两次失败、第三次成功"的假函数，看指数退避重试生效
    2. 评估打回重答（harness.py 的 eval 门控逻辑）：模拟模型第一次给出过短的回答，
       没通过质量检查后被打回重新回答一次，第二次给出合格回答
    3. 权限拒绝（permissions.py）：模拟用户在确认提示里输入 "n"，敏感操作被拒绝执行

这三个场景在真实调用 Gemini 时都不容易稳定复现（真实模型很少给出过短回答、
也很少真的网络超时），所以用确定性的假函数演示，能保证每次运行结果一致。
"""

import builtins
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import harness as harness_module
import recovery
import trace_report
from harness import AgentHarness
from permissions import check_permission

from common import trace


def demo_recovery() -> None:
    print("\n===== 场景 1：失败重试（recovery.py）=====")
    attempts = {"count": 0}

    @recovery.with_retry(max_attempts=3, initial_backoff=0.2)
    def flaky_call() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ConnectionError(f"模拟网络抖动（第 {attempts['count']} 次调用）")
        return "调用成功"

    result = flaky_call()
    print(f"最终结果：{result}（共尝试 {attempts['count']} 次）")


def demo_eval_retry() -> None:
    print("\n===== 场景 2：评估不通过，打回模型重新回答（harness.py）=====")
    # 模拟模型：第一次给出一个过短的回答（会被 eval.py 判定不通过），
    # 第二次（被打回重答后）给出一个合格的回答
    responses = iter(
        [
            {"role": "assistant", "content": "嗯"},
            {"role": "assistant", "content": "关于这个问题，完整的回答是：结果为 42，计算过程已核实无误。"},
        ]
    )
    harness_module.call_model = lambda messages, tools: next(responses)

    h = AgentHarness()
    answer = h.run_turn("随便问一个不需要工具的问题")
    print(f"最终回答：{answer}")


def demo_permission_rejection() -> None:
    print("\n===== 场景 3：用户拒绝敏感操作（permissions.py）=====")
    original_input = builtins.input
    builtins.input = lambda prompt: (print(prompt + "n（模拟用户输入）"), "n")[1]
    try:
        approved = check_permission("send_notification", {"message": "测试通知"}, auto_approve=False)
    finally:
        builtins.input = original_input
    print(f"批准结果：{approved}")


if __name__ == "__main__":
    trace.reset()
    demo_recovery()
    demo_eval_retry()
    demo_permission_rejection()

    trace_report.render(
        question="（边界情况演示，非真实提问）",
        answer="（见上方三个场景各自的输出）",
        output_path=Path(__file__).resolve().parent / "trace_visualization.html",
    )
