"""初始化数据库：启用 pgvector 扩展 + 建表。

用法：
    python src/init_db.py

这部分是基础设施代码，直接写完整；真正有教学价值的"embedding 手写演示"
在 src/embedding.py 里，那里的核心调用逻辑留给课堂现场实现。

EMBEDDING_DIM = 768，对应 Gemini gemini-embedding-001 模型（outputDimensionality=768）。
如果换用别的 embedding 模型/维度，改这里即可，注意要跟 src/embedding.py 里
实际请求的 outputDimensionality 保持一致。
"""

from db import get_connection

EMBEDDING_DIM = 768


def init_db() -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # pgvector 扩展提供 vector 类型和向量距离运算符（<-> 欧式距离、<=> 余弦距离等）
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding VECTOR({EMBEDDING_DIM})
                );
                """
            )
        conn.commit()
        print("数据库初始化完成：已启用 pgvector 扩展，已创建 notes 表")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
