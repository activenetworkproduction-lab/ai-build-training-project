"""把 data/raw/*.txt（爬虫产出）逐句拆成三元组，写入 Neo4j。

用法（common/extraction.py 里的 extract_triples 被课堂现场实现之后）：
    python 04_graph/ingest.py

为了控制模型调用次数（一句话一次调用），这里只挑每篇文章的前 N 段——
图谱抽取本身就是"简单导入样例"的定位，不需要处理全文。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db_neo4j import get_driver
from common.extraction import extract_triples

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
MAX_PARAGRAPHS_PER_FILE = 5  # 每篇文章只取前几段做实体抽取，控制模型调用次数


def ensure_constraint(driver) -> None:
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS "
            "FOR (n:Entity) REQUIRE n.name IS UNIQUE"
        )


def load_paragraphs() -> list[str]:
    if not RAW_DIR.exists():
        raise RuntimeError(f"找不到 {RAW_DIR}，请先运行 00_crawler/crawl.py")

    paragraphs = []
    for file in sorted(RAW_DIR.glob("*.txt")):
        lines = [line.strip() for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]
        paragraphs.extend(lines[:MAX_PARAGRAPHS_PER_FILE])
    return paragraphs


def ingest() -> None:
    paragraphs = load_paragraphs()
    if not paragraphs:
        print("没有可导入的内容，请先运行爬虫")
        return

    driver = get_driver()
    try:
        ensure_constraint(driver)

        total = 0
        with driver.session() as session:
            # 先清空，避免重复运行导致关系翻倍——教学场景下"可重复运行"更重要
            session.run("MATCH (n:Entity) DETACH DELETE n")

            for i, text in enumerate(paragraphs, start=1):
                try:
                    triples = extract_triples(text)
                except Exception as err:  # 单句抽取失败不影响其它句子
                    print(f"[{i}/{len(paragraphs)}] 抽取失败，跳过：{err}")
                    continue

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
                print(f"[{i}/{len(paragraphs)}] 抽取到 {len(triples)} 条关系：{text[:30]}...")

        print(f"\n导入完成，共写入 {total} 条关系")
    finally:
        driver.close()


if __name__ == "__main__":
    ingest()
