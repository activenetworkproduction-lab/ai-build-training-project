-- 这个文件会在 Postgres 容器"第一次"初始化数据目录时自动执行一次
-- （docker-entrypoint-initdb.d 机制），不需要手动跑任何初始化脚本。
-- 如果卷已经初始化过（重启容器），这个文件不会重新执行——
-- 想重新跑一遍就删掉 pgdata 这个 volume（docker compose down -v）。

-- pgvector 扩展提供 vector 类型和向量距离运算符（<-> 欧式距离、<=> 余弦距离等）
CREATE EXTENSION IF NOT EXISTS vector;

-- 统一的文档表：vector-ingest 项目写入 embedding，rag-query 项目从这里读
-- source 字段记录这条内容来自哪个爬虫抓取的页面，方便溯源
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768)
);
