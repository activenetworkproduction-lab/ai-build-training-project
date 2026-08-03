# 00 · 爬虫（共用的数据来源）

抓取中文维基百科上几个和本项目主题相关的词条（检索增强生成/向量数据库/图数据库/PostgreSQL），
产出到仓库根目录的 `data/raw/*.txt`，供 [03_vector](../03_vector) 和 [04_graph](../04_graph)
各自读取、独立处理（互不依赖，两边都能单独重新导入）。

不算在"7 个项目"里，是一个共用的前置步骤——选爬维基百科上关于 RAG/向量库/图数据库
本身的词条，是为了让最后的效果很应景：可以问系统"什么是 RAG"，答案就来自这里抓的内容。

## 当前状态：完整实现

纯 HTML 抓取解析，不涉及任何模型调用，不需要课堂留白。

## 运行

```bash
python 00_crawler/crawl.py
```

或 `powershell -File scripts/start-crawler.ps1`。

## 实现细节

- 用 `requests` + `BeautifulSoup` 抓取 `zh.wikipedia.org` 的词条页面，解析
  `#mw-content-text .mw-parser-output` 里的正文段落，去掉脚注标记（`[1]`）等干扰内容
- 带有辨识度的 `User-Agent`，遵守维基百科对爬虫的礼貌性要求（限速 1 秒/请求）
- 词条不存在时优雅跳过（打印提示，不中断整个爬取），实测 6 个目标词条里有 2 个
  （Neo4j、Okapi BM25）没有对应的中文维基页面，这是正常情况
