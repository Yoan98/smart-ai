from __future__ import annotations

import os
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

from core.llm.base import LLMAdapter


class OpenAIAdapter(LLMAdapter):
    name = "openai"

    def _client(self):
        if OpenAI is None:
            raise RuntimeError("openai package not installed")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        return OpenAI(api_key=api_key)

    def _model(self) -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_plan(self, prompt: str) -> str:
        client = self._client()
        model = self._model()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "输出严格 JSON，无额外文字。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = completion.choices[0].message.content or "{}"
        return text

    def summarize(self, content: str) -> str:
        client = self._client()
        model = self._model()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "将内容整理为清晰的中文总结。"},
                {"role": "user", "content": content},
            ],
            temperature=0.4,
        )
        return completion.choices[0].message.content or ""