"""上下文管理：harness 的第二个组成部分。

对话历史（messages）会越攒越长，真实场景里必须做窗口裁剪，否则要么超出模型的
上下文长度限制，要么每次调用都要付费重新处理一大段历史。这里演示最简单的策略：
只保留 system prompt + 最近 N 条消息。
"""


class ConversationContext:
    def __init__(self, system_prompt: str, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]

    def add(self, message: dict) -> None:
        self.messages.append(message)
        self._trim()

    def _trim(self) -> None:
        # +1 是因为第 0 条 system prompt 不算在"最近 N 条"里
        if len(self.messages) > self.max_messages + 1:
            dropped = len(self.messages) - (self.max_messages + 1)
            self.messages = [self.messages[0]] + self.messages[-self.max_messages :]
            print(f"  [Context] 历史过长，裁掉了最早的 {dropped} 条消息")
