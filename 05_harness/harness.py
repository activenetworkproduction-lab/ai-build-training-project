"""把 tools / context / permissions / state / recovery / eval 六个组件拼起来，
就是一个最小但完整的 Agent Harness。

harness 本身不是"一个多聪明的算法"，而是**围绕模型调用的一整圈基础设施**：
模型只负责"这一步该干什么"，其余的历史管理、要不要放行、状态记录、失败重试、
结果好不好都是 harness 的活。这也是为什么"Harness"和"Loop"经常被分开讨论——
Loop 是循环本身，Harness 是让循环里每一步都可靠、可控、可观测的那圈脚手架。

【课堂实操说明】唯一留白的是 call_model()——"把消息+工具定义发给模型，拿到它的
决策"这一步，已经用真实问题验证跑通（见文件底部注释），课堂上现场重写。
其余六个组件都是完整实现，可以直接读代码理解每个组件具体做了什么。
"""

import json

from context import ConversationContext
from eval import evaluate_response
from permissions import check_permission
from recovery import with_retry
from state import SessionState
from tools import call_tool, get_tool_schemas

from common.trace import record

MAX_ROUNDS = 5  # 留出比"3 个工具依次调用+最终回答"更多一点余量，给 eval 打回重答留出空间
MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = (
    "你是一个通用助手，可以调用工具：calculate（算术计算）、get_weather（查天气，模拟数据）、"
    "send_notification（发通知）。能用工具解决的问题就调用工具，不要凭空编造结果。"
    "所有工具都用完、信息足够了，再用文字给出最终回答。"
)


def call_model(messages: list[dict], tools: list[dict]) -> dict:
    # TODO(课堂实操)：删掉下面这行占位报错，参考本文件底部注释掉的参考实现，
    # 自己实现"把 messages + tools 发给模型，拿到它的决策"的过程。
    raise NotImplementedError("call_model 将在课堂上现场实现，见本文件顶部/底部的说明")


class AgentHarness:
    def __init__(self, auto_approve_sensitive: bool = False):
        self.context = ConversationContext(SYSTEM_PROMPT)
        self.state = SessionState()
        self.auto_approve_sensitive = auto_approve_sensitive

    @with_retry(max_attempts=3)
    def _call_model_with_recovery(self) -> dict:
        return call_model(self.context.messages, get_tool_schemas())

    def run_turn(self, user_message: str) -> str:
        record("context", f"[Context] 用户输入加入对话历史：{user_message}")
        self.context.add({"role": "user", "content": user_message})

        eval_retry_used = False
        for round_no in range(1, MAX_ROUNDS + 1):
            message = self._call_model_with_recovery()
            self.context.add(message)

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                final = message.get("content") or ""
                record("eval", "[Eval] 评估最终回答质量…")
                result = evaluate_response(user_message, final)
                record("eval", f"[Eval] 结果：{result}")

                if result["passed"] or eval_retry_used:
                    return final

                # 评估没通过：不是直接把不合格的回答扔给用户，而是打回模型重新回答一次——
                # 这才是"评估"这个组件真正的价值：不只是打分报告，还能驱动一次修正。
                # 只重试一次（eval_retry_used），避免"回答一直不合格"时无限循环。
                eval_retry_used = True
                record(
                    "eval",
                    f"[Eval] 质量不达标（{result['issues']}），打回模型重新回答一次",
                )
                self.context.add(
                    {
                        "role": "user",
                        "content": (
                            f"你上一条回答没有通过质量检查（{'；'.join(result['issues'])}），"
                            "请重新给出一个更完整的回答。"
                        ),
                    }
                )
                continue

            for call in tool_calls:
                name = call["function"]["name"]
                args = json.loads(call["function"]["arguments"])
                record("harness", f"\n[Harness] 第 {round_no} 轮：模型请求调用 {name}({args})")

                if not check_permission(name, args, auto_approve=self.auto_approve_sensitive):
                    result_text = "用户拒绝了这次操作"
                else:
                    result_text = str(call_tool(name, args))

                self.state.set(f"last_{name}_result", result_text)
                self.context.add({"role": "tool", "tool_call_id": call["id"], "content": result_text})

        return "（已达最大轮数，未能给出最终回答）"


# ===== 参考实现（已用真实问题验证跑通，课堂上现场重写）=====
#
# 实测效果：问"帮我算一下 (23 + 19) * 3，然后查一下北京天气，最后给我发个通知说完成了"，
# 模型依次调用 calculate → get_weather → send_notification 三个工具（send_notification
# 触发了 permissions.py 里的权限确认逻辑），最后给出总结所有结果的文字回答。
#
# import os
# import requests
#
# def call_model(messages: list[dict], tools: list[dict]) -> dict:
#     api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         raise RuntimeError("缺少 GEMINI_API_KEY 环境变量，请在 .env 里配置")
#
#     response = requests.post(
#         "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
#         headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
#         json={"model": MODEL, "messages": messages, "tools": tools},
#         timeout=30,
#     )
#     if not response.ok:
#         raise RuntimeError(f"调用模型失败（HTTP {response.status_code}）：{response.text[:500]}")
#     return response.json()["choices"][0]["message"]
#
# ===== 参考实现结束 =====
