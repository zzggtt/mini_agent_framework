"""阶段六：定义 Tool 协议和参数结构。

这一轮要解决的问题是：
1. 不同外部能力要有统一的调用接口，而不是散落成任意函数。
2. 每个工具都应该自描述：它叫什么、做什么、接收什么参数。
3. 为后续 ToolAgent / ReActAgent 升级到更正式的工具 schema 做准备。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ToolParameter:
    """描述一个工具参数的最小 schema。"""

    name: str
    type: str
    description: str
    required: bool = True

    def to_schema(self) -> dict[str, object]:
        """把参数对象转成便于展示和后续扩展的 schema 结构。"""

        return {
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }


class Tool(ABC):
    """定义所有工具共享的最小接口协议。"""

    name: str = ""
    description: str = ""
    parameters: list[ToolParameter] = []

    def get_parameters(self) -> dict[str, dict[str, object]]:
        """返回工具参数 schema，供 registry 或后续 prompt 组装使用。"""

        return {
            parameter.name: parameter.to_schema()
            for parameter in self.parameters
        }

    def get_description(self) -> str:
        """返回工具描述，供后续模型理解工具用途。"""

        return self.description

    @abstractmethod
    def run(self, parameters: dict[str, Any]) -> Any:
        """执行工具，并返回原始结果或 ToolResult。"""
