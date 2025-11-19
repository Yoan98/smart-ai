from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """Shared state for the LangGraph StateGraph.

    - user_input: 原始用户输入
    - plan: 规划器输出的计划（JSON 字典）
    - tool_results: 每个工具运行的结果列表（按步骤顺序）
    - final_output: 汇总后的最终响应
    """

    user_input: str
    plan: Optional[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    final_output: Optional[str]