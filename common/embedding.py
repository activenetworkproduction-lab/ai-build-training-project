"""把一段文字变成一个向量（embedding）。

vector-ingest 用它给爬来的文档生成向量存入 Postgres；rag-query 的向量查询
用它给用户的问题生成向量，两边共用同一份实现，保证向量维度和语义空间一致。

思路：
    1. 拼一个 HTTP 请求，直接调用 embedding 接口（不用重型 SDK，方便看清楚
       请求体/响应体长什么样）：
       POST https://generativelanguage.googleapis.com/v1beta/models/
            gemini-embedding-001:embedContent?key=API_KEY
       body: {"model": "models/gemini-embedding-001",
              "content": {"parts": [{"text": "一段文字"}]},
              "outputDimensionality": 768}
       （gemini-embedding-001 默认输出 3072 维，用 outputDimensionality 截断成
        768 维，跟 docker/postgres-init/01-init.sql 里 documents.embedding
        的 VECTOR(768) 对应；注意更常见的旧模型名 text-embedding-004 已经下线了）
    2. 从响应 JSON 里取出那一串浮点数（就是这段文字的向量表示）
    3. 返回给调用方
"""

import os


def embed_text(text: str) -> list[float]:
    # TODO(课堂实操)：删掉下面这行占位报错，参考本文件底部注释掉的参考实现，
    # 自己实现「拼 HTTP 请求 → 调用 embedding 接口 → 取出向量」的过程。
    raise NotImplementedError("embed_text 将在课堂上现场实现，见本文件顶部的思路说明")


# ===== 参考实现（已用真实 Gemini API 验证跑通，返回 768 维向量，71 条爬虫段落全部导入成功，课堂上现场重写）=====
#
# import requests
#
# def embed_text(text: str) -> list[float]:
#     api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         raise RuntimeError("缺少 GEMINI_API_KEY 环境变量，请在 .env 里配置")
#
#     url = (
#         "https://generativelanguage.googleapis.com/v1beta/models/"
#         f"gemini-embedding-001:embedContent?key={api_key}"
#     )
#     response = requests.post(
#         url,
#         json={
#             "model": "models/gemini-embedding-001",
#             "content": {"parts": [{"text": text}]},
#             "outputDimensionality": 768,
#         },
#         timeout=30,
#     )
#     if not response.ok:
#         raise RuntimeError(f"embedding 请求失败（HTTP {response.status_code}）：{response.text[:500]}")
#     return response.json()["embedding"]["values"]
#
# ===== 参考实现结束 =====
