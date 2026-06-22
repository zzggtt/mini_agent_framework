"""阶段八：实现只支持单次工具调用的 ToolAgent。

这一轮要解决的问题是：
1. 在 SimpleAgent 的基础上，引入一次工具调用链路。
2. 用最小文本协议理解 Action -> Observation -> Final Answer 的执行过程。
3. 让 Agent 先学会“调一次工具”，再进入后续更复杂的 ReAct 循环。
"""

from __future__ import annotations

import json
import re
from typing import Any

from my_agents.core.agent import Agent
from my_agents.core.message import Message, MessageRole
from my_agents.tools.registry import ToolRegistry

ACTION_RE = re.compile(r"Action:\s*(?P<action>[^\n]+)")
ACTION_INPUT_RE = re.compile(r"Action Input:\s*(?P<input>[\s\S]+)")


class ToolAgent(Agent):
    """实现只支持一次工具调用的学习版 Agent。"""

    def __init__(
        self,
        name: str,
        llm: object,
        tool_registry: ToolRegistry,
        system_prompt: str = "",
    ) -> None:
        """初始化 ToolAgent，并注入工具注册中心。"""

        super().__init__(name=name, llm=llm, system_prompt=system_prompt)
        self.tool_registry = tool_registry

    def run(self, input_text: str) -> str:
        """执行一轮带单次工具调用的主循环。"""

        user_message = Message(role=MessageRole.USER, content=input_text)
        self.add_message(user_message)

        planning_messages = self._build_planning_messages()
        assistant_plan = self.llm.chat(planning_messages)

        action_name, action_input = self._parse_action_response(assistant_plan)
        if action_name is None:
            final_answer = self._extract_final_answer(assistant_plan)
            self.add_message(Message(role=MessageRole.ASSISTANT, content=final_answer))
            return final_answer

        tool_result = self.tool_registry.execute(action_name, action_input)
        observation = self._format_observation(action_name, tool_result)

        final_messages = planning_messages + [
            Message(role=MessageRole.ASSISTANT, content=assistant_plan),
            Message(role=MessageRole.TOOL, content=observation),
        ]
        final_answer = self.llm.chat(final_messages)
        final_answer = self._extract_final_answer(final_answer)
        self.add_message(Message(role=MessageRole.ASSISTANT, content=final_answer))
        return final_answer

    def _build_planning_messages(self) -> list[Message]:
        """构造第一次让模型决定是否调用工具的上下文。"""

        messages: list[Message] = []
        if self.system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=self.system_prompt))
        messages.append(Message(role=MessageRole.SYSTEM, content=self._build_tool_instruction()))
        messages.extend(self.get_history())
        return messages

    def _build_tool_instruction(self) -> str:
        """生成给模型看的最小工具调用协议说明。"""

        tools_description = self.tool_registry.get_tools_description() or "- 无可用工具"
        return (
            "你是一个会调用工具的助手。\n"
            "如果需要调用工具，请严格输出如下格式：\n"
            "Action: <tool_name>\n"
            'Action Input: {"key": "value"}\n'
            "如果不需要调用工具，请直接给出最终自然语言回答，"
            "或使用 Final Answer: <answer> 格式。\n"
            "当前可用工具如下：\n"
            f"{tools_description}"
        )

    def _parse_action_response(self, text: str) -> tuple[str | None, dict[str, Any]]:
        """解析模型输出中的 Action 和 Action Input。"""

        action_match = ACTION_RE.search(text)
        input_match = ACTION_INPUT_RE.search(text)
        if action_match is None or input_match is None:
            return None, {}

        action_name = action_match.group("action").strip()
        raw_action_input = input_match.group("input").strip()
        if not action_name:
            return None, {}

        try:
            parsed_input = json.loads(raw_action_input)
        except json.JSONDecodeError:
            return None, {}

        if not isinstance(parsed_input, dict):
            return None, {}

        return action_name, parsed_input

    @staticmethod
    def _extract_final_answer(text: str) -> str:
        """提取最终回答；没有显式标签时直接返回原文本。"""

        marker = "Final Answer:"
        if marker in text:
            return text.split(marker, 1)[1].strip()
        return text.strip()

    @staticmethod
    def _format_observation(action_name: str, tool_result: Any) -> str:
        """把工具执行结果整理成 Observation 文本。"""

        status = "ok" if tool_result.ok else "error"
        return (
            f"Tool: {action_name}\n"
            f"Status: {status}\n"
            f"Content: {tool_result.content}\n"
            f"Error: {tool_result.error}"
        )
