"""向量查询：找出和问题语义最相近的几条记录。

用法：
    python src/query_vector.py "什么是向量检索？"

思路：
    1. 用 embedding.embed_text() 把用户的问题也变成一个向量
    2. 用 pgvector 的 <=> 运算符（余弦距离，越小越相似）做排序查询
    3. 打印结果，直观感受"语义相近"和"关键词相同"的区别（对比 query_bm25.py）——
       比如问"数据库怎么存向量"，即使原文没出现"存"这个字，也能查到 pgvector 那条。
"""

import sys

from db import get_connection
from embedding import embed_text


def query_vector(question: str, top_k: int = 5) -> None:
    query_vector_values = embed_text(question)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # <=> 是 pgvector 提供的余弦距离运算符，值越小表示越相似。
            # %s::vector 是必须的：psycopg2 默认把 Python list 传成 numeric[]，
            # <=> 没有 vector <=> numeric[] 的重载，需要显式转成 vector 类型。
            cur.execute(
                "SELECT content, embedding <=> %s::vector AS distance "
                "FROM notes ORDER BY distance ASC LIMIT %s",
                (query_vector_values, top_k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    print(f"问题：{question}\n")
    for i, (content, distance) in enumerate(rows, start=1):
        print(f"{i}. [距离 {distance:.4f}] {content}")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "什么是向量检索？"
    query_vector(query)
