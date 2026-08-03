"""BM25 查询：基于关键词匹配和词频统计的经典检索算法，不需要模型。

用法：
    python src/query_bm25.py "pgvector 扩展"

实现说明：
    BM25 需要先把文本"分词"才能统计词频。中文没有空格分词，严谨的做法要用
    jieba 这类分词库，但为了让教学重点留在 BM25 算法本身（而不是中文分词），
    这里用最简单的"按字符切分"（每个汉字当一个词），足够演示 BM25 对比向量检索
    的效果差异：搜索"pgvector 扩展"时，BM25 会因为原文明确出现"扩展"两个字而
    给出很高的分数，即使问题里没有直接提到"存储"这类近义表达。
"""

import sys
from pathlib import Path

from rank_bm25 import BM25Okapi

SAMPLE_FILE = Path(__file__).parent.parent / "sample-data" / "notes.txt"


def tokenize(text: str) -> list[str]:
    """按字符切分（含数字/字母时按原样保留连续片段），足够满足教学演示用途。"""
    return list(text.strip())


def query_bm25(question: str, top_k: int = 5) -> None:
    lines = [line.strip() for line in SAMPLE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    tokenized_corpus = [tokenize(line) for line in lines]

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenize(question))

    ranked = sorted(zip(lines, scores), key=lambda pair: pair[1], reverse=True)[:top_k]

    print(f"问题：{question}\n")
    for i, (content, score) in enumerate(ranked, start=1):
        print(f"{i}. [得分 {score:.4f}] {content}")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "pgvector 扩展"
    query_bm25(query)
