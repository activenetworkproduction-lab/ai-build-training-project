"""【骨架阶段占位】把 sample-data/company.txt 逐句拆成三元组，写入 Neo4j。

用法（细化阶段实现 extraction.extract_triples 之后）：
    python src/ingest.py

TODO(细化阶段)：
    1. 读取 sample-data/company.txt，按行拆成一句句文本
    2. 对每一句调用 extraction.extract_triples() 得到三元组列表
    3. 用 Cypher 的 MERGE 写入图：两个 Entity 节点 + 一条带 type 属性的关系边

        MERGE (a:Entity {name: $subject})
        MERGE (b:Entity {name: $object})
        MERGE (a)-[:RELATED_TO {type: $relation}]->(b)

       用 MERGE 而不是 CREATE，是为了让同名实体自动复用同一个节点。
"""

from pathlib import Path

from db import get_driver
from extraction import extract_triples

SAMPLE_FILE = Path(__file__).parent.parent / "sample-data" / "company.txt"


def ingest() -> None:
    lines = [line.strip() for line in SAMPLE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

    driver = get_driver()
    try:
        with driver.session() as session:
            total = 0
            for line in lines:
                triples = extract_triples(line)  # TODO(细化阶段)：目前会抛 NotImplementedError
                for t in triples:
                    session.run(
                        """
                        MERGE (a:Entity {name: $subject})
                        MERGE (b:Entity {name: $object})
                        MERGE (a)-[:RELATED_TO {type: $relation}]->(b)
                        """,
                        subject=t["subject"],
                        relation=t["relation"],
                        object=t["object"],
                    )
                    total += 1
        print(f"导入完成，共写入 {total} 条关系")
    finally:
        driver.close()


if __name__ == "__main__":
    ingest()
