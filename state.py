from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages

# 这是整个图共享的数据结构


class AgentState(TypedDict):
    # add_messages 是一个特殊的 reducer，
    # 意味着新消息会追加到列表中，而不是覆盖旧列表
    messages: Annotated[list, add_messages]
    goal: str
    plan: List[str]
    step_index: int
    step_outputs: List[str]
