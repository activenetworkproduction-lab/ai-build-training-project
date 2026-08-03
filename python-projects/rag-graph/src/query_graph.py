"""图查询：从某个实体出发，找到与它相关的其它实体。

用法：
    python src/query_graph.py "李娜"

思路：
    用 Cypher 查询和给定实体有直接关系（1 跳）的所有节点：

        MATCH (a:Entity {name: $name})-[r:RELATED_TO]-(b:Entity)
        RETURN startNode(r).name AS from, r.type AS relation, endNode(r).name AS to

    注意用 startNode(r)/endNode(r) 而不是直接用 a/b：因为查询用的是无向模式
    `-[r]-`（不关心关系方向，只要跟 a 有连接就匹配），如果直接 RETURN a.name AS from，
    显示的方向会固定成"从查询的实体出发"，掩盖了关系本身真实的方向（比如"王芳汇报给李娜"
    存的时候方向是 王芳→李娜，查李娜时如果只看 a/b 会被误显示成"李娜汇报给王芳"）。
    startNode(r)/endNode(r) 拿到的是关系本身存储时的真实方向，不受匹配模式影响。

    图查询回答的是"A 和 B 之间是什么关系、经过几步能连到一起"，
    而不是"哪段文字和问题最相似"——这是它和向量/BM25 查询的本质区别。
"""

import sys

from db import get_driver


def query_graph(entity_name: str) -> None:
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
            rows = [(record["from_name"], record["relation"], record["to_name"]) for record in result]
    finally:
        driver.close()

    if not rows:
        print(f"没有找到和 “{entity_name}” 相关的关系（检查实体名是否写对，或先跑 ingest.py 导入数据）")
        return

    print(f"和 “{entity_name}” 相关的关系：\n")
    for from_name, relation, to_name in rows:
        print(f"  ({from_name}) -[{relation}]-> ({to_name})")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "李娜"
    query_graph(name)
