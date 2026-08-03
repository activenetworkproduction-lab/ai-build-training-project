"""把 data/raw/*.txt（爬虫产出）分段、生成 embedding，写入 Postgres 的 documents 表。

用法（common/embedding.py 里的 embed_text 被课堂现场实现之后）：
    python 03_vector/ingest.py

分块方式：爬虫已经按段落（自然换行）切好了，这里直接按行切分——每个段落
本身长度适中（几十到几百字），不需要再做更复杂的滑动窗口/重叠切分，
这也是"简单导入样例"这个定位该有的复杂度。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db_postgres import get_connection
from common.embedding import embed_text

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
MIN_CHUNK_LENGTH = 20  # 太短的段落大概率是格式碎片，跳过


def load_chunks() -> list[tuple[str, str]]:
    """返回 [(source, content), ...]，source 是来源文件名（不含扩展名）。"""
    if not RAW_DIR.exists():
        raise RuntimeError(f"找不到 {RAW_DIR}，请先运行 00_crawler/crawl.py")

    chunks = []
    for file in sorted(RAW_DIR.glob("*.txt")):
        source = file.stem
        for line in file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if len(line) >= MIN_CHUNK_LENGTH:
                chunks.append((source, line))
    return chunks


def ingest() -> None:
    chunks = load_chunks()
    if not chunks:
        print("没有可导入的内容，请先运行爬虫")
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 每次导入前清空，避免重复运行导致数据翻倍——教学场景下"可重复运行"比"增量导入"更重要
            cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
            for i, (source, content) in enumerate(chunks, start=1):
                vector = embed_text(content)
                cur.execute(
                    "INSERT INTO documents (source, content, embedding) VALUES (%s, %s, %s)",
                    (source, content, vector),
                )
                print(f"[{i}/{len(chunks)}] {source}: {content[:30]}...")
        conn.commit()
        print(f"\n导入完成，共 {len(chunks)} 条")
    finally:
        conn.close()


if __name__ == "__main__":
    ingest()
