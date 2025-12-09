from langgraph.graph import StateGraph, START, END
from typing import Literal
from state import AgentState
from node import plan_node, executor_node


def after_plan(state: AgentState) -> Literal["executor", END]:
    outline = state.get("outline", [])
    if len(outline) == 0:
        return END
    return "executor"


def should_loop(state: AgentState) -> Literal["executor", END]:
    idx = state.get("current_index", 0)
    outline = state.get("outline", [])
    if idx < len(outline):
        return "executor"
    return END


workflow = StateGraph(AgentState)
workflow.add_node("plan", plan_node)
workflow.add_node("executor", executor_node)
workflow.add_edge(START, "plan")
workflow.add_conditional_edges("plan", after_plan)
workflow.add_conditional_edges("executor", should_loop)
app = workflow.compile()
