from langgraph.graph import StateGraph, START, END
from typing import Literal
from state import AgentState
from node import planner_node, agent_node, tool_node, post_exec_node, intent_node

# 这个函数用来决定下一步去哪里


def after_planner(state: AgentState) -> Literal["agent", END]:
    plan = state.get("plan", [])
    if len(plan) == 0:
        return END
    return "agent"


def agent_next(state: AgentState) -> Literal["tools", "post"]:
    messages = state['messages']
    last_message = messages[-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "post"


def loop_or_end(state: AgentState) -> Literal["agent", END]:
    idx = state.get("step_index", 0)
    plan = state.get("plan", [])
    if idx < len(plan):
        return "agent"
    return END


# 初始化图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("intent", intent_node)
workflow.add_node("planner", planner_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("post", post_exec_node)

# 添加边
# 1.以此开始
workflow.add_edge(START, "intent")
workflow.add_edge("intent", "planner")

# 2.agent 之后的条件跳转
workflow.add_conditional_edges("planner", after_planner)
workflow.add_conditional_edges("agent", agent_next)

# 3.工具执行完，必须回到 agent 再次思考（形成循环！）
workflow.add_edge("tools", "agent")
workflow.add_conditional_edges("post", loop_or_end)

# 编译图
app = workflow.compile()
