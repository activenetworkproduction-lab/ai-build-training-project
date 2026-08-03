""""拆分"过程：把一段自然语言文本拆成 (实体, 关系, 实体) 三元组。

课堂实操说明：核心的 HTTP 调用逻辑已经注释掉——这部分已经用真实的 Gemini API
验证跑通过，注释内容就是验证通过的代码，课堂上会照着这个思路重新手写一遍。
用 sample-data/company.txt 里的一句话实测过效果：

    输入："李娜是启明科技的技术总监，向张伟汇报。"
    输出：[
        {"subject": "李娜", "relation": "就职公司", "object": "启明科技"},
        {"subject": "李娜", "relation": "担任职务", "object": "技术总监"},
        {"subject": "李娜", "relation": "汇报对象", "object": "张伟"}
    ]

思路：
    1. 把一句话和一个提示词（prompt）一起发给大模型，让它按固定格式（JSON）
       输出三元组
    2. 用普通的 HTTP 请求直接调用 Gemini 的 OpenAI 兼容 chat completions 接口
       （思路和 apps/server 里 ocr.service.ts 调用视觉模型完全一样，只是这里
       输入是纯文本，要求模型返回 JSON）
    3. 解析模型返回的 JSON（模型有时会用 ```json 代码块包一层，需要先去掉），
       得到三元组列表，交给 ingest.py 写入 Neo4j

这一步比向量 RAG 的"分块"更进一步：不只是切文本，而是从文本里"拆出"结构化的
实体和关系，这也是知识图谱能回答"A 和 B 是什么关系"这类问题的原因。
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


# ===== 参考实现（已用真实 Gemini API 验证跑通，课堂上现场重写）=====
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
#     # 模型有时会把 JSON 包在 ```json ... ``` 代码块里，先去掉再解析
#     if raw.startswith("```"):
#         raw = raw.strip("`")
#         raw = raw[4:] if raw.startswith("json") else raw
#     return json.loads(raw)
#
# ===== 参考实现结束 =====
