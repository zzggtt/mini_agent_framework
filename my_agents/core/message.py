"""阶段二：定义 Agent 框架内部统一使用的消息结构。

这一轮要解决的问题是：
1. 用户输入、模型回复、系统提示词都需要有统一的数据表示。
2. 后续接入真实 LLM 时，消息对象要能稳定转换为 OpenAI 风格的 messages。
3. Agent 内部不应该到处手写 dict，而应该统一使用 Message。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    """约束消息角色，避免在项目里到处手写字符串。"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(slots=True)
class Message:
    """表示一条发给模型或从模型返回的消息。

    设计目的：
    1. 统一保存 role 和 content。
    2. 让框架内部先面向对象编排消息，最后再转成 API 需要的 dict。
    3. 为后续 history、tool、memory、rag 注入提供统一载体。
    """

    role: MessageRole
    content: str

    def to_dict(self) -> dict[str, str]:
        """转换成聊天模型常见的消息格式。

        这一层的目的不是做复杂逻辑，而是把内部对象稳定映射到：
        {"role": "...", "content": "..."}
        """

        return {"role": self.role.value, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """从原始字典恢复 Message 对象。

        这一方法主要服务调试、测试和后续可能的历史恢复场景。
        """

        role = MessageRole(data["role"])
        content = data["content"]
        return cls(role=role, content=content)

    def __str__(self) -> str:
        """返回便于调试查看的紧凑字符串表示。"""

        return f"{self.role.value}: {self.content}"
