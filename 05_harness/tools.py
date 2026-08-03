"""工具注册表：harness 的第一个组成部分。

每个工具 = 一个函数 + 一份描述它的 schema（模型看 schema 决定要不要调用、传什么参数）。
这里刻意放了三个"权限级别"不同的工具，方便下面 permissions.py 演示区别对待：
    - calculate / get_weather：只读，不产生副作用，可以直接放行
    - send_notification：会"发出去"东西（这里只是模拟打印），代表有副作用的操作，
      现实中类似"发邮件""删文件""转账"，需要额外的权限确认
"""

import ast
import operator

TOOL_REGISTRY: dict[str, dict] = {}


def register_tool(name: str, description: str, parameters: dict):
    def decorator(fn):
        TOOL_REGISTRY[name] = {
            "function": fn,
            "schema": {
                "type": "function",
                "function": {"name": name, "description": description, "parameters": parameters},
            },
        }
        return fn

    return decorator


def get_tool_schemas() -> list[dict]:
    return [entry["schema"] for entry in TOOL_REGISTRY.values()]


def call_tool(name: str, arguments: dict):
    if name not in TOOL_REGISTRY:
        raise ValueError(f"未知工具：{name}")
    return TOOL_REGISTRY[name]["function"](**arguments)


# 只允许这几种运算符，避免 eval() 能执行任意代码——这是"安全地执行看似需要 eval 的操作"的标准做法
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"不支持的表达式：{ast.dump(node)}")


@register_tool(
    "calculate",
    "计算一个算术表达式，支持加减乘除、括号、负数",
    {
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "例如 (23 + 19) * 3"}},
        "required": ["expression"],
    },
)
def calculate(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return _safe_eval(tree.body)


@register_tool(
    "get_weather",
    "查询某个城市的天气（演示用，返回固定的模拟数据，不是真实天气）",
    {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
)
def get_weather(city: str) -> dict:
    # 用城市名的哈希生成一个确定性的"假天气"，同一个城市每次查询结果一样，方便演示
    seed = sum(ord(c) for c in city)
    return {
        "city": city,
        "temperature_c": 10 + seed % 20,
        "condition": ["晴", "多云", "小雨", "阴"][seed % 4],
        "note": "这是模拟数据，不是真实天气",
    }


@register_tool(
    "send_notification",
    "发送一条通知（这里只是模拟，不会真的发送到任何地方）；这是一个有副作用的操作，需要权限确认",
    {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    },
)
def send_notification(message: str) -> str:
    print(f"  [通知已发送]（模拟）：{message}")
    return f"已发送通知：{message}"
