"""状态管理：harness 的第四个组成部分。

区别于 context（对话历史，给模型看的）：state 是 harness 自己攒的、跨轮次的
结构化数据，比如"上一次查询的结果""用户的偏好设置"，用来做展示、审计或者
后续逻辑判断，不一定要塞回给模型。
"""


class SessionState:
    def __init__(self):
        self.data: dict = {}

    def set(self, key: str, value) -> None:
        self.data[key] = value
        print(f"  [State] {key} = {value}")

    def get(self, key: str, default=None):
        return self.data.get(key, default)
