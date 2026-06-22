"""阶段三：提供稳定的测试替身。

这一轮要解决的问题是：
1. 在没有真实 API Key 的情况下，也能测试 Agent 主循环。
2. 单元测试不依赖网络、费用和模型随机性。
3. 能记录传给模型的 messages，便于验证上下文拼装是否正确。
"""

from __future__ import annotations

from typing import Any


class FakeLLM:
    """用固定回复队列模拟一个最小可用的 LLM。"""

    def __init__(self, responses: list[str]) -> None:
        """初始化一个带固定回复队列的假模型。

        设计目的：
        1. `responses` 控制每次 chat 的返回值，保证测试稳定。
        2. `calls` 记录每次收到的 messages，便于后续断言 Agent 是否正确组装上下文。
        """

        self.responses = list(responses)
        self.calls: list[list[Any]] = []

    def chat(self, messages: list[Any]) -> str:
        """记录输入消息，并按顺序返回预设回复。

        这里故意保持接口很小，只模拟当前阶段真正需要的能力：
        llm.chat(messages) -> str
        """

        # 这里记录列表快照，而不是原列表引用，避免调用方后续继续 append
        # 时把历史调用记录一并污染。
        self.calls.append(list(messages))
        return self.responses.pop(0)
