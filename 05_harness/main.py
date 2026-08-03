"""运行一次 harness 演示。

用法：
    python agent-engineering/harness/main.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import trace_report
from harness import AgentHarness

from common import trace

if __name__ == "__main__":
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "帮我算一下 (23 + 19) * 3，然后查一下北京天气，最后给我发个通知说完成了"
    )

    trace.reset()
    harness = AgentHarness(auto_approve_sensitive=True)
    answer = harness.run_turn(question)

    print("\n=== 最终回答 ===")
    print(answer)

    trace_report.render(question, answer, Path(__file__).resolve().parent / "trace_visualization.html")
