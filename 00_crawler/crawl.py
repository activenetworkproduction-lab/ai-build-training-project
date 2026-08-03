"""爬虫：抓取 AI News（https://ai-news.tayoru-kun.com/，用户自己设计的 AI 新闻网站）
的内容，产出到仓库根目录的 data/raw/*.txt，供 03_vector 和 04_graph 各自读取。

【学习要点】这个网站本身是一个纯前端 SPA（打开源码看，<body> 里只有一个空的
<div id="app">，内容全靠 JS 跑起来之后再拉数据），所以"爬"这个站不是解析 HTML，
而是要先找到它背后真正提供数据的接口。做法：打开浏览器开发者工具的网络面板，
或者直接看它加载的 JS 文件里有没有 fetch(...) 调用——在这个站的
assets/NewsView-*.js 里能翻到 `fetch(`${API}?days=60`)`，顺藤摸瓜就找到了
下面这个 API_BASE。这也是为什么它比爬维基百科更简单：目标网站自己提供了
结构化的 JSON，不需要用 BeautifulSoup 解析 HTML 标签。

用法：
    python 00_crawler/crawl.py [天数，默认 7]

产出：按新闻分类（tag）汇总，每个分类一个文件，一行一条新闻（标题+摘要）：
    data/raw/模型.txt
    data/raw/工具.txt
    data/raw/协议.txt
    data/raw/平台.txt
    data/raw/研究.txt
"""

import sys
from pathlib import Path

import requests

API_BASE = "https://daily-ai-news-collector-ipzxnrn3rq-an.a.run.app"

# API 返回的 tag 是英文 key，网站界面上显示的是这些中文名（抄自网站自己的
# assets/config-*.js 里的分类配置），文件名用中文名方便和其它爬虫产出保持风格一致
TAG_NAMES = {
    "model": "模型",
    "tool": "工具",
    "protocol": "协议",
    "platform": "平台",
    "research": "研究",
}

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
HEADERS = {"User-Agent": "TrainingProjectCrawler/0.1 (educational RAG demo; contact: none)"}


def fetch_news(days: int) -> list[dict]:
    """调用 API，把所有日期分组里的新闻条目拍平成一个列表。"""
    response = requests.get(f"{API_BASE}?days={days}", headers=HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()

    items = []
    for group in payload.get("data", []):
        items.extend(group.get("items", []))
    return items


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7

    print(f"抓取 AI News 最近 {days} 天的内容…")
    items = fetch_news(days)
    print(f"共获取到 {len(items)} 条新闻")

    # 按分类（tag）分组，一个分类写一个文件——这样图谱入库阶段沿用"每个文件只取
    # 前几行"的做法（见 04_graph/ingest.py 的 MAX_PARAGRAPHS_PER_FILE），控制模型
    # 调用次数的效果依然成立，不会因为新闻条数多就爆炸式增长
    by_tag: dict[str, list[dict]] = {}
    for item in items:
        by_tag.setdefault(item.get("tag", "其他"), []).append(item)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for tag, tag_items in by_tag.items():
        tag_name = TAG_NAMES.get(tag, tag)
        lines = []
        for item in tag_items:
            title = item.get("title", {}).get("zh", "").strip()
            summary = item.get("summary", {}).get("zh", "").strip()
            if not title and not summary:
                continue
            lines.append(f"{title}：{summary}")

        out_path = OUTPUT_DIR / f"{tag_name}.txt"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {tag_name}：{len(lines)} 条 → {out_path.relative_to(OUTPUT_DIR.parents[1])}")

    print(f"\n完成，共写入 {len(by_tag)} 个分类文件")


if __name__ == "__main__":
    main()
