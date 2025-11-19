from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.graph.state import AgentState
from core.llm.base import LLMAdapter, MockLLMAdapter
from core.tools.registry import ToolRegistry


class PlanStep(BaseModel):
    type: str = Field(description="step type: 'tool' or 'plugin'")
    name: str = Field(description="tool or plugin name")
    input: Dict[str, Any] = Field(default_factory=dict)
    condition: Optional[str] = Field(default=None, description="optional condition for execution")


class Plan(BaseModel):
    objective: str
    steps: List[PlanStep] = Field(default_factory=list)


class PlannerNode:
    """Planner Agent Node

    输入用户需求，输出计划 JSON（由 LLM 决策）。
    有离线回退逻辑以保障测试与本地运行。
    """

    def __init__(self, llm: Optional[LLMAdapter] = None, registry: Optional[ToolRegistry] = None):
        self.llm = llm or MockLLMAdapter()
        self.registry = registry or ToolRegistry()

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        user_input = state["user_input"]
        available_tools = sorted(self.registry.list_tool_names())

        plan = self._generate_plan(user_input, available_tools)
        return {"plan": plan.dict()}

    # internal helpers
    def _generate_plan(self, user_input: str, available_tools: List[str]) -> Plan:
        prompt = self._build_prompt(user_input, available_tools)
        try:
            raw = self.llm.generate_plan(prompt)
            parsed = self._safe_parse_plan(raw)
            if parsed and len(parsed.steps) > 0:
                return parsed
        except Exception:
            pass
        # fallback deterministic plan
        return self._fallback_plan(user_input, available_tools)

    def _build_prompt(self, user_input: str, available_tools: List[str]) -> str:
        return (
            "You are a planning agent. Based on the user's goal, produce a JSON plan.\n"
            "Requirements:\n"
            "- Use available tools only.\n"
            "- Structure: {\"objective\": str, \"steps\": [{\"type\": \"tool\", \"name\": str, \"input\": object}]}\n"
            f"AvailableTools: {available_tools}\n"
            f"UserInput: {user_input}\n"
            "Return ONLY JSON without extra text."
        )

    def _safe_parse_plan(self, raw: str) -> Optional[Plan]:
        try:
            data = json.loads(raw)
            return Plan(**data)
        except Exception:
            return None

    def _fallback_plan(self, user_input: str, available_tools: List[str]) -> Plan:
        steps: List[PlanStep] = []
        # Prefer search -> outline -> mindmap if available
        if "search" in available_tools:
            steps.append(PlanStep(type="tool", name="search", input={"query": user_input, "limit": 5}))
        if "outline" in available_tools:
            steps.append(PlanStep(type="tool", name="outline", input={
                "topic": user_input,
                "objectives": [
                    "明确探究目标",
                    "设计实验或探究步骤",
                    "数据记录与分析",
                    "形成结论与反思"
                ],
                "sections": 5,
                "depth": 2
            }))
        if "mindmap" in available_tools:
            steps.append(PlanStep(type="tool", name="mindmap", input={
                "topic": user_input,
                "subtopics": ["背景知识", "核心概念", "实验设计", "数据分析", "反思改进"],
                "depth": 2
            }))
        return Plan(objective=f"围绕‘{user_input}’生成可执行的探究式学习任务计划", steps=steps)