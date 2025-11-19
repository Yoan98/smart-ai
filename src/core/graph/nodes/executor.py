from __future__ import annotations

from typing import Any, Dict, List

from core.graph.state import AgentState
from core.tools.registry import ToolRegistry


class ToolExecutorNode:
    """Tool Executor node.
    根据 Planner 计划逐步执行工具并收集结果。
    """

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        plan = state.get("plan") or {}
        steps: List[Dict[str, Any]] = plan.get("steps", [])
        results: List[Dict[str, Any]] = state.get("tool_results", [])

        for idx, step in enumerate(steps):
            if step.get("type") != "tool":
                # 仅执行工具类型；插件类型可以未来扩展
                continue
            name = step.get("name")
            payload = step.get("input", {})
            tool = self.registry.get(name)
            if not tool:
                results.append({
                    "step": idx,
                    "name": name,
                    "status": "skipped",
                    "reason": "tool not found"
                })
                continue
            try:
                output = tool.run(**payload)
                results.append({
                    "step": idx,
                    "name": name,
                    "status": "ok",
                    "output": output
                })
            except Exception as e:
                results.append({
                    "step": idx,
                    "name": name,
                    "status": "error",
                    "error": str(e)
                })

        return {"tool_results": results}