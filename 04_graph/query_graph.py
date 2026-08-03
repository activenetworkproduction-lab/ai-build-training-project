"""图查询：从某个实体出发，找到与它相关的其它实体。

用法：
    python 04_graph/query_graph.py "阿里巴巴"

思路：
    用 Cypher 查询和给定实体有直接关系（1 跳）的所有节点。用 startNode(r)/
    endNode(r) 而不是直接用 a/b：因为查询用的是无向模式 -[r]-（不关心关系
    方向，只要跟 a 有连接就匹配），如果直接 RETURN a.name AS from，显示的
    方向会固定成"从查询的实体出发"，掩盖了关系本身真实的方向。
    startNode(r)/endNode(r) 拿到的是关系本身存储时的真实方向。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db_neo4j import get_driver


def search_graph(entity_name: str) -> list[dict]:
    """给 02_ai-rag/query_agentic.py 当工具函数用，返回结构化结果。"""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (a:Entity {name: $name})-[r:RELATED_TO]-(b:Entity)
                RETURN startNode(r).name AS from_name, r.type AS relation, endNode(r).name AS to_name
                """,
                name=entity_name,
            )
            return [
                {"from": record["from_name"], "relation": record["relation"], "to": record["to_name"]}
                for record in result
            ]
    finally:
        driver.close()


def query_graph(entity_name: str) -> None:
    rows = search_graph(entity_name)
    if not rows:
        print(f"没有找到和“{entity_name}”相关的关系（检查实体名是否写对，或先跑 04_graph/ingest.py）")
        return

    print(f"和“{entity_name}”相关的关系：\n")
    for r in rows:
        print(f"  ({r['from']}) -[{r['relation']}]-> ({r['to']})")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "阿里巴巴"
    query_graph(name)
