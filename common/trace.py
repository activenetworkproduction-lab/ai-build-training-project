"""执行轨迹记录器：05_harness / 06_loop / 07_graph-engineering 都用它记录"发生了什么"。

设计成"打印 + 记录"合一：用 record() 代替裸 print()，输出到终端的内容完全不变
（record 内部就是先 print），只是同时在一个模块级列表里多存一份结构化数据。
运行结束后可以调用 render_timeline_html() 把这次运行的完整过程导出成一个
可视化的 HTML 时间线（自动生成，不是课堂留白点，纯展示用）。

用模块级全局列表存"当前这一次运行"的事件，足够单进程命令行 demo 用——
这几个项目都是"跑一次、看一次结果"的教学脚本，不需要为了并发/多次运行
的场景（会需要更复杂的按 run id 隔离）增加复杂度。
"""

import json
from pathlib import Path

_events: list[dict] = []

# dataviz 技能校验过的分类配色，固定顺序（相邻两两对比在浅色/深色模式下都能通过校验）
_PALETTE = [
    {"light": "#2a78d6", "dark": "#3987e5"},  # blue
    {"light": "#eb6834", "dark": "#d95926"},  # orange
    {"light": "#1baf7a", "dark": "#199e70"},  # aqua
    {"light": "#eda100", "dark": "#c98500"},  # yellow
    {"light": "#e87ba4", "dark": "#d55181"},  # magenta
    {"light": "#008300", "dark": "#008300"},  # green
    {"light": "#4a3aa7", "dark": "#9085e9"},  # violet
    {"light": "#e34948", "dark": "#e66767"},  # red
]


def reset() -> None:
    """开始新的一次运行前调用，清空上一次的记录。"""
    _events.clear()


def record(kind: str, message: str) -> None:
    """代替 print()：正常打印到终端，同时记一条结构化事件，供之后渲染成时间线。"""
    print(message)
    _events.append({"kind": kind, "message": message})


def events() -> list[dict]:
    return list(_events)


def render_timeline_html(
    title: str,
    intro: str,
    stat: str,
    kind_labels: dict[str, str],
    kind_order: list[str],
    output_path: Path,
    extra_section_html: str = "",
) -> None:
    """把 events() 记录的过程渲染成一个单文件 HTML 时间线（数据内嵌，双击打开即可看）。

    kind_order 决定颜色的固定分配顺序（最多 8 种，对应 _PALETTE），kind_labels
    是每种 kind 对应的中文展示名（用于图例和徽标文字）——时间线里每一条都会
    同时显示颜色徽标和文字标签，颜色只是辅助识别，不是唯一的区分手段。
    """
    colors = {kind: _PALETTE[i % len(_PALETTE)] for i, kind in enumerate(kind_order)}
    data_json = json.dumps(events(), ensure_ascii=False).replace("</", "<\\/")
    labels_json = json.dumps(kind_labels, ensure_ascii=False)
    colors_json = json.dumps(colors, ensure_ascii=False)
    kind_order_json = json.dumps(kind_order, ensure_ascii=False)

    html = f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>{title}</title>
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
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--page-plane); font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  .viz-root {{ max-width: 860px; margin: 0 auto; padding: 24px 20px 40px; }}
  h1 {{ font-size: 18px; color: var(--text-primary); margin: 0 0 4px; }}
  h2 {{ font-size: 14px; color: var(--text-primary); margin: 24px 0 10px; }}
  p.intro {{ color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin: 0 0 4px; white-space: pre-line; }}
  p.stat {{ color: var(--text-muted); font-size: 12px; margin: 0 0 16px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }}
  .legend .chip {{
    display: flex; align-items: center; gap: 6px; border: 1px solid var(--border);
    border-radius: 999px; padding: 4px 10px 4px 8px; font-size: 12px; color: var(--text-primary);
  }}
  .legend .chip .swatch {{ width: 9px; height: 9px; border-radius: 50%; flex: none; }}
  .timeline {{ display: flex; flex-direction: column; gap: 6px; }}
  .event {{
    display: flex; gap: 10px; align-items: flex-start;
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 6px;
    padding: 8px 12px; font-size: 13px; color: var(--text-primary); line-height: 1.5;
  }}
  .event .bar {{ width: 3px; align-self: stretch; border-radius: 2px; flex: none; }}
  .event .idx {{ color: var(--text-muted); font-size: 11px; flex: none; width: 22px; text-align: right; }}
  .event .badge {{
    font-size: 11px; padding: 1px 7px; border-radius: 999px; flex: none;
    color: var(--surface-1); white-space: nowrap;
  }}
  .event .msg {{ white-space: pre-wrap; word-break: break-word; }}
</style>
</head>
<body>
<div class="viz-root">
  <h1>{title}</h1>
  <p class="intro">{intro}</p>
  <p class="stat">{stat}</p>
  {extra_section_html}
  <h2>执行时间线</h2>
  <div class="legend" id="legend"></div>
  <div class="timeline" id="timeline"></div>
</div>
<script>
const EVENTS = {data_json};
const LABELS = {labels_json};
const COLORS = {colors_json};
const KIND_ORDER = {kind_order_json};

function isDark() {{
  const attr = document.documentElement.getAttribute('data-theme');
  if (attr === 'dark') return true;
  if (attr === 'light') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}}
function colorFor(kind) {{
  const mode = isDark() ? 'dark' : 'light';
  const c = COLORS[kind];
  return c ? c[mode] : 'var(--text-muted)';
}}

const legend = document.getElementById('legend');
KIND_ORDER.forEach((kind) => {{
  const chip = document.createElement('div');
  chip.className = 'chip';
  const swatch = document.createElement('span');
  swatch.className = 'swatch';
  swatch.style.background = colorFor(kind);
  chip.appendChild(swatch);
  chip.appendChild(document.createTextNode(LABELS[kind] || kind));
  legend.appendChild(chip);
}});

const timeline = document.getElementById('timeline');
EVENTS.forEach((e, i) => {{
  const row = document.createElement('div');
  row.className = 'event';

  const bar = document.createElement('div');
  bar.className = 'bar';
  bar.style.background = colorFor(e.kind);
  row.appendChild(bar);

  const idx = document.createElement('div');
  idx.className = 'idx';
  idx.textContent = i + 1;
  row.appendChild(idx);

  const badge = document.createElement('span');
  badge.className = 'badge';
  badge.style.background = colorFor(e.kind);
  badge.textContent = LABELS[e.kind] || e.kind;
  row.appendChild(badge);

  const msg = document.createElement('div');
  msg.className = 'msg';
  msg.textContent = e.message;
  row.appendChild(msg);

  timeline.appendChild(row);
}});
</script>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
