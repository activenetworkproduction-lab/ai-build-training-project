# 局域网数据库访问信息

本机（`anc-tarounoMini.anc.lan`，局域网 IP `192.168.20.174`）上运行着两套 Docker 数据库基础设施，均已开放局域网访问。局域网内的其他机器可直接使用以下信息连接。

> 密码为明文记录，仅限内网可信环境使用；如需变更密码，请联系本机维护者。

## 通用套件（独立于本项目）

| 服务 | 连接方式 |
|---|---|
| Postgres | `postgresql://shareduser:5RhM7sS17QOGcfTdEw1ffmn@192.168.20.174:5432/shareddb` |
| Neo4j Browser | http://192.168.20.174:7474 |
| Neo4j Bolt | `bolt://192.168.20.174:7687` |
| Neo4j 账号 | `neo4j` / `OnogdO9Cnn0iKcbLlz1QPgo` |

## 训练项目套件（本仓库 `docker/docker-compose.yml`）

| 服务 | 连接方式 |
|---|---|
| Postgres (pgvector) | `postgresql://rag:rag_password@192.168.20.174:5532/ragdb` |
| Neo4j Browser | http://192.168.20.174:7475 |
| Neo4j Bolt | `bolt://192.168.20.174:7688` |
| Neo4j 账号 | `neo4j` / `raggraph123` |
| pgAdmin | http://192.168.20.174:5050，账号 `admin@training-project.com` / `admin123` |

### 注意事项

- 训练项目的 Neo4j 若使用 Neo4j Browser 自动填充的连接地址，可能显示为内部端口 `7687`（与通用套件冲突），请手动改成 `bolt://192.168.20.174:7688`。Python 驱动使用 `bolt://` 协议直连不受此影响。
- 若要在其他局域网机器上运行本仓库的 Python 脚本，需要把该机器自己的 `.env` 中的 `localhost` 替换为 `192.168.20.174`。
- 本机 IP 为动态局域网地址，如主机重启或网络变化可能变更，请以维护者最新通知为准。
