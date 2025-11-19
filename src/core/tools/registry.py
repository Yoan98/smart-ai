from __future__ import annotations

import importlib
import os
import pkgutil
from typing import Dict, List, Optional

from core.tools.base import BaseTool


class ToolRegistry:
    """Auto-register tools by scanning core/tools modules.

    所有工具文件都在 core/tools/ 下。自动加载继承 BaseTool 的类。
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._discover()

    def _discover(self):
        base_dir = os.path.dirname(__file__)  # .../core/tools
        for _, mod_name, is_pkg in pkgutil.iter_modules([base_dir]):
            if is_pkg:
                continue
            if mod_name in {"base", "registry", "__init__"}:
                continue
            dotted = f"core.tools.{mod_name}"
            try:
                module = importlib.import_module(dotted)
            except Exception:
                continue
            # find classes inheriting BaseTool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseTool) and attr is not BaseTool:
                    try:
                        instance = attr()
                        if instance.name in self._tools:
                            # skip duplicates
                            continue
                        self._tools[instance.name] = instance
                    except Exception:
                        # skip bad tool
                        continue

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def all(self) -> Dict[str, BaseTool]:
        return dict(self._tools)