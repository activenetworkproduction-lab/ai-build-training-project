"""共享状态：沿着图的边在各个节点之间流动的对象。

每个节点都能读、能写，把独立的几次模型调用变成一个有记忆的系统——
写手节点能看到研究员产出的要点，评论者能看到写手的草稿，
写手被打回重写时又能看到评论者的反馈，全靠这个对象串起来。
"""

from dataclasses import dataclass


@dataclass
class GraphState:
    topic: str
    research_notes: str = ""
    draft: str = ""
    feedback: str = ""
    revision_count: int = 0
