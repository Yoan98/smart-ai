import os

from src.app import build_graph
from core.graph.state import AgentState


def test_graph_runs_end_to_end():
    os.environ["LLM_PROVIDER"] = "mock"
    graph = build_graph()
    compiled = graph.compile()

    initial: AgentState = {
        "user_input": "为高中生设计一个关于牛顿第二定律的探究式学习任务",
        "plan": None,
        "tool_results": [],
        "final_output": None,
    }
    result = compiled.invoke(initial)

    assert result.get("plan") is not None
    assert isinstance(result.get("tool_results"), list)
    assert len(result.get("tool_results")) >= 1
    assert isinstance(result.get("final_output"), str)
    assert len(result.get("final_output")) > 0