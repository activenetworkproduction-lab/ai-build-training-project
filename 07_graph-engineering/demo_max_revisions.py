"""复现 README 里提到的"评论者永远要求修改，MAX_REVISIONS 保护生效"这个边界情况。

之前这个场景只在 README 里描述过（"另外用一个模拟的'永远要求修改'评论者单独测试过"），
但不是仓库里能直接跑起来复现的脚本——这个文件把它变成一个真正可复现的 demo：
不需要 GEMINI_API_KEY，也不需要先实现课堂留白的 call_model()，用一个永远返回
REVISE 的假评论者，确定性地验证"环不会无限转下去"这件事。

用法：
    python 07_graph-engineering/demo_max_revisions.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import nodes
import visualize_flow
from graph import MAX_REVISIONS, run_graph

from common import trace

_call_count = 0


def fake_call_model(prompt: str) -> str:
    global _call_count
    _call_count += 1
    if "你是评论者" in prompt:
        return "决定：REVISE\n反馈：（演示用固定回复）永远不满意，用来验证 MAX_REVISIONS 保护"
    return f"（演示用固定草稿 #{_call_count}）这是一段占位内容，用来测试环路保护机制。"


nodes.call_model = fake_call_model

if __name__ == "__main__":
    trace.reset()
    final_state = run_graph("MAX_REVISIONS 边界测试（评论者永远不满意）")

    print("=== 最终稿 ===")
    print(final_state.draft)
    print(f"\n（共修改 {final_state.revision_count} 次，MAX_REVISIONS = {MAX_REVISIONS}）")
    assert final_state.revision_count == MAX_REVISIONS, "应该正好在 MAX_REVISIONS 次停止，没有无限循环"
    print("断言通过：环在 MAX_REVISIONS 次后正确停止，没有死循环。")

    visualize_flow.render(
        "MAX_REVISIONS 边界测试",
        final_state.draft,
        final_state.revision_count,
        Path(__file__).resolve().parent / "trace_visualization.html",
    )
