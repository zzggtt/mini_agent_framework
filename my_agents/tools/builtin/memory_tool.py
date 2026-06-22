"""阶段十一到阶段十二：把显式记忆系统包装成工具。"""

from __future__ import annotations

from typing import Any

from my_agents.memory.simple_memory import SimpleMemory
from my_agents.tools.base import Tool, ToolParameter
from my_agents.tools.result import ToolResult


class MemoryTool(Tool):
    """通过统一工具协议暴露 add / search / summary / clear 能力。"""

    name = "memory"
    description = "保存、检索、汇总和清空长期记忆。"
    parameters = [
        ToolParameter(
            name="action",
            type="string",
            description="要执行的记忆操作：add、search、summary、clear",
        ),
        ToolParameter(
            name="content",
            type="string",
            description="add 操作要写入的记忆内容",
            required=False,
        ),
        ToolParameter(
            name="query",
            type="string",
            description="search 操作使用的关键词查询",
            required=False,
        ),
        ToolParameter(
            name="limit",
            type="integer",
            description="search 操作返回的最大条数",
            required=False,
        ),
    ]

    def __init__(self, memory: SimpleMemory | None = None) -> None:
        """初始化工具，并允许外部注入共享的记忆仓库。"""

        self.memory = memory or SimpleMemory()

    def run(self, parameters: dict[str, Any]) -> ToolResult:
        """根据 action 分发到底层记忆系统。"""

        action = str(parameters.get("action", "")).strip().lower()
        if action == "add":
            return self._add(parameters)
        if action == "search":
            return self._search(parameters)
        if action == "summary":
            return self._summary()
        if action == "clear":
            return self._clear()
        return ToolResult(ok=False, content="", error=f"不支持的 memory action: {action}")

    def _add(self, parameters: dict[str, Any]) -> ToolResult:
        """写入一条显式记忆。"""

        content = str(parameters.get("content", "")).strip()
        if not content:
            return ToolResult(ok=False, content="", error="memory.add 需要非空 content")

        memory_type = str(parameters.get("memory_type", "semantic")).strip() or "semantic"
        item = self.memory.add(content=content, memory_type=memory_type)
        return ToolResult(
            ok=True,
            content=item.content,
            metadata={"id": item.id, "memory_type": item.memory_type},
        )

    def _search(self, parameters: dict[str, Any]) -> ToolResult:
        """按关键词检索记忆，并返回文本结果。"""

        query = str(parameters.get("query", "")).strip()
        if not query:
            return ToolResult(ok=False, content="", error="memory.search 需要非空 query")

        limit = int(parameters.get("limit", 5))
        results = self.memory.search(query=query, limit=limit)
        if not results:
            return ToolResult(ok=True, content="未找到相关记忆。")

        content = "\n".join(item.content for item in results)
        return ToolResult(ok=True, content=content, metadata={"count": len(results)})

    def _summary(self) -> ToolResult:
        """把当前全部记忆内容汇总成一段文本。"""

        items = self.memory.list_all()
        if not items:
            return ToolResult(ok=True, content="当前没有任何记忆。")

        content = "\n".join(f"- {item.content}" for item in items)
        return ToolResult(ok=True, content=content, metadata={"count": len(items)})

    def _clear(self) -> ToolResult:
        """清空当前全部记忆。"""

        self.memory.clear()
        return ToolResult(ok=True, content="记忆已清空。")
