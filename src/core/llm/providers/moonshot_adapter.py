from __future__ import annotations

from core.llm.base import LLMAdapter


class MoonshotAdapter(LLMAdapter):
    name = "moonshot"

    def generate_plan(self, prompt: str) -> str:
        # Placeholder; in production, integrate provider SDK.
        from core.llm.base import MockLLMAdapter
        return MockLLMAdapter().generate_plan(prompt)

    def summarize(self, content: str) -> str:
        from core.llm.base import MockLLMAdapter
        return MockLLMAdapter().summarize(content)