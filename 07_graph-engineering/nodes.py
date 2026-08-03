"""三个节点：研究员 → 写手 → 评论者。

每个节点职责单一，只干一件事，这是图编排和"一个万能 agent 自己想清楚全部步骤"
（也就是 Loop）最大的区别：这里是人为把工作拆成几个专业角色，各自的 prompt
互不干扰，出了问题也容易定位是哪个节点的锅。

三个节点共用同一个 call_model()（纯文本对话，不需要工具调用），
这是本文件唯一留白的部分。
"""

import os

from state import GraphState

MODEL = "gemini-3.5-flash"


def call_model(prompt: str) -> str:
    # TODO(课堂实操)：删掉下面这行占位报错，参考本文件底部注释掉的参考实现，
    # 自己实现"把 prompt 发给模型、拿到纯文本回答"的过程。
    raise NotImplementedError("call_model 将在课堂上现场实现，见本文件底部的说明")


def research_node(state: GraphState) -> GraphState:
    prompt = f"你是研究员。请针对主题「{state.topic}」，列出 3-5 条关键事实/要点，用简洁的列表形式。"
    state.research_notes = call_model(prompt)
    print(f"[Node: 研究员] 产出要点：\n{state.research_notes}\n")
    return state


def writer_node(state: GraphState) -> GraphState:
    if state.feedback:
        prompt = (
            f"你是写手。以下是关于「{state.topic}」的研究要点：\n{state.research_notes}\n\n"
            f"你之前写的草稿被评论者打回，反馈是：{state.feedback}\n"
            "请根据反馈修改，重新写一段 100~150 字的短文。"
        )
    else:
        prompt = (
            f"你是写手。以下是关于「{state.topic}」的研究要点：\n{state.research_notes}\n\n"
            "请基于这些要点写一段 100~150 字的短文介绍这个主题。"
        )
    state.draft = call_model(prompt)
    print(f"[Node: 写手] 第 {state.revision_count + 1} 版草稿：\n{state.draft}\n")
    return state


def critic_node(state: GraphState) -> tuple[GraphState, str]:
    prompt = (
        f"你是评论者。请审阅下面这段关于「{state.topic}」的短文草稿，判断是否合格"
        "（内容准确、逻辑清楚、长度合适）。\n"
        f"草稿：{state.draft}\n\n"
        "必须严格按以下格式输出，两行都要有：\n"
        "决定：APPROVE 或 REVISE\n"
        "反馈：<如果是 REVISE，具体说明哪里需要改进；如果是 APPROVE，写一句认可的话>"
    )
    response = call_model(prompt)
    decision, feedback = _parse_critic_response(response)
    state.feedback = feedback
    print(f"[Node: 评论者] 决定：{decision}，反馈：{feedback}\n")
    return state, decision


def _parse_critic_response(text: str) -> tuple[str, str]:
    """把评论者输出的一整段文字，按"决定："/"反馈："两个标题拆开。"""
    decision_idx = text.find("决定：")
    feedback_idx = text.find("反馈：")
    if decision_idx == -1 or feedback_idx == -1:
        # 模型没按格式输出时，保守处理成"需要修改"，避免把不确定的输出当成通过
        return "REVISE", f"（模型未按约定格式输出，原始输出：{text.strip()[:200]}）"

    decision_text = text[decision_idx + len("决定：") : feedback_idx].strip()
    feedback_text = text[feedback_idx + len("反馈：") :].strip()
    decision = "APPROVE" if "APPROVE" in decision_text.upper() else "REVISE"
    return decision, feedback_text


# ===== 参考实现（已用真实主题验证跑通，课堂上现场重写）=====
#
# 实测效果：主题"RAG（检索增强生成）"，评论者第一轮就给出 APPROVE，0 次修改就结束——
# 说明质量把关到位时图不一定要经过环路。换个主题"向量数据库"实测则真的触发了一次
# REVISE：评论者指出草稿把"向量数据库"和"嵌入模型"的职责搞混了（"向量数据库本身
# 不负责把数据转成向量，那是 embedding 模型的活，向量数据库只管存储和检索"），
# 写手看到这条反馈后改写，第二版就把这个区分讲清楚了，评论者才 APPROVE。
# MAX_REVISIONS 强制终止这个保护机制，另外用模拟的"永远要求修改"评论者单独测试过，
# 3 轮后正确停止，不会死循环。
#
# import requests
#
# def call_model(prompt: str) -> str:
#     api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         raise RuntimeError("缺少 GEMINI_API_KEY 环境变量，请在 .env 里配置")
#
#     response = requests.post(
#         "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
#         headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
#         json={"model": MODEL, "messages": [{"role": "user", "content": prompt}]},
#         timeout=30,
#     )
#     if not response.ok:
#         raise RuntimeError(f"调用模型失败（HTTP {response.status_code}）：{response.text[:500]}")
#     return response.json()["choices"][0]["message"]["content"]
#
# ===== 参考实现结束 =====
