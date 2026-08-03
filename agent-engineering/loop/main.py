"""运行一次通用 Agent Loop 演示。

用法：
    python agent-engineering/loop/main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from agent_loop import run_loop

if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "85美元的15%是多少？换算成欧元是多少？"
    answer = run_loop(question)
    print("\n=== 最终回答 ===")
    print(answer)
