"""向量查询：找出和问题语义最相近的几条记录。

用法：
    python 03_vector/query_vector.py "什么是向量检索？"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db_postgres import get_connection
from common.embedding import embed_text


def search_vector(question: str, top_k: int = 5) -> list[dict]:
    """给 02_ai-rag/query_agentic.py 当工具函数用，返回结构化结果。"""
    vector = embed_text(question)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # %s::vector 是必须的：psycopg2 默认把 Python list 传成 numeric[]，
            # <=> 没有 vector <=> numeric[] 的重载，需要显式转成 vector 类型。
            cur.execute(
                "SELECT source, content, embedding <=> %s::vector AS distance "
                "FROM documents ORDER BY distance ASC LIMIT %s",
                (vector, top_k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {"source": source, "content": content, "distance": round(float(distance), 4)}
        for source, content, distance in rows
    ]


def query_vector(question: str, top_k: int = 5) -> None:
    results = search_vector(question, top_k)
    print(f"问题：{question}\n")
    for i, r in enumerate(results, start=1):
        print(f"{i}. [{r['source']}] [距离 {r['distance']}] {r['content']}")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "什么是向量检索？"
    query_vector(query)
