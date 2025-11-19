from __future__ import annotations

from typing import Any, Dict, List

from core.graph.state import AgentState
from core.llm.base import LLMAdapter, MockLLMAdapter


class FinalAggregatorNode:
    """Final Aggregator node.
    汇总工具输出并形成最终响应；若可用使用 LLM，总是提供离线回退。
    """

    def __init__(self, llm: LLMAdapter | None = None):
        self.llm = llm or MockLLMAdapter()

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        user_input = state["user_input"]
        results: List[Dict[str, Any]] = state.get("tool_results", [])

        # 尝试 LLM 汇总
        try:
            summary = self.llm.summarize(self._format_for_summary(user_input, results))
            if summary:
                return {"final_output": summary}
        except Exception:
            pass

        # 离线回退：纯规则的汇总
        return {"final_output": self._offline_aggregate(user_input, results)}

    # helpers
    def _format_for_summary(self, user_input: str, results: List[Dict[str, Any]]) -> str:
        lines = [f"UserInput: {user_input}", "ToolResults:"]
        for r in results:
            lines.append(f"- [{r.get('status')}] {r.get('name')}: {r.get('output')}")
        return "\n".join(lines)

    def _offline_aggregate(self, user_input: str, results: List[Dict[str, Any]]) -> str:
        sections: List[str] = [f"任务主题：{user_input}"]
        for r in results:
            status = r.get("status")
            name = r.get("name")
            output = r.get("output")
            if status == "ok":
                sections.append(f"工具[{name}]结果：{output}")
            elif status == "error":
                sections.append(f"工具[{name}]执行失败：{r.get('error')}")
            else:
                sections.append(f"工具[{name}]跳过：{r.get('reason')}")
        sections.append("—— 汇总完毕（离线回退）。")
        return "\n".join(sections)