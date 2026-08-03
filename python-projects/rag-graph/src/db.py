"""Neo4j 连接工具：读取 .env 里的 NEO4J_URI/USER/PASSWORD，返回一个 driver。

这部分是纯粹的基础设施代码（不是教学重点），骨架阶段就直接写完整。
"""

import os

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

load_dotenv()


def get_driver() -> Driver:
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER")
    password = os.environ.get("NEO4J_PASSWORD")
    if not (uri and user and password):
        raise RuntimeError(
            "缺少 NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD 环境变量，"
            "请复制 .env.example 为 .env 并按需修改"
        )
    return GraphDatabase.driver(uri, auth=(user, password))
