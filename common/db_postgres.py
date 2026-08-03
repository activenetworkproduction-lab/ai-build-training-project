"""Postgres 连接工具：读取仓库根目录 .env 里的 DATABASE_URL，返回一个 psycopg2 连接。

这部分是纯粹的基础设施代码（不是教学重点），直接写完整。
crawler / vector-ingest / rag-query 都从这里拿连接，保证连的是同一个数据库。
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# 无论从哪个子目录运行脚本，都加载仓库根目录下的 .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "缺少 DATABASE_URL 环境变量，请复制根目录的 .env.example 为 .env 并按需修改"
        )
    return psycopg2.connect(database_url)
