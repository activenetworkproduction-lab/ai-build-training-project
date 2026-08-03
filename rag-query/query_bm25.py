"""BM25 查询：基于关键词匹配和词频统计的经典检索算法，不需要模型。

用法：
    python rag-query/query_bm25.py "PostgreSQL 扩展"

实现说明：
    中文没有空格分词，严谨的做法要用 jieba 这类分词库，但为了让教学重点留在
    BM25 算法本身，这里用最简单的"按字符切分"（每个汉字当一个词）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rank_bm25 import BM25Okapi

from common.db_postgres import get_connection


def tokenize(text: str) -> list[str]:
    return list(text.strip())


def load_documents() -> list[tuple[str, str]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT source, content FROM documents")
            return cur.fetchall()
    finally:
        conn.close()


def search_bm25(question: str, top_k: int = 5) -> list[dict]:
    """给 rag-query/query_agentic.py 当工具函数用，返回结构化结果。"""
    docs = load_documents()
    corpus = [tokenize(content) for _, content in docs]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(tokenize(question))

    ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)[:top_k]
    return [
        {"source": source, "content": content, "score": round(float(score), 4)}
        for (source, content), score in ranked
    ]


def query_bm25(question: str, top_k: int = 5) -> None:
    results = search_bm25(question, top_k)
    print(f"问题：{question}\n")
    for i, r in enumerate(results, start=1):
        print(f"{i}. [{r['source']}] [得分 {r['score']}] {r['content']}")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "PostgreSQL 扩展"
    query_bm25(query)
