import os

from core.graph.nodes.planner import PlannerNode
from core.tools.registry import ToolRegistry
from core.llm.base import MockLLMAdapter


def test_planner_generates_plan_for_inquiry_learning():
    # Ensure tools are registered
    registry = ToolRegistry()
    llm = MockLLMAdapter()
    node = PlannerNode(llm=llm, registry=registry)

    state = {
        "user_input": "为高中生设计一个关于牛顿第二定律的探究式学习任务",
        "plan": None,
        "tool_results": [],
        "final_output": None,
    }

    updated = node(state)
    plan = updated["plan"]
    assert plan["objective"]
    step_names = [s["name"] for s in plan["steps"]]
    # Should include core tools for inquiry
    assert "search" in step_names
    assert "outline" in step_names
    assert "mindmap" in step_names