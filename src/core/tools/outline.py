from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from core.tools.base import BaseTool


class OutlineArgs(BaseModel):
    topic: str = Field(..., description="主题")
    objectives: List[str] = Field(default_factory=list, description="学习目标/探究目标")
    sections: int = Field(default=5, ge=1, le=20, description="章节数")
    depth: int = Field(default=2, ge=1, le=5, description="层级深度")


class OutlineTool(BaseTool):
    name = "outline"
    description = "生成结构化学习/探究大纲"
    args_schema = OutlineArgs

    def run(self, **kwargs) -> Dict[str, Any]:
        args = self.args_schema(**kwargs)
        sections = max(1, min(args.sections, 20))
        depth = max(1, min(args.depth, 5))
        outline = {
            "topic": args.topic,
            "objectives": args.objectives,
            "structure": []
        }
        # deterministic hierarchical outline
        for i in range(1, sections + 1):
            section = {"title": f"第{i}章：子主题{i}", "items": []}
            for j in range(1, depth + 1):
                section["items"].append(f"层级{j}：围绕{args.topic}的要点{i}.{j}")
            outline["structure"].append(section)
        return outline