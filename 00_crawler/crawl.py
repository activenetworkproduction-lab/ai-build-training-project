"""爬虫：抓取中文维基百科上几个和 RAG 技术相关的词条，作为后续 embedding/图谱的语料。

这是一个通用教学示例爬虫，不涉及任何具体业务数据，抓取内容是维基百科条目正文
（CC BY-SA 授权，允许非商业教学场景复用）。因为爬的正好是 RAG/向量库/图数据库
这些技术本身的词条，最后做出来的效果会很应景：可以问系统"什么是 RAG"、
"BM25 和向量检索有什么区别"，答案就来自这里抓的内容。

用法：
    python 00_crawler/crawl.py

产出：repo 根目录 data/raw/<词条名>.txt，每个文件是一个词条的正文段落
"""

import re
import time
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

# 目标词条：都是和本项目主题（向量检索/图数据库/RAG）相关的中文维基百科条目
TARGET_TITLES = [
    "检索增强生成",
    "向量数据库",
    "图数据库",
    "Neo4j",
    "PostgreSQL",
    "Okapi BM25",
]

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# 维基百科要求爬虫带上有辨识度的 User-Agent，说明身份和用途
HEADERS = {
    "User-Agent": "TrainingProjectCrawler/0.1 (educational RAG demo; contact: none)"
}

# 维基百科正文里常见的干扰内容：脚注标记 [1]、编辑按钮文字等，去掉让文本更干净
CITATION_PATTERN = re.compile(r"\[\d+\]")


def fetch_article(title: str) -> str | None:
    """抓取一个词条的正文段落，拼成一段纯文本。抓取失败（比如词条不存在）时返回 None。"""
    url = f"https://zh.wikipedia.org/wiki/{quote(title)}"
    response = requests.get(url, headers=HEADERS, timeout=15)
    if response.status_code == 404:
        print(f"  跳过「{title}」：词条不存在（404）")
        return None
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    content = soup.select_one("#mw-content-text .mw-parser-output")
    if not content:
        print(f"  跳过「{title}」：没找到正文容器，页面结构可能变了")
        return None

    paragraphs = []
    for p in content.find_all("p", recursive=True):
        # 跳过嵌套在信息框/导航框里的段落，只要顶层正文段落
        if p.find_parent(class_=["infobox", "navbox"]):
            continue
        text = CITATION_PATTERN.sub("", p.get_text()).strip()
        if len(text) > 10:  # 太短的多半是空段落或格式碎片，跳过
            paragraphs.append(text)

    return "\n".join(paragraphs)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0

    for title in TARGET_TITLES:
        print(f"抓取「{title}」…")
        try:
            text = fetch_article(title)
        except requests.RequestException as err:
            print(f"  失败：{err}")
            continue

        if not text:
            continue

        out_path = OUTPUT_DIR / f"{title}.txt"
        out_path.write_text(text, encoding="utf-8")
        print(f"  已保存 {len(text)} 字到 {out_path.relative_to(OUTPUT_DIR.parents[1])}")
        saved += 1

        time.sleep(1)  # 礼貌性限速，不给维基百科服务器添麻烦

    print(f"\n完成，共抓取 {saved}/{len(TARGET_TITLES)} 个词条")


if __name__ == "__main__":
    main()
