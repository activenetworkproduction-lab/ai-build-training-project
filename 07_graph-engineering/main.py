"""运行一次图编排演示：研究员 → 写手 → 评论者。

用法：
    python agent-engineering/graph/main.py "RAG（检索增强生成）"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import visualize_flow
from graph import run_graph

from common import trace

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "RAG（检索增强生成）"
    trace.reset()
    final_state = run_graph(topic)

    print("=== 最终稿 ===")
    print(final_state.draft)
    print(f"\n（共修改 {final_state.revision_count} 次）")

    visualize_flow.render(
        topic, final_state.draft, final_state.revision_count,
        Path(__file__).resolve().parent / "trace_visualization.html",
    )
