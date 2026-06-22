"""阶段六：工具系统包。

这一层负责把外部能力统一抽象成 Tool，并通过 ToolRegistry 管理。
"""

from my_agents.tools.base import Tool, ToolParameter
from my_agents.tools.registry import ToolRegistry
from my_agents.tools.result import ToolResult

__all__ = [
    "Tool",
    "ToolParameter",
    "ToolRegistry",
    "ToolResult",
]
