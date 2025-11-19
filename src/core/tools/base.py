from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel


class BaseTool:
    """Base class for tools in the framework.

    每个工具必须：
    - 定义唯一的 name
    - 定义 description
    - 定义 args_schema (pydantic BaseModel)
    - 实现 run(**kwargs)
    """

    name: str = "base"
    description: str = ""
    args_schema: type[BaseModel] | None = None

    def run(self, **kwargs) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError

    def schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "args": self.args_schema.schema() if self.args_schema else {},
        }