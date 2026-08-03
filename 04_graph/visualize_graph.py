"""图谱可视化 demo：把 Neo4j 里"实体-关系-实体"的三元组画成一张力导向的节点关系图。

用法（需要先跑过 ingest.py，图谱里要有数据）：
    python 04_graph/visualize_graph.py

做的事情：
    1. 从 Neo4j 读出所有 (实体, 关系, 实体) 三元组
    2. 生成一个单文件 HTML：数据直接内嵌进去，双击打开即可看，不需要额外起服务；
       节点位置由页面里手写的力导向布局算法（Fruchterman-Reingold 的简化版）实时算出来——
       节点之间互相"排斥"，有关系的节点之间用"弹簧"拉近，多轮迭代后自然形成一张
       疏密有致的关系图，这本身就是"文本怎么被结构化成图"的一种直观展示。

这一步本身不是"课堂留白"——它只是读取已经抽取好的三元组做展示，不涉及调用模型。
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.db_neo4j import get_driver

OUTPUT_FILE = Path(__file__).resolve().parent / "graph_visualization.html"


def fetch_triples() -> list[tuple[str, str, str]]:
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(
                "MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity) "
                "RETURN a.name AS a, r.type AS relation, b.name AS b"
            )
            return [(record["a"], record["relation"], record["b"]) for record in result]
    finally:
        driver.close()


def build_graph(triples: list[tuple[str, str, str]]) -> tuple[list[dict], list[dict]]:
    degree = Counter()
    for a, _, b in triples:
        degree[a] += 1
        degree[b] += 1

    names = sorted(degree, key=lambda n: -degree[n])
    index = {name: i for i, name in enumerate(names)}

    nodes = [{"id": i, "name": name, "degree": degree[name]} for i, name in enumerate(names)]
    edges = [
        {"source": index[a], "target": index[b], "label": relation}
        for a, relation, b in triples
    ]
    return nodes, edges


def build_html(nodes: list[dict], edges: list[dict]) -> str:
    nodes_json = json.dumps(nodes, ensure_ascii=False).replace("</", "<\\/")
    edges_json = json.dumps(edges, ensure_ascii=False).replace("</", "<\\/")
    total_nodes = len(nodes)
    total_edges = len(edges)
    top = nodes[0]["name"] if nodes else ""
    top_degree = nodes[0]["degree"] if nodes else 0

    return f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>图谱可视化 · 04_graph</title>
<style>
  .viz-root {{
    color-scheme: light;
    --surface-1:      #fcfcfb;
    --page-plane:     #f9f9f7;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --text-muted:     #898781;
    --gridline:       #e1e0d9;
    --border:         rgba(11,11,11,0.10);
    --node-fill:      #2a78d6;
    --node-fill-dim:  #c3c2b7;
    --edge-stroke:    #c3c2b7;
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
      --border:         rgba(255,255,255,0.10);
      --node-fill:      #3987e5;
      --node-fill-dim:  #383835;
      --edge-stroke:    #383835;
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
    --border:         rgba(255,255,255,0.10);
    --node-fill:      #3987e5;
    --node-fill-dim:  #383835;
    --edge-stroke:    #383835;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--page-plane); font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  .viz-root {{ max-width: 1040px; margin: 0 auto; padding: 24px 20px 40px; }}
  h1 {{ font-size: 18px; color: var(--text-primary); margin: 0 0 4px; }}
  p.intro {{ color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin: 0 0 4px; }}
  p.stat {{ color: var(--text-muted); font-size: 12px; margin: 0 0 16px; }}
  .toolbar {{ display: flex; gap: 8px; margin-bottom: 10px; }}
  .toolbar input {{
    flex: 1; font-size: 13px; padding: 7px 10px; border-radius: 6px;
    border: 1px solid var(--border); background: var(--surface-1); color: var(--text-primary);
    font-family: inherit;
  }}
  .toolbar button {{
    font-size: 12px; padding: 7px 12px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--surface-1); color: var(--text-primary); cursor: pointer; font-family: inherit;
  }}
  .layout {{ display: flex; gap: 14px; align-items: flex-start; }}
  .chart-card {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 8px;
    padding: 8px; flex: 1; min-width: 0; position: relative;
  }}
  canvas {{ display: block; width: 100%; height: 560px; border-radius: 6px; cursor: grab; }}
  .side-card {{
    width: 260px; flex: none; background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px; font-size: 12px; color: var(--text-primary);
    max-height: 560px; overflow-y: auto;
  }}
  .side-card h2 {{ font-size: 13px; margin: 0 0 8px; }}
  .side-card .hint {{ color: var(--text-muted); }}
  .side-card ul {{ margin: 8px 0 0; padding-left: 16px; }}
  .side-card li {{ margin-bottom: 6px; line-height: 1.5; }}
  .tooltip {{
    position: absolute; pointer-events: none; z-index: 10;
    background: var(--text-primary); color: var(--surface-1);
    font-size: 12px; padding: 5px 9px; border-radius: 6px; opacity: 0; transition: opacity 100ms ease;
  }}
</style>
</head>
<body>
<div class="viz-root">
  <h1>图谱可视化：文本怎么被拆成"实体-关系-实体"网络</h1>
  <p class="intro">
    每条新闻先被 <code>extract_triples()</code> 拆成若干条 (主体, 关系, 客体) 三元组存进 Neo4j，
    下面这张图把所有三元组连起来：每个圆点是一个实体，节点越大代表它和越多实体有关系；
    每条线是一条关系，鼠标悬停能看到具体关系名。节点位置由页面里手写的
    <b>力导向布局算法</b>实时计算——节点互相排斥、有连接的节点互相拉近，可以拖动节点，
    也可以在上面搜索框输入实体名快速定位。
  </p>
  <p class="stat">共 {total_nodes} 个实体 · {total_edges} 条关系 · 连接最多的实体是「{top}」（{top_degree} 条关系）</p>
  <div class="toolbar">
    <input id="search" type="text" placeholder="输入实体名回车定位，比如 阿里巴巴 / OpenAI / Qwen3.8-Max">
    <button id="reset">重新布局</button>
  </div>
  <div class="layout">
    <div class="chart-card">
      <canvas id="canvas"></canvas>
      <div class="tooltip" id="tooltip"></div>
    </div>
    <div class="side-card" id="side">
      <h2>点击一个节点</h2>
      <p class="hint">查看它和哪些实体有关系</p>
    </div>
  </div>
</div>
<script>
const NODES = {nodes_json};
const EDGES = {edges_json};

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');
const sideCard = document.getElementById('side');

function cssVar(name) {{
  return getComputedStyle(document.querySelector('.viz-root')).getPropertyValue(name).trim();
}}

let W = 0, H = 0;
function resize() {{
  const rect = canvas.getBoundingClientRect();
  W = canvas.width = rect.width * devicePixelRatio;
  H = canvas.height = rect.height * devicePixelRatio;
}}
window.addEventListener('resize', resize);

// ---- 力导向布局（Fruchterman-Reingold 简化版） ----
// 思路：把每个节点当成互相排斥的电荷（离得越近推得越用力），
// 把每条边当成弹簧（把两端拉近到理想长度 k），每一轮迭代里
// 把两种力叠加算出节点的位移，再用一个逐渐降低的"温度"限制单次移动幅度，
// 迭代足够多轮之后节点会自然稳定在一个疏密合理的位置上。
const degreeMax = Math.max(1, ...NODES.map(n => n.degree));

// 模拟坐标系和屏幕像素完全独立——物理引擎在一个抽象坐标系里自由运动，
// 每一帧再通过下面的"自动取景"把当前所有节点的包围盒缩放/平移到画布可见范围内，
// 这样不管排斥力算出来的坐标多大/多分散，画面上永远能看到完整的图，不会有节点
// 被顶到边界卡住的问题。
const SIM_SIZE = 260 * Math.sqrt(Math.max(1, NODES.length));

function initPositions() {{
  NODES.forEach((n) => {{
    const angle = Math.random() * Math.PI * 2;
    const radius = Math.random() * SIM_SIZE * 0.5;
    n.x = Math.cos(angle) * radius;
    n.y = Math.sin(angle) * radius;
    n.fixed = false;
  }});
}}

let temperature = 1;
const K = SIM_SIZE / Math.sqrt(Math.max(1, NODES.length));

function step() {{
  for (const n of NODES) {{ n.fx = 0; n.fy = 0; }}

  for (let i = 0; i < NODES.length; i++) {{
    for (let j = i + 1; j < NODES.length; j++) {{
      const a = NODES[i], b = NODES[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      let dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const rep = (K * K) / dist;
      dx /= dist; dy /= dist;
      a.fx += dx * rep; a.fy += dy * rep;
      b.fx -= dx * rep; b.fy -= dy * rep;
    }}
  }}

  for (const e of EDGES) {{
    const a = NODES[e.source], b = NODES[e.target];
    let dx = a.x - b.x, dy = a.y - b.y;
    let dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const att = (dist * dist) / K;
    dx /= dist; dy /= dist;
    a.fx -= dx * att; a.fy -= dy * att;
    b.fx += dx * att; b.fy += dy * att;
  }}

  const maxDisp = K * 0.5 * temperature;
  for (const n of NODES) {{
    if (n.fixed) continue;
    const disp = Math.sqrt(n.fx * n.fx + n.fy * n.fy) || 0.01;
    const capped = Math.min(disp, maxDisp);
    n.x += (n.fx / disp) * capped;
    n.y += (n.fy / disp) * capped;
  }}
  temperature = Math.max(0.02, temperature * 0.99);
}}

// 当前这一帧的"模拟坐标 -> 屏幕像素"变换，由 draw() 每帧算出来，
// 鼠标事件（悬停/拖拽/命中测试）用它的逆变换换算回模拟坐标。
let view = {{ scale: 1, offX: 0, offY: 0 }};

function toScreen(x, y) {{
  return {{ x: x * view.scale + view.offX, y: y * view.scale + view.offY }};
}}
function toSim(px, py) {{
  return {{ x: (px - view.offX) / view.scale, y: (py - view.offY) / view.scale }};
}}

let hovered = null;
let selected = null;

function draw() {{
  ctx.clearRect(0, 0, W, H);
  const edgeStroke = cssVar('--edge-stroke');
  const nodeFill = cssVar('--node-fill');
  const nodeFillDim = cssVar('--node-fill-dim');
  const textPrimary = cssVar('--text-primary');

  const margin = 40 * devicePixelRatio;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const n of NODES) {{
    minX = Math.min(minX, n.x); maxX = Math.max(maxX, n.x);
    minY = Math.min(minY, n.y); maxY = Math.max(maxY, n.y);
  }}
  const boxW = Math.max(1, maxX - minX), boxH = Math.max(1, maxY - minY);
  const scale = Math.min((W - margin * 2) / boxW, (H - margin * 2) / boxH, 40);
  view = {{
    scale,
    offX: margin - minX * scale + Math.max(0, (W - margin * 2 - boxW * scale) / 2),
    offY: margin - minY * scale + Math.max(0, (H - margin * 2 - boxH * scale) / 2),
  }};

  const highlightSet = new Set();
  const focusNode = selected || hovered;
  if (focusNode) {{
    highlightSet.add(focusNode.id);
    EDGES.forEach((e) => {{
      if (e.source === focusNode.id) highlightSet.add(e.target);
      if (e.target === focusNode.id) highlightSet.add(e.source);
    }});
  }}

  ctx.lineWidth = 1 * devicePixelRatio;
  EDGES.forEach((e) => {{
    const a = toScreen(NODES[e.source].x, NODES[e.source].y);
    const b = toScreen(NODES[e.target].x, NODES[e.target].y);
    const dim = focusNode && !(highlightSet.has(e.source) && highlightSet.has(e.target));
    ctx.strokeStyle = edgeStroke;
    ctx.globalAlpha = dim ? 0.12 : 0.55;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }});
  ctx.globalAlpha = 1;

  NODES.forEach((n) => {{
    const p = toScreen(n.x, n.y);
    const r = (4 + 10 * (n.degree / degreeMax)) * devicePixelRatio;
    const dim = focusNode && !highlightSet.has(n.id);
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fillStyle = dim ? nodeFillDim : nodeFill;
    ctx.globalAlpha = dim ? 0.35 : 1;
    ctx.fill();
    ctx.globalAlpha = 1;

    if (!dim && (n.degree >= degreeMax * 0.4 || focusNode === n || highlightSet.has(n.id))) {{
      ctx.fillStyle = textPrimary;
      ctx.font = (11 * devicePixelRatio) + 'px system-ui, sans-serif';
      ctx.fillText(n.name, p.x + r + 4, p.y + 4 * devicePixelRatio);
    }}
  }});
}}

let running = true;
function loop() {{
  if (running && temperature > 0.03) step();
  draw();
  requestAnimationFrame(loop);
}}

function nodeAt(px, py) {{
  let best = null, bestDist = 18 * devicePixelRatio;
  for (const n of NODES) {{
    const p = toScreen(n.x, n.y);
    const r = (4 + 10 * (n.degree / degreeMax)) * devicePixelRatio;
    const d = Math.hypot(p.x - px, p.y - py) - r;
    if (d < bestDist) {{ bestDist = d; best = n; }}
  }}
  return best;
}}

function canvasPos(ev) {{
  const rect = canvas.getBoundingClientRect();
  return {{
    x: (ev.clientX - rect.left) * devicePixelRatio,
    y: (ev.clientY - rect.top) * devicePixelRatio,
  }};
}}

let dragging = null;
canvas.addEventListener('mousedown', (ev) => {{
  const p = canvasPos(ev);
  const n = nodeAt(p.x, p.y);
  if (n) {{ dragging = n; n.fixed = true; canvas.style.cursor = 'grabbing'; }}
}});
window.addEventListener('mouseup', () => {{
  if (dragging) {{ dragging.fixed = false; dragging = null; canvas.style.cursor = 'grab'; temperature = Math.max(temperature, 0.3); }}
}});
canvas.addEventListener('mousemove', (ev) => {{
  const p = canvasPos(ev);
  if (dragging) {{
    const sim = toSim(p.x, p.y);
    dragging.x = sim.x; dragging.y = sim.y;
    return;
  }}
  const n = nodeAt(p.x, p.y);
  hovered = n;
  if (n) {{
    tooltip.style.opacity = '1';
    const rect = canvas.getBoundingClientRect();
    tooltip.style.left = (p.x / devicePixelRatio) + 'px';
    tooltip.style.top = (p.y / devicePixelRatio - 24) + 'px';
    tooltip.textContent = n.name + '（' + n.degree + ' 条关系）';
  }} else {{
    tooltip.style.opacity = '0';
  }}
}});
canvas.addEventListener('click', (ev) => {{
  const p = canvasPos(ev);
  const n = nodeAt(p.x, p.y);
  selected = n;
  showSide(n);
}});

function showSide(n) {{
  if (!n) {{
    sideCard.innerHTML = '<h2>点击一个节点</h2><p class="hint">查看它和哪些实体有关系</p>';
    return;
  }}
  const rels = EDGES.filter(e => e.source === n.id || e.target === n.id).map((e) => {{
    if (e.source === n.id) {{
      return '→ [' + e.label + '] ' + NODES[e.target].name;
    }}
    return '← [' + e.label + '] ' + NODES[e.source].name;
  }});
  sideCard.innerHTML = '<h2>' + n.name + '</h2><p class="hint">' + rels.length + ' 条关系</p>' +
    '<ul>' + rels.map(r => '<li>' + r.replace(/</g, '&lt;') + '</li>').join('') + '</ul>';
}}

document.getElementById('reset').addEventListener('click', () => {{
  initPositions();
  temperature = 1;
  selected = null;
  showSide(null);
}});

document.getElementById('search').addEventListener('keydown', (ev) => {{
  if (ev.key !== 'Enter') return;
  const q = ev.target.value.trim();
  const n = NODES.find(n => n.name === q) || NODES.find(n => n.name.includes(q));
  if (n) {{
    selected = n;
    showSide(n);
  }}
}});

resize();
initPositions();
loop();
</script>
</body>
</html>
"""


def visualize() -> None:
    triples = fetch_triples()
    if not triples:
        print("图谱是空的，请先运行 04_graph/ingest.py 导入数据")
        return

    nodes, edges = build_graph(triples)
    html = build_html(nodes, edges)
    OUTPUT_FILE.write_text(html, encoding="utf-8")

    print(f"共 {len(nodes)} 个实体，{len(edges)} 条关系")
    print(f"已生成 {OUTPUT_FILE}，用浏览器打开即可查看")


if __name__ == "__main__":
    visualize()
