"""阶段四：实现最小可用的对话 Agent。

这一轮要解决的问题是：
1. 让 Agent 第一次具备“接收输入 -> 调模型 -> 返回结果”的能力。
2. 让 Agent 能维护最基本的多轮对话历史。
3. 为后面的 ToolAgent、ReActAgent 提供最小主循环模板。
"""

from __future__ import annotations

from my_agents.core.agent import Agent
from my_agents.core.message import Message, MessageRole


class SimpleAgent(Agent):
    """实现最基础的多轮对话 Agent。"""

    def __init__(self, name: str, llm: object, system_prompt: str = "") -> None:
        """初始化一个最简单的对话 Agent。"""

        super().__init__(name=name, llm=llm, system_prompt=system_prompt)

    def run(self, input_text: str) -> str:
        """执行一轮最小对话主循环。

        主流程：
        1. 把当前用户输入包装成 Message。
        2. 先写入 history，让这一轮调用能看到当前输入。
        3. 组装 system prompt + history 作为本轮上下文。
        4. 调用 llm.chat(messages) 获取文本回复。
        5. 把 assistant 回复写回 history，支持下一轮连续对话。
        """

        user_message = Message(role=MessageRole.USER, content=input_text)
        self.add_message(user_message)

        # 本轮真正发给模型的上下文不只是一句输入，
        # 而是 system prompt + 历史消息的组合。
        messages: list[Message] = []
        if self.system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=self.system_prompt))
        messages.extend(self.get_history())

        # 当前阶段先约定 chat() 返回纯文本，
        # 这样既能接 FakeLLM，也方便后续接真实 LLM。
        assistant_text = self.llm.chat(messages)
        assistant_message = Message(role=MessageRole.ASSISTANT, content=assistant_text)
        self.add_message(assistant_message)
        return assistant_text
