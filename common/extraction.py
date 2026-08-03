""""拆分"过程：把一段自然语言文本拆成 (实体, 关系, 实体) 三元组。

graph-ingest 用它把爬来的文档拆成三元组写入 Neo4j。

思路：
    1. 把一句话和一个提示词（prompt）一起发给大模型，让它按固定格式（JSON）
       输出三元组
    2. 用普通的 HTTP 请求直接调用 Gemini 的 OpenAI 兼容 chat completions 接口
       （思路和 embedding.py、ocr 项目调用模型完全一样，只是这里输入是纯文本，
       要求模型返回 JSON）
    3. 解析模型返回的 JSON（模型有时会用 ```json 代码块包一层，需要先去掉），
       得到三元组列表，交给 ingest.py 写入 Neo4j
"""

from __future__ import annotations

from typing import TypedDict


class Triple(TypedDict):
    subject: str
    relation: str
    object: str


def extract_triples(text: str) -> list[Triple]:
    # TODO(课堂实操)：删掉下面这行占位报错，参考本文件底部注释掉的参考实现，
    # 自己实现「拼 prompt → 调用模型 → 解析 JSON」的过程。
    raise NotImplementedError("extract_triples 将在课堂上现场实现，见本文件顶部的思路说明")


# ===== 参考实现（已用真实 Gemini API 验证跑通，20 段爬虫文本共抽取出 194 条关系，课堂上现场重写）=====
#
# import json
# import os
# import requests
#
# PROMPT_TEMPLATE = (
#     "从下面这句话中抽取所有 (主体, 关系, 客体) 三元组，用于构建知识图谱。\n"
#     "严格输出一个 JSON 数组，不要输出任何多余的文字或 Markdown 代码块标记，\n"
#     '每个元素格式为 {{"subject": "...", "relation": "...", "object": "..."}}。\n'
#     "句子：{text}"
# )
#
# def extract_triples(text: str) -> list[Triple]:
#     api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         raise RuntimeError("缺少 GEMINI_API_KEY 环境变量，请在 .env 里配置")
#
#     response = requests.post(
#         "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
#         headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
#         json={
#             "model": "gemini-3.5-flash",
#             "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(text=text)}],
#         },
#         timeout=30,
#     )
#     if not response.ok:
#         raise RuntimeError(f"抽取三元组失败（HTTP {response.status_code}）：{response.text[:500]}")
#
#     raw = response.json()["choices"][0]["message"]["content"].strip()
#     if raw.startswith("```"):
#         raw = raw.strip("`")
#         raw = raw[4:] if raw.startswith("json") else raw
#     return json.loads(raw)
#
# ===== 参考实现结束 =====
