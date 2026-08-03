"""把三个节点用边连起来，组成一个图：

    研究员 ──→ 写手 ──→ 评论者
                 ↑           │
                 └── REVISE ─┘（条件边，构成一个环）
                          APPROVE → 结束（另一条条件边）

这就是"图编排"和"循环"的本质区别：循环是模型自己决定每一步做什么，
图是人预先画好节点之间怎么走——评论者说 REVISE 就一定回写手，说 APPROVE
就一定结束，路径是声明式的，不是模型临场决定的。

MAX_REVISIONS 是"失败隔离"的一种体现：环不能无限转下去，模型/prompt
如果有问题（评论者一直不满意）也不能让程序卡死或无限烧 token。
"""

from nodes import critic_node, research_node, writer_node
from state import GraphState

MAX_REVISIONS = 3


def run_graph(topic: str) -> GraphState:
    state = GraphState(topic=topic)

    print("[Edge] 开始 → 研究员节点")
    state = research_node(state)

    while True:
        print("[Edge] 研究员/写手 → 写手节点")
        state = writer_node(state)

        print("[Edge] 写手 → 评论者节点")
        state, decision = critic_node(state)

        if decision == "APPROVE":
            print("[Edge] 评论者：APPROVE → 结束")
            break

        state.revision_count += 1
        if state.revision_count >= MAX_REVISIONS:
            print(f"[Edge] 已达最大修改次数（{MAX_REVISIONS}），强制结束，避免无限循环")
            break

        print(f"[Edge] 评论者：REVISE → 打回写手节点（第 {state.revision_count} 次修改）")

    return state
