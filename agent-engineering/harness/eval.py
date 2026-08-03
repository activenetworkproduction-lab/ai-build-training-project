"""评估：harness 的第六个组成部分。

不判断"回答得对不对"（那需要更复杂的评估体系或人工审查），只做最基本的质量检查：
回答是不是空的、是不是短到不像是认真回答了问题。真实项目里这一步可以换成
"用另一个模型当裁判""跑一组回归测试用例"等更严格的评估。
"""


def evaluate_response(user_question: str, final_answer: str) -> dict:
    issues = []
    if not final_answer or not final_answer.strip():
        issues.append("回答为空")
    elif len(final_answer.strip()) < 5:
        issues.append("回答过短，可能没有真正回答问题")

    return {"passed": len(issues) == 0, "issues": issues}
