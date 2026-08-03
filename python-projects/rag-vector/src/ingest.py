"""【骨架阶段占位】把 sample-data/notes.txt 逐行导入数据库，并存下每一行的 embedding。

用法（细化阶段实现 embedding.embed_text 之后）：
    python src/ingest.py

TODO(细化阶段)：
    1. 读取 sample-data/notes.txt，按行切分成一条条 "文档"
       （真实场景里这一步通常叫"分块/chunking"，这份示例数据本身较短，直接按行切即可）
    2. 对每一行调用 embedding.embed_text() 得到向量
    3. 用 INSERT INTO notes (content, embedding) VALUES (%s, %s) 存进数据库
"""

from pathlib import Path

from db import get_connection
from embedding import embed_text

SAMPLE_FILE = Path(__file__).parent.parent / "sample-data" / "notes.txt"


def ingest() -> None:
    lines = [line.strip() for line in SAMPLE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for line in lines:
                vector = embed_text(line)  # TODO(细化阶段)：目前会抛 NotImplementedError
                cur.execute(
                    "INSERT INTO notes (content, embedding) VALUES (%s, %s)",
                    (line, vector),
                )
        conn.commit()
        print(f"导入完成，共 {len(lines)} 条")
    finally:
        conn.close()


if __name__ == "__main__":
    ingest()
