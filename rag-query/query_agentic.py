"""Agentic 查询：AI 自己决定"查几次、每次用什么方式查"，最后综合所有结果回答。

这是一个多轮迭代式 Agent（ReAct 风格），跟前面三种查询最大的不同是：
BM25/向量/图查询都是"人决定用哪种方式查一次"，而这里是"AI 自己决定"：
每一轮，模型可以选择调用 bm25_search / vector_search / graph_search 中的
一个工具，看到结果后再决定——继续换个方式查，还是已经够了可以直接回答。

用法：
    python rag-query/query_agentic.py "RAG 和向量数据库、图数据库分别是什么关系？"

【课堂实操说明】核心的"调用模型做决策"这一步（call_model 函数）已经注释掉了——
这部分已经用真实问题验证跑通过：问"RAG 和向量数据库、图数据库分别是什么关系？"，
模型自己规划了 4 轮工具调用（vector_search → graph_search → 又是 bm25_search
和 graph_search 各一次 → 再补一次 vector_search），第 4 轮才给出综合回答，
过程中自己判断"这个问题该换个方式再查一次"，这就是"多轮迭代式 Agent"和
"查一次就返回"的关键区别。课堂上会照着这个思路重新手写一遍。整个多轮循环、
工具分发、结果拼装的框架代码是完整的，唯一缺的就是"发请求给模型、拿到它的
决策"这一步。
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from query_bm25 import search_bm25
from query_graph import search_graph
from query_vector import search_vector

MAX_ROUNDS = 4
MODEL = "gemini-3.5-flash"

# 工具定义：格式和 OpenAI 的 function calling 一模一样，Gemini 的 OpenAI 兼容接口
# 也认这套格式。模型看到这份定义就知道"有哪些工具、每个工具要传什么参数"。
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bm25_search",
            "description": "关键词检索：适合问题里包含明确专有名词/关键词的情况",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": "语义相似度检索：适合问题是自然语言描述、没有明确关键词的情况",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "自然语言问题"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "graph_search",
            "description": "图查询：适合问“A 和 B 是什么关系”“某个实体关联了哪些其它实体”这类问题",
            "parameters": {
                "type": "object",
                "properties": {"entity": {"type": "string", "description": "实体名称，例如 RAG、PostgreSQL"}},
                "required": ["entity"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "你是一个 RAG 问答助手，可以调用工具查询知识库来回答用户问题。"
    "知识库内容是关于 RAG、向量数据库、图数据库、PostgreSQL 的维基百科片段。"
    f"你最多可以调用 {MAX_ROUNDS} 轮工具，觉得信息足够时就直接用文字回答，不要再调用工具。"
    "回答时要说明信息主要来自哪种查询方式（关键词/语义/图谱）。"
)


def dispatch_tool(name: str, arguments: dict) -> str:
    """真正执行某个工具，返回给模型看的文本结果。这部分是纯本地逻辑，不涉及模型调用。"""
    if name == "bm25_search":
        results = search_bm25(arguments["query"], top_k=3)
    elif name == "vector_search":
        results = search_vector(arguments["query"], top_k=3)
    elif name == "graph_search":
        results = search_graph(arguments["entity"])
    else:
        return f"未知工具：{name}"

    if not results:
        return "没有查到相关结果"
    return json.dumps(results, ensure_ascii=False)


def call_model(messages: list[dict]) -> dict:
    # TODO(课堂实操)：删掉下面这行占位报错，参考本文件底部注释掉的参考实现，
    # 自己实现"把 messages + TOOLS 发给模型，拿到它的决策（工具调用或最终回答）"的过程。
    raise NotImplementedError("call_model 将在课堂上现场实现，见本文件顶部的思路说明")


def query_agentic(question: str) -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for round_no in range(1, MAX_ROUNDS + 1):
        message = call_model(messages)
        messages.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            print(f"\n=== 第 {round_no} 轮：模型给出最终回答 ===")
            print(message.get("content", "（模型没有返回文字内容）"))
            return

        for call in tool_calls:
            fn_name = call["function"]["name"]
            fn_args = json.loads(call["function"]["arguments"])
            print(f"\n=== 第 {round_no} 轮：模型调用 {fn_name}({fn_args}) ===")

            result_text = dispatch_tool(fn_name, fn_args)
            print(f"工具返回：{result_text[:300]}...")

            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": result_text}
            )

    print(f"\n已达到最大轮数（{MAX_ROUNDS}），强制要求模型总结回答…")
    messages.append({"role": "user", "content": "请基于目前查到的信息直接给出最终回答，不要再调用工具。"})
    final = call_model(messages)
    print(final.get("content", "（模型没有返回文字内容）"))


# ===== 参考实现（已用真实问题验证跑通，课堂上现场重写）=====
#
# 实测效果：问"RAG 和向量数据库、图数据库分别是什么关系？"，
# 第 1 轮模型调用 vector_search 查语义相关内容，第 2 轮调用 graph_search(entity="RAG")
# 发现关系里有一条 "RAG -[最常见的实现方式是]-> 向量数据库"，第 3 轮又依次调用了
# bm25_search 和 graph_search(entity="图数据库") 补充图数据库的信息，第 4 轮再调用
# 一次 vector_search 确认知识图谱相关的表述，最后给出一段结构化的综合回答，
# 并且注明了每部分结论主要来自哪种查询方式。
#
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


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "RAG 和向量数据库、图数据库分别是什么关系？"
    query_agentic(q)
