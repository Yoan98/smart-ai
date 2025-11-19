from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from core.tools.base import BaseTool


class MindMapArgs(BaseModel):
    topic: str = Field(..., description="主题")
    subtopics: List[str] = Field(default_factory=list, description="子主题列表")
    depth: int = Field(default=2, ge=1, le=5, description="层级深度")


class MindMapTool(BaseTool):
    name = "mindmap"
    description = "生成思维导图（树形结构）"
    args_schema = MindMapArgs

    def run(self, **kwargs) -> Dict[str, Any]:
        args = self.args_schema(**kwargs)
        # deterministic tree
        tree: Dict[str, Any] = {"center": args.topic, "branches": []}
        for sidx, sub in enumerate(args.subtopics, start=1):
            branch = {"name": f"{sub}", "children": []}
            for d in range(1, args.depth + 1):
                branch["children"].append({"name": f"{sub}-层级{d}", "note": f"围绕{args.topic}的{sub}子要点{d}"})
            tree["branches"].append(branch)
        return tree