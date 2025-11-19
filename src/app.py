from __future__ import annotations

import sys
from typing import Dict

from langgraph.graph import StateGraph, END

from core.graph.state import AgentState
from core.graph.nodes.planner import PlannerNode
from core.graph.nodes.executor import ToolExecutorNode
from core.graph.nodes.aggregator import FinalAggregatorNode
from core.llm.provider import get_llm_from_env
from core.tools.registry import ToolRegistry


def build_graph() -> StateGraph:
    registry = ToolRegistry()
    llm = get_llm_from_env()

    graph = StateGraph(AgentState)

    planner = PlannerNode(llm=llm, registry=registry)
    executor = ToolExecutorNode(registry=registry)
    aggregator = FinalAggregatorNode(llm=llm)

    graph.add_node("planner", planner)
    graph.add_node("executor", executor)
    graph.add_node("aggregator", aggregator)

    graph.set_entry_point("planner")

    def route_after_planner(state: AgentState) -> str:
        plan = state.get("plan") or {}
        steps = plan.get("steps", [])
        return "executor" if len(steps) > 0 else "aggregator"

    graph.add_conditional_edges("planner", route_after_planner)
    graph.add_edge("executor", "aggregator")
    graph.add_edge("aggregator", END)

    return graph


def run_once(user_input: str) -> Dict:
    compiled = build_graph().compile()
    initial: AgentState = {
        "user_input": user_input,
        "plan": None,
        "tool_results": [],
        "final_output": None,
    }
    return compiled.invoke(initial)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/app.py '<your task input>'")
        sys.exit(1)
    query = sys.argv[1]
    result = run_once(query)
    print("\n=== Final Output ===\n")
    print(result.get("final_output"))