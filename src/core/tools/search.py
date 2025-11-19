from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from core.tools.base import BaseTool


class SearchArgs(BaseModel):
    query: str = Field(..., description="查询关键词")
    limit: int = Field(default=3, ge=1, le=10, description="返回条数")


class SearchTool(BaseTool):
    name = "search"
    description = "基于本地知识库的简易查询（离线）"
    args_schema = SearchArgs

    def __init__(self):
        super().__init__()
        self._kb = self._load_kb()

    def _load_kb(self) -> List[Dict[str, Any]]:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # src/
        kb_path = os.path.join(base_dir, "data", "knowledge_base.json")
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def run(self, **kwargs) -> Dict[str, Any]:
        args = self.args_schema(**kwargs)
        q = args.query.lower()
        scored: List[Dict[str, Any]] = []
        for entry in self._kb:
            text = (entry.get("title", "") + " " + entry.get("content", "")).lower()
            score = 0
            for token in set(q.split()):
                if token and token in text:
                    score += 1
            if score > 0:
                scored.append({"score": score, **entry})
        scored.sort(key=lambda x: x["score"], reverse=True)
        hits = scored[: args.limit]
        return {"query": args.query, "hits": hits}