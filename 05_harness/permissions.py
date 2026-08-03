"""权限校验：harness 的第三个组成部分。

不是所有工具调用都应该无条件执行——只读操作（查天气、算数）可以直接放行，
但有副作用的操作（发通知、删文件、转账……）应该在执行前有一道"确认"关卡。
这和 Claude Code 自己的权限模型是一个思路：读操作静默执行，写/危险操作要询问。
"""

from common.trace import record

SENSITIVE_TOOLS = {"send_notification"}


def check_permission(tool_name: str, arguments: dict, auto_approve: bool = False) -> bool:
    if tool_name not in SENSITIVE_TOOLS:
        return True  # 只读工具，直接放行

    if auto_approve:
        record("permissions", f"  [Permissions] 自动批准敏感操作 {tool_name}({arguments})（演示模式，跳过人工确认）")
        return True

    answer = input(f"  [Permissions] Agent 想执行敏感操作 {tool_name}({arguments})，允许吗？[y/N] ")
    approved = answer.strip().lower() == "y"
    record("permissions", f"  [Permissions] 用户{'批准' if approved else '拒绝'}了这次操作")
    return approved
