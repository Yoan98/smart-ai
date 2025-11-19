from __future__ import annotations

from core.llm.base import LLMAdapter


class DeepSeekAdapter(LLMAdapter):
    name = "deepseek"

    def generate_plan(self, prompt: str) -> str:
        # Placeholder; in production, integrate provider SDK.
        # For now, mirror Mock behavior to avoid runtime/network dependency unless configured.
        from core.llm.base import MockLLMAdapter
        return MockLLMAdapter().generate_plan(prompt)

    def summarize(self, content: str) -> str:
        from core.llm.base import MockLLMAdapter
        return MockLLMAdapter().summarize(content)