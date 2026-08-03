# 00 · 爬虫（共用的数据来源）

抓取 [AI News](https://ai-news.tayoru-kun.com/)——一个自建的 AI 行业新闻聚合站——
最近几天的内容，按分类（模型/工具/协议/平台/研究）汇总到仓库根目录的
`data/raw/*.txt`，供 [03_vector](../03_vector) 和 [04_graph](../04_graph)
各自读取、独立处理（互不依赖，两边都能单独重新导入）。

不算在"7 个项目"里，是一个共用的前置步骤。选这个站是因为它内容新鲜、按分类
组织得很清楚，最后做出来的效果也很直观：可以问系统"最近有哪些AI模型发布"
"阿里巴巴和英伟达有什么相关新闻"，答案就来自这里抓的真实新闻。

## 当前状态：完整实现

纯 API 调用+JSON 解析，不涉及任何模型调用，不需要课堂留白。

## 运行

```bash
python 00_crawler/crawl.py [天数，默认 7]
```

或 `powershell -File scripts/start-crawler.ps1`。

## 学习要点：怎么找到 SPA 网站背后的数据接口

打开 https://ai-news.tayoru-kun.com/ 看网页源码（`curl` 直接看原始 HTML，
不要用浏览器渲染后的），会发现 `<body>` 里只有一个空的 `<div id="app">`——
这是一个纯前端单页应用（SPA），内容全靠 JavaScript 加载完之后再拉数据渲染出来。
所以"爬"这个站不能像爬维基百科那样直接解析 HTML 标签。

找接口的方法：看它加载了哪些 JS 文件，直接 `curl` 下来搜 `fetch(`：

```bash
curl -s https://ai-news.tayoru-kun.com/assets/NewsView-*.js | grep -o 'fetch([^)]*)'
# fetch(`${pe}?days=60`)
```

再看同一批 JS 里 `pe`（或者随便什么变量名）对应的接口地址是从哪个模块导入的
（这个站是从 `config-*.js` 里导出的），顺藤摸瓜就能拼出完整的接口：

```
https://daily-ai-news-collector-ipzxnrn3rq-an.a.run.app?days=7
```

这一步其实就是浏览器开发者工具里"网络"面板能直接看到的东西，这里选择翻 JS
源码是想让你看到"找接口"本身也可以是纯读代码的过程，不一定要靠工具。

## 返回数据长什么样

```json
{
  "status": "success",
  "data": [
    {
      "date": "2026-08-03-20",
      "items": [
        {
          "id": "2026-08-03-alibaba-qwen3-8-max-global-release",
          "tag": "model",
          "title": { "zh": "...", "en": "...", "ja": "..." },
          "summary": { "zh": "...", "en": "...", "ja": "..." },
          "source": "South China Morning Post",
          "url": "https://www.scmp.com/..."
        }
      ]
    }
  ]
}
```

结构清晰的多语言 JSON，不需要 BeautifulSoup 解析 HTML——这也是选它做爬虫
教学对象的原因之一：能直观对比"爬有 API 的站"和"爬纯 HTML 站"（比如上一版
用的维基百科）的差异。

## 为什么按分类汇总成 5 个文件，而不是一条新闻一个文件

`days=7` 大概能抓到 60 条新闻，如果每条新闻单独存一个文件，04_graph 那边
"每个文件只取前几行做实体抽取"（`MAX_PARAGRAPHS_PER_FILE`）这个控制模型调用
次数的机制就会失效——不管抓多少条新闻，每个文件都只取前几行，效果都一样可控。
按 model/tool/protocol/platform/research 五个分类汇总，正好是这个网站自己的
分类体系，语义上也更连贯。
