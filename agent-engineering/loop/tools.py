"""两个互相独立的工具，刻意设计成"经常需要连续用两个才能回答问题"，
用来体现循环的价值——如果一次工具调用就能回答，那根本不需要循环。
"""

import ast
import operator

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


def calculate(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return _safe_eval(tree.body)


# 相对 USD 的固定汇率（演示用，不是实时汇率）
USD_RATES = {"USD": 1.0, "EUR": 0.92, "CNY": 7.20, "JPY": 149.5, "GBP": 0.79}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    if from_currency not in USD_RATES or to_currency not in USD_RATES:
        raise ValueError(f"不支持的币种，可选：{list(USD_RATES)}")
    usd = amount / USD_RATES[from_currency]
    return round(usd * USD_RATES[to_currency], 2)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算一个算术表达式，支持加减乘除、括号、负数",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "例如 85 * 0.15"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "把一个金额从一种货币转换成另一种（固定汇率，演示用，不是实时汇率）",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from_currency": {"type": "string", "description": "三位货币代码，例如 USD"},
                    "to_currency": {"type": "string", "description": "三位货币代码，例如 EUR"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
]


def dispatch(name: str, arguments: dict):
    if name == "calculate":
        return calculate(arguments["expression"])
    if name == "convert_currency":
        return convert_currency(arguments["amount"], arguments["from_currency"], arguments["to_currency"])
    raise ValueError(f"未知工具：{name}")
