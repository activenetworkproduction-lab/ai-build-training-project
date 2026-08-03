"""初始化图数据库：给 Entity 节点的 name 属性建唯一约束。

用法：
    python src/init_db.py

约束的作用：后面用 MERGE (n:Entity {name: $name}) 写入节点时，同名实体会自动
去重合并，而不是每次都新建一个重复节点——这对"从文本里反复抽取实体"的场景很重要。
"""

from db import get_driver


def init_db() -> None:
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS "
                "FOR (n:Entity) REQUIRE n.name IS UNIQUE"
            )
        print("图数据库初始化完成：已创建 Entity.name 唯一约束")
    finally:
        driver.close()


if __name__ == "__main__":
    init_db()
