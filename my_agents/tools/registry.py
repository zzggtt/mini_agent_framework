"""阶段六：实现统一的工具注册与执行入口。

这一轮要解决的问题是：
1. Agent 不应该直接持有每一个具体工具，而应该通过注册中心查找和执行工具。
2. 未注册工具、重复注册和工具执行异常都需要有统一行为。
3. 所有工具结果最终都要收敛成 ToolResult。
"""

from __future__ import annotations

from typing import Any

from my_agents.tools.base import Tool
from my_agents.tools.result import ToolResult


class ToolRegistry:
    """统一管理已注册工具，并提供执行入口。"""

    def __init__(self) -> None:
        """初始化一个空的工具注册中心。"""

        self._tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """注册一个工具；同名工具默认拒绝重复注册。"""

        if not tool.name.strip():
            raise ValueError("工具必须提供非空的 name。")

        if tool.name in self._tools:
            raise ValueError(f"工具已注册：{tool.name}")

        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        """按名称获取工具；不存在时返回 None。"""

        return self._tools.get(name)

    def execute(self, name: str, parameters: dict[str, Any]) -> ToolResult:
        """执行指定工具，并把各种返回风格统一包装成 ToolResult。"""

        tool = self.get_tool(name)
        if tool is None:
            return ToolResult(
                ok=False,
                content="",
                error=f"Unknown tool: {name}",
            )

        try:
            result = tool.run(parameters)
        except Exception as exc:
            return ToolResult(
                ok=False,
                content="",
                error=f"Tool execution failed: {tool.name}: {exc}",
            )

        if isinstance(result, ToolResult):
            return result

        return ToolResult(ok=True, content=result)

    def get_tools_description(self) -> str:
        """输出当前已注册工具的说明文本。"""

        descriptions: list[str] = []
        for tool_name in sorted(self._tools):
            tool = self._tools[tool_name]
            descriptions.append(f"- {tool.name}: {tool.get_description()}")
        return "\n".join(descriptions)
