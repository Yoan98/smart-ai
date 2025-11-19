from __future__ import annotations

from typing import Protocol


class LLMAdapter(Protocol):
    """LLM adapter interface for planning and summarization."""

    name: str

    def generate_plan(self, prompt: str) -> str:  # returns JSON string
        ...

    def summarize(self, content: str) -> str:
        ...


class MockLLMAdapter:
    """Offline mock LLM adapter for tests and local runs.

    规则驱动但遵循相同接口，满足“流程由 LLM 决策”接口形态，同时可离线运行。
    """

    name = "mock"

    def generate_plan(self, prompt: str) -> str:
        # Very simple heuristic: if prompt mentions available tools, compose a plan
        # Extract user input line
        try:
            user_line = [l for l in prompt.splitlines() if l.startswith("UserInput:")][0]
            user_input = user_line.split("UserInput:")[-1].strip()
        except Exception:
            user_input = "用户任务"
        plan = {
            "objective": f"围绕‘{user_input}’生成可执行的探究式学习任务计划",
            "steps": [
                {"type": "tool", "name": "search", "input": {"query": user_input, "limit": 3}},
                {
                    "type": "tool",
                    "name": "outline",
                    "input": {
                        "topic": user_input,
                        "objectives": ["明确目标", "设计探究步骤", "记录与分析", "得出结论"],
                        "sections": 4,
                        "depth": 2,
                    },
                },
                {
                    "type": "tool",
                    "name": "mindmap",
                    "input": {
                        "topic": user_input,
                        "subtopics": ["背景知识", "核心概念", "实验设计", "数据分析", "反思改进"],
                        "depth": 2,
                    },
                },
            ],
        }
        import json
        return json.dumps(plan, ensure_ascii=False)

    def summarize(self, content: str) -> str:
        # Basic deterministic summarization: return content with a header
        return "【总结】\n" + content