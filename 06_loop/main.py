"""运行一次通用 Agent Loop 演示。

用法：
    python agent-engineering/loop/main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import trace_report
from agent_loop import run_loop

from common import trace

if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "85美元的15%是多少？换算成欧元是多少？"
    trace.reset()
    answer = run_loop(question)
    print("\n=== 最终回答 ===")
    print(answer)

    trace_report.render(question, answer, Path(__file__).resolve().parent / "trace_visualization.html")
