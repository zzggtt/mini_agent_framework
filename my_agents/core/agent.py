"""阶段四：定义所有 Agent 共享的基础抽象。

这一轮要解决的问题是：
1. 不同类型的 Agent 都会共享 name、llm、system_prompt、history 这些状态。
2. 后续会有 SimpleAgent、ToolAgent、ReActAgent，公共能力应该放到基类里。
3. 具体执行流程由子类决定，但历史管理应该统一。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from my_agents.core.message import Message


class Agent(ABC):
    """定义 Agent 的公共状态和基础接口。"""

    def __init__(self, name: str, llm: Any, system_prompt: str = "") -> None:
        """初始化所有 Agent 都会用到的依赖和状态。

        设计目的：
        1. `name` 代表这个 Agent 的身份。
        2. `llm` 是模型接口依赖，当前阶段可以传 FakeLLM。
        3. `system_prompt` 是运行配置，不直接存进 history。
        4. `_history` 专门保存当前会话中的 user / assistant 等消息。
        """

        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self._history: list[Message] = []

    def add_message(self, message: Message) -> None:
        """向当前会话历史中追加一条消息。"""

        self._history.append(message)

    def get_history(self) -> list[Message]:
        """返回历史消息的副本，而不是直接暴露内部列表。

        这样外部代码即使误操作返回值，也不会直接破坏 Agent 内部状态。
        """

        return list(self._history)

    def clear_history(self) -> None:
        """清空当前会话历史。"""

        self._history.clear()

    @abstractmethod
    def run(self, input_text: str) -> str:
        """执行一轮对话，并返回 assistant 的文本回复。

        这里用抽象方法，是为了把“公共状态”和“具体流程”分开。
        不同 Agent 都可以有各自的执行主循环。
        """
