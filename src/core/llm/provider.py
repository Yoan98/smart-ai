from __future__ import annotations

import os
from typing import Optional

from core.llm.base import LLMAdapter, MockLLMAdapter
from core.llm.providers.openai_adapter import OpenAIAdapter
from core.llm.providers.deepseek_adapter import DeepSeekAdapter
from core.llm.providers.moonshot_adapter import MoonshotAdapter


def get_llm_from_env() -> LLMAdapter:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "openai":
        return OpenAIAdapter()
    if provider == "deepseek":
        return DeepSeekAdapter()
    if provider == "moonshot":
        return MoonshotAdapter()
    return MockLLMAdapter()


def resolve_llm(explicit: Optional[str] = None) -> LLMAdapter:
    if explicit:
        os.environ["LLM_PROVIDER"] = explicit
    return get_llm_from_env()