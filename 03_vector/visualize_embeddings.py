"""embedding 可视化 demo：把 768 维向量投影到 2 维，直观看到"语义相近的新闻会聚在一起"。

用法（需要先跑过 ingest.py，documents 表里要有数据）：
    python 03_vector/visualize_embeddings.py

做的事情：
    1. 从 Postgres 读出所有 (source, content, embedding)
    2. 手写 PCA（主成分分析）把 768 维压到 2 维——用 numpy 的 SVD 实现，
       不依赖 scikit-learn，方便直接在这个文件里看清楚 PCA 到底在算什么
    3. 生成一个单文件 HTML（数据直接内嵌进去，双击打开即可看，不需要额外起服务）

这一步本身不是"课堂留白"——它只是读取已经算好的向量做展示，不涉及调用模型。
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db_postgres import get_connection

OUTPUT_FILE = Path(__file__).resolve().parent / "embeddings_visualization.html"

# 和各项目 README 里保持一致的分类顺序（爬虫按这个顺序汇总）
TAG_ORDER = ["模型", "工具", "协议", "平台", "研究"]

# dataviz 技能校验过的分类配色（浅色/深色两套，固定顺序，不循环取色）
TAG_COLORS = {
    "模型": {"light": "#2a78d6", "dark": "#3987e5"},
    "工具": {"light": "#eb6834", "dark": "#d95926"},
    "协议": {"light": "#1baf7a", "dark": "#199e70"},
    "平台": {"light": "#eda100", "dark": "#c98500"},
    "研究": {"light": "#e87ba4", "dark": "#d55181"},
}


def fetch_documents() -> list[tuple[str, str, list[float]]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT source, content, embedding FROM documents ORDER BY id")
            rows = cur.fetchall()
    finally:
        conn.close()
    return [(source, content, json.loads(embedding)) for source, content, embedding in rows]


def pca_2d(vectors: np.ndarray) -> tuple[np.ndarray, tuple[float, float]]:
    """手写 PCA：中心化 + SVD，取前两个主成分。

    SVD 分解 centered = U @ diag(S) @ Vt 之后，把数据投影到前两个主成分方向
    就是 centered @ Vt[:2].T（等价于 U[:, :2] * S[:2]）。S**2 / sum(S**2)
    就是每个主成分解释了多少方差——这是 PCA 降维"损失了多少信息"的量化指标。
    """
    centered = vectors - vectors.mean(axis=0)
    u, s, vt = np.linalg.svd(centered, full_matrices=False)
    projected = centered @ vt[:2].T
    explained_ratio = (s**2) / (s**2).sum()
    return projected, (float(explained_ratio[0]), float(explained_ratio[1]))


def build_html(points: list[dict], explained: tuple[float, float]) -> str:
    data_json = json.dumps(points, ensure_ascii=False).replace("</", "<\\/")
    colors_json = json.dumps(TAG_COLORS, ensure_ascii=False)
    tag_order_json = json.dumps(TAG_ORDER, ensure_ascii=False)
    pc1_pct = round(explained[0] * 100, 1)
    pc2_pct = round(explained[1] * 100, 1)
    total = len(points)

    return f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>embedding 可视化 · 03_vector</title>
<style>
  .viz-root {{
    color-scheme: light;
    --surface-1:      #fcfcfb;
    --page-plane:     #f9f9f7;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --text-muted:     #898781;
    --gridline:       #e1e0d9;
    --baseline:       #c3c2b7;
    --border:         rgba(11,11,11,0.10);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) .viz-root {{
      color-scheme: dark;
      --surface-1:      #1a1a19;
      --page-plane:     #0d0d0d;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted:     #898781;
      --gridline:       #2c2c2a;
      --baseline:       #383835;
      --border:         rgba(255,255,255,0.10);
    }}
  }}
  :root[data-theme="dark"] .viz-root {{
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --page-plane:     #0d0d0d;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --gridline:       #2c2c2a;
    --baseline:       #383835;
    --border:         rgba(255,255,255,0.10);
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--page-plane); font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  .viz-root {{ max-width: 920px; margin: 0 auto; padding: 24px 20px 40px; }}
  h1 {{ font-size: 18px; color: var(--text-primary); margin: 0 0 4px; }}
  p.intro {{ color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin: 0 0 4px; }}
  p.stat {{ color: var(--text-muted); font-size: 12px; margin: 0 0 16px; }}
  .chart-card {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }}
  svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
  .gridline {{ stroke: var(--gridline); stroke-width: 1; }}
  .baseline {{ stroke: var(--baseline); stroke-width: 1; }}
  circle.pt {{
    stroke: var(--surface-1);
    stroke-width: 1.5px;
    cursor: pointer;
    transition: opacity 120ms ease, r 120ms ease;
  }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }}
  .legend button {{
    display: flex; align-items: center; gap: 6px;
    background: transparent; border: 1px solid var(--border);
    border-radius: 999px; padding: 5px 12px 5px 8px;
    font-size: 12px; color: var(--text-primary); cursor: pointer;
    font-family: inherit;
  }}
  .legend button.active {{ border-color: var(--text-primary); }}
  .legend button .swatch {{ width: 10px; height: 10px; border-radius: 50%; flex: none; }}
  .legend button.reset {{ color: var(--text-secondary); }}
  .tooltip {{
    position: absolute; pointer-events: none; z-index: 10;
    background: var(--text-primary); color: var(--surface-1);
    font-size: 12px; line-height: 1.5; padding: 8px 10px; border-radius: 6px;
    max-width: 320px; opacity: 0; transition: opacity 100ms ease;
  }}
  .chart-wrap {{ position: relative; }}
  details {{ margin-top: 16px; }}
  summary {{ font-size: 12px; color: var(--text-secondary); cursor: pointer; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
  th, td {{ text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--gridline); color: var(--text-primary); }}
  th {{ color: var(--text-muted); font-weight: 500; }}
</style>
</head>
<body>
<div class="viz-root">
  <h1>embedding 可视化：语义相近的新闻会聚在一起</h1>
  <p class="intro">
    每条新闻先被 <code>embed_text()</code> 转成一个 768 维的向量，人没法直接看懂 768 维空间，
    所以这里用 PCA（主成分分析）把它压缩到 2 维再画出来——两个点在图上离得越近，
    说明它们的原始向量在语义上越相似。点击下面的分类标签可以高亮某一类新闻，
    鼠标悬停在点上能看到具体内容。
  </p>
  <p class="stat">共 {total} 条新闻 · 前两个主成分共解释了原始 768 维里 {pc1_pct + pc2_pct}% 的方差
    （PC1 {pc1_pct}% + PC2 {pc2_pct}%，降到 2 维必然会损失一部分信息，这是 PCA 的正常取舍）</p>
  <div class="chart-card">
    <div class="chart-wrap">
      <svg id="chart" viewBox="0 0 800 520"></svg>
      <div class="tooltip" id="tooltip"></div>
    </div>
    <div class="legend" id="legend"></div>
  </div>
  <details>
    <summary>以表格形式查看全部数据点（无障碍 / 不方便看颜色时使用）</summary>
    <table id="table"><thead><tr><th>分类</th><th>内容</th></tr></thead><tbody></tbody></table>
  </details>
</div>
<script>
const DATA = {data_json};
const COLORS = {colors_json};
const TAG_ORDER = {tag_order_json};

const W = 800, H = 520, PAD = 36;
const xs = DATA.map(d => d.x), ys = DATA.map(d => d.y);
const xMin = Math.min(...xs), xMax = Math.max(...xs);
const yMin = Math.min(...ys), yMax = Math.max(...ys);
const xSpan = (xMax - xMin) || 1, ySpan = (yMax - yMin) || 1;

function sx(x) {{ return PAD + (x - xMin) / xSpan * (W - PAD * 2); }}
function sy(y) {{ return H - PAD - (y - yMin) / ySpan * (H - PAD * 2); }}

const isDark = () => {{
  const attr = document.documentElement.getAttribute('data-theme');
  if (attr === 'dark') return true;
  if (attr === 'light') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}};

function colorFor(tag) {{
  const mode = isDark() ? 'dark' : 'light';
  return COLORS[tag][mode];
}}

const svg = document.getElementById('chart');
const NS = 'http://www.w3.org/2000/svg';

function el(tag, attrs) {{
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}}

// 网格线（弱化处理，只是给视觉一个参照，坐标值本身没有实际业务含义）
for (let i = 1; i < 4; i++) {{
  const gx = PAD + (W - PAD * 2) * i / 4;
  svg.appendChild(el('line', {{ x1: gx, y1: PAD, x2: gx, y2: H - PAD, class: 'gridline' }}));
  const gy = PAD + (H - PAD * 2) * i / 4;
  svg.appendChild(el('line', {{ x1: PAD, y1: gy, x2: W - PAD, y2: gy, class: 'gridline' }}));
}}
svg.appendChild(el('line', {{ x1: PAD, y1: H - PAD, x2: W - PAD, y2: H - PAD, class: 'baseline' }}));
svg.appendChild(el('line', {{ x1: PAD, y1: PAD, x2: PAD, y2: H - PAD, class: 'baseline' }}));

const tooltip = document.getElementById('tooltip');
let activeTag = null;

const circles = DATA.map((d) => {{
  const c = el('circle', {{ class: 'pt', cx: sx(d.x), cy: sy(d.y), r: 6 }});
  c.addEventListener('mouseenter', (ev) => {{
    tooltip.style.opacity = '1';
    tooltip.innerHTML = '<b>[' + d.tag + ']</b><br>' + d.text;
    const rect = svg.getBoundingClientRect();
    const wrapRect = svg.parentElement.getBoundingClientRect();
    const scale = rect.width / W;
    tooltip.style.left = (sx(d.x) * scale) + 'px';
    tooltip.style.top = (sy(d.y) * scale - 10) + 'px';
  }});
  c.addEventListener('mouseleave', () => {{ tooltip.style.opacity = '0'; }});
  svg.appendChild(c);
  return {{ el: c, tag: d.tag }};
}});

function render() {{
  circles.forEach(({{ el, tag }}) => {{
    if (!activeTag) {{
      el.setAttribute('fill', 'var(--text-muted)');
      el.setAttribute('opacity', '0.55');
    }} else if (tag === activeTag) {{
      el.setAttribute('fill', colorFor(tag));
      el.setAttribute('opacity', '1');
    }} else {{
      el.setAttribute('fill', 'var(--gridline)');
      el.setAttribute('opacity', '0.35');
    }}
  }});
}}

const legend = document.getElementById('legend');
const resetBtn = document.createElement('button');
resetBtn.className = 'legend reset active';
resetBtn.textContent = '全部（未高亮）';
resetBtn.addEventListener('click', () => {{ activeTag = null; refreshLegend(); render(); }});
legend.appendChild(resetBtn);

const legendButtons = {{}};
TAG_ORDER.forEach((tag) => {{
  const count = DATA.filter(d => d.tag === tag).length;
  const btn = document.createElement('button');
  const swatch = document.createElement('span');
  swatch.className = 'swatch';
  swatch.style.background = colorFor(tag);
  btn.appendChild(swatch);
  btn.appendChild(document.createTextNode(tag + '（' + count + '）'));
  btn.addEventListener('click', () => {{ activeTag = tag; refreshLegend(); render(); }});
  legend.appendChild(btn);
  legendButtons[tag] = btn;
}});

function refreshLegend() {{
  resetBtn.classList.toggle('active', !activeTag);
  TAG_ORDER.forEach((tag) => {{
    legendButtons[tag].classList.toggle('active', activeTag === tag);
    legendButtons[tag].querySelector('.swatch').style.background = colorFor(tag);
  }});
}}

const tbody = document.querySelector('#table tbody');
DATA.forEach((d) => {{
  const tr = document.createElement('tr');
  tr.innerHTML = '<td>' + d.tag + '</td><td>' + d.text.replace(/</g, '&lt;') + '</td>';
  tbody.appendChild(tr);
}});

render();
</script>
</body>
</html>
"""


def visualize() -> None:
    rows = fetch_documents()
    if not rows:
        print("documents 表是空的，请先运行 03_vector/ingest.py 导入数据")
        return

    vectors = np.array([embedding for _, _, embedding in rows])
    projected, explained = pca_2d(vectors)

    points = [
        {"x": round(float(x), 4), "y": round(float(y), 4), "tag": source, "text": content}
        for (source, content, _), (x, y) in zip(rows, projected)
    ]

    html = build_html(points, explained)
    OUTPUT_FILE.write_text(html, encoding="utf-8")

    print(f"共 {len(points)} 条向量，PCA 前两个主成分解释了方差："
          f"PC1={explained[0]*100:.1f}% PC2={explained[1]*100:.1f}%")
    print(f"已生成 {OUTPUT_FILE}，用浏览器打开即可查看")


if __name__ == "__main__":
    visualize()
