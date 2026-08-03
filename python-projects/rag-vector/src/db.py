"""数据库连接工具：读取 .env 里的 DATABASE_URL，返回一个 psycopg2 连接。

这部分是纯粹的基础设施代码（不是教学重点），骨架阶段就直接写完整。
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "缺少 DATABASE_URL 环境变量，请复制 .env.example 为 .env 并按需修改"
        )
    return psycopg2.connect(database_url)
