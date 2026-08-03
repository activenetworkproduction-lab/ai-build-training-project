"""把一段文字变成一个向量（embedding）。

课堂实操说明：核心的 HTTP 调用逻辑已经注释掉——这部分已经用真实的 Gemini API
验证跑通过（gemini-embedding-001 模型，返回 768 维向量），注释内容就是验证通过
的代码，课堂上会照着这个思路重新手写一遍。

思路：
    1. 拼一个 HTTP 请求，直接调用 embedding 接口（不用重型 SDK，方便看清楚
       请求体/响应体长什么样）：
       POST https://generativelanguage.googleapis.com/v1beta/models/
            gemini-embedding-001:embedContent?key=API_KEY
       body: {"model": "models/gemini-embedding-001",
              "content": {"parts": [{"text": "一段文字"}]},
              "outputDimensionality": 768}
       （gemini-embedding-001 默认输出 3072 维，用 outputDimensionality 截断成
        768 维，跟 init_db.py 里的 EMBEDDING_DIM 对应；注意 text-embedding-004
        这个更常见的旧模型名已经下线了，2026 年现在能用的是 gemini-embedding-001）
    2. 从响应 JSON 里取出那一串浮点数（就是这段文字的向量表示）
    3. 返回给调用方，后续要么存进数据库（ingest.py），要么跟查询文本的向量
       做相似度比较（query_vector.py）
"""


def embed_text(text: str) -> list[float]:
    # TODO(课堂实操)：删掉下面这行占位报错，参考本文件底部注释掉的参考实现，
    # 自己实现「拼 HTTP 请求 → 调用 embedding 接口 → 取出向量」的过程。
    raise NotImplementedError("embed_text 将在课堂上现场实现，见本文件顶部的思路说明")


# ===== 参考实现（已用真实 Gemini API 验证跑通，返回 768 维向量，课堂上现场重写）=====
#
# import os
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
