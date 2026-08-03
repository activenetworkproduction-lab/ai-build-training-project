"""把这一次 harness 运行的过程渲染成可视化 HTML（调用 common/trace.py 的通用渲染器）。

这一步本身不涉及调用模型，不是课堂留白点——纯粹是把 harness 六个组件已经在打印的
内容，多存一份结构化数据再画出来。
"""

from pathlib import Path

from common.trace import events, render_timeline_html

KIND_LABELS = {
    "context": "上下文",
    "harness": "工具调用",
    "permissions": "权限确认",
    "state": "状态记录",
    "recovery": "失败重试",
    "eval": "结果评估",
}
KIND_ORDER = ["context", "harness", "permissions", "state", "recovery", "eval"]


def render(question: str, answer: str, output_path: Path) -> None:
    recs = events()
    kinds_used = sorted({e["kind"] for e in recs}, key=lambda k: KIND_ORDER.index(k) if k in KIND_ORDER else 99)
    counts = ", ".join(f"{KIND_LABELS.get(k, k)} {sum(1 for e in recs if e['kind'] == k)} 次" for k in kinds_used)

    render_timeline_html(
        title="Agent Harness 执行轨迹 · 05_harness",
        intro=(
            "问题：" + question + "\n"
            "最终回答：" + answer + "\n"
            "这条时间线是 harness 六个组件（工具调用/上下文/权限确认/状态记录/失败重试/结果评估）"
            "刚才真实发生的完整过程，颜色只是辅助识别——每条记录都带着文字标签，不靠颜色单独区分。"
        ),
        stat=f"共 {len(recs)} 条记录 · {counts}",
        kind_labels=KIND_LABELS,
        kind_order=KIND_ORDER,
        output_path=output_path,
    )
    print(f"\n已生成 {output_path}，用浏览器打开即可查看这次运行的完整时间线")
