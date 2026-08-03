"""把这一次 loop 运行的过程渲染成可视化 HTML（调用 common/trace.py 的通用渲染器）。

这一步本身不涉及调用模型，不是课堂留白点。
"""

from pathlib import Path

from common.trace import events, render_timeline_html

KIND_LABELS = {"loop": "循环步骤"}
KIND_ORDER = ["loop"]


def render(question: str, answer: str, output_path: Path) -> None:
    recs = events()

    render_timeline_html(
        title="Agent Loop 执行轨迹 · 06_loop",
        intro=(
            "问题：" + question + "\n"
            "最终回答：" + answer + "\n"
            "这条时间线是模型自己反复“决策 → 执行 → 观察”的真实过程——"
            "每一轮它自己判断还要不要再调用一次工具，直到信息足够才给出文字回答。"
        ),
        stat=f"共 {len(recs)} 条记录",
        kind_labels=KIND_LABELS,
        kind_order=KIND_ORDER,
        output_path=output_path,
    )
    print(f"\n已生成 {output_path}，用浏览器打开即可查看这次运行的完整时间线")
