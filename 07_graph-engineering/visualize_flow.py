"""把这一次图编排运行的"结构"和"实际走过的路径"画成一张 HTML：

上半部分是三个节点的静态流程图（研究员 → 写手 → 评论者，评论者 REVISE 时打回写手
形成环路，APPROVE 时才走向结束），边上标出这次真实运行里 REVISE 环路走了几次；
下半部分复用 common/trace.py 的时间线组件，能逐条看到每个节点具体产出了什么内容。

这一步本身不涉及调用模型，不是课堂留白点——纯粹是把 graph.py/nodes.py 已经在
打印的内容，多存一份结构化数据再画出来。
"""

from pathlib import Path

from common.trace import events, render_timeline_html

KIND_LABELS = {
    "edge": "边（路由）",
    "node_research": "研究员节点",
    "node_writer": "写手节点",
    "node_critic": "评论者节点",
}
KIND_ORDER = ["edge", "node_research", "node_writer", "node_critic"]


def _ended_by_approve(recs: list[dict]) -> bool:
    edge_events = [e for e in recs if e["kind"] == "edge"]
    return bool(edge_events) and "APPROVE" in edge_events[-1]["message"]


def _flow_diagram_html(revision_count: int, approved: bool) -> str:
    end_label = "APPROVE → 结束" if approved else "达到上限，强制结束"
    if revision_count:
        revise_label = f"REVISE ×{revision_count}（本次真实走过）"
        revise_opacity = "1"
    else:
        revise_label = "REVISE（本次未触发，评论者一次就通过了）"
        revise_opacity = "0.35"

    return f"""
  <h2>图结构：这次运行实际走过的路径</h2>
  <div class="chart-card" style="background:var(--surface-1);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:20px;">
    <svg viewBox="0 0 700 220" style="width:100%;height:auto;overflow:visible;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="var(--text-secondary)" />
        </marker>
      </defs>

      <rect x="20" y="40" width="130" height="56" rx="8" fill="none" stroke="var(--text-secondary)" stroke-width="1.5"/>
      <text x="85" y="73" text-anchor="middle" fill="var(--text-primary)" font-size="14">研究员</text>

      <rect x="275" y="40" width="130" height="56" rx="8" fill="none" stroke="var(--text-secondary)" stroke-width="1.5"/>
      <text x="340" y="73" text-anchor="middle" fill="var(--text-primary)" font-size="14">写手</text>

      <rect x="530" y="40" width="130" height="56" rx="8" fill="none" stroke="var(--text-secondary)" stroke-width="1.5"/>
      <text x="595" y="73" text-anchor="middle" fill="var(--text-primary)" font-size="14">评论者</text>

      <line x1="150" y1="68" x2="271" y2="68" stroke="var(--text-secondary)" stroke-width="2" marker-end="url(#arrow)"/>
      <line x1="405" y1="68" x2="526" y2="68" stroke="var(--text-secondary)" stroke-width="2" marker-end="url(#arrow)"/>

      <path d="M 560 96 C 560 165, 340 165, 340 100" fill="none" stroke="#eb6834" stroke-width="2.5"
            stroke-dasharray="6 4" opacity="{revise_opacity}" marker-end="url(#arrow)"/>
      <text x="450" y="190" text-anchor="middle" fill="var(--text-secondary)" font-size="12" opacity="{revise_opacity}">{revise_label}</text>

      <line x1="620" y1="96" x2="620" y2="140" stroke="var(--text-secondary)" stroke-width="2" marker-end="url(#arrow)"/>
      <text x="622" y="155" text-anchor="start" fill="var(--text-primary)" font-size="12">{end_label}</text>
    </svg>
  </div>
"""


def render(topic: str, final_draft: str, revision_count: int, output_path: Path) -> None:
    recs = events()
    approved = _ended_by_approve(recs)

    render_timeline_html(
        title="图编排执行轨迹 · 07_graph-engineering",
        intro=(
            "主题：" + topic + "\n"
            "最终稿：" + final_draft + "\n"
            "研究员 → 写手 → 评论者是人预先画好的固定路径，评论者说 REVISE 就一定打回写手、"
            "说 APPROVE 就一定结束——路径是声明式的，不是模型临场决定的（这是图编排和循环最大的区别）。"
        ),
        stat=f"共 {len(recs)} 条记录 · 修改了 {revision_count} 次 · {'评论者 APPROVE 通过' if approved else '因达到 MAX_REVISIONS 强制结束'}",
        kind_labels=KIND_LABELS,
        kind_order=KIND_ORDER,
        output_path=output_path,
        extra_section_html=_flow_diagram_html(revision_count, approved),
    )
    print(f"\n已生成 {output_path}，用浏览器打开即可查看这次运行的图结构 + 完整时间线")
