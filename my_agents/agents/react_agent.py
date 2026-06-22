"""阶段九到阶段十：实现学习版 ReActAgent。

这一轮要解决的问题是：
1. 让 Agent 支持多轮 Thought -> Action -> Observation -> Final Answer 循环。
2. 在 happy path 之外，补上解析失败、未知工具和最大迭代次数等恢复逻辑。
3. 保存每一步执行轨迹，方便学习和调试 ReAct 主循环。
"""

from __future__ import annotations

import json
import re
from typing import Any

from my_agents.core.agent import Agent
from my_agents.core.message import Message, MessageRole
from my_agents.tools.registry import ToolRegistry

THOUGHT_RE = re.compile(r"Thought:\s*(?P<thought>[^\n]+)")
ACTION_RE = re.compile(r"Action:\s*(?P<action>[^\n]+)")
ACTION_INPUT_RE = re.compile(r"Action Input:\s*(?P<input>[^\n]+)")
FINAL_ANSWER_RE = re.compile(r"Final Answer:\s*(?P<answer>[\s\S]+)")


class ReActAgent(Agent):
    """实现支持多轮工具调用的学习版 ReActAgent。"""

    def __init__(
        self,
        name: str,
        llm: object,
        tool_registry: ToolRegistry,
        system_prompt: str = "",
        max_iterations: int = 3,
        debug: bool = False,
    ) -> None:
        """初始化 ReActAgent 的依赖、限制和调试配置。"""

        super().__init__(name=name, llm=llm, system_prompt=system_prompt)
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.debug = debug
        self._trace: list[dict[str, Any]] = []

    def run(self, input_text: str) -> str:
        """执行多步 ReAct 循环，直到得到 Final Answer 或达到上限。"""

        self._trace = []
        self.add_message(Message(role=MessageRole.USER, content=input_text))
        messages = self._build_prompt()

        for _ in range(self.max_iterations):
            assistant_text = self.llm.chat(messages)
            messages.append(Message(role=MessageRole.ASSISTANT, content=assistant_text))
            step = self._parse_action(assistant_text)

            if step["final_answer"]:
                final_answer = str(step["final_answer"]).strip()
                self._record_trace(
                    thought=step["thought"],
                    action=step["action"],
                    action_input=step["action_input"],
                    observation="",
                    final_answer=final_answer,
                )
                self.add_message(Message(role=MessageRole.ASSISTANT, content=final_answer))
                return final_answer

            observation = self._execute_action(step)
            messages.append(Message(role=MessageRole.TOOL, content=observation))

        final_answer = "抱歉，我在最大迭代次数内仍未完成任务。"
        if self.debug and self._trace:
            final_answer = f"{final_answer}\n\nTrace: {self._trace}"
        self.add_message(Message(role=MessageRole.ASSISTANT, content=final_answer))
        return final_answer

    def get_trace(self) -> list[dict[str, Any]]:
        """返回执行轨迹的副本，避免外部直接修改内部状态。"""

        return [dict(item) for item in self._trace]

    def _build_prompt(self) -> list[Message]:
        """构造 ReAct 主循环第一次调用模型所需的上下文。"""

        messages: list[Message] = []
        if self.system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=self.system_prompt))
        messages.append(Message(role=MessageRole.SYSTEM, content=self._build_react_instruction()))
        messages.extend(self.get_history())
        return messages

    def _build_react_instruction(self) -> str:
        """生成学习版 ReAct 协议说明和工具描述。"""

        tools_description = self.tool_registry.get_tools_description() or "- 无可用工具"
        return (
            "你是一个会使用 ReAct 模式解决问题的助手。\n"
            "每一步请遵循如下格式之一：\n"
            "Thought: <你的思考>\n"
            "Action: <tool_name>\n"
            'Action Input: {"key": "value"}\n'
            "或者：\n"
            "Thought: <你的思考>\n"
            "Final Answer: <最终答案>\n"
            "当你收到 Observation 后，可以继续思考并决定下一步。\n"
            "当前可用工具如下：\n"
            f"{tools_description}"
        )

    def _parse_action(self, text: str) -> dict[str, Any]:
        """解析一次模型输出中的 Thought、Action、Action Input 和 Final Answer。"""

        thought_match = THOUGHT_RE.search(text)
        action_match = ACTION_RE.search(text)
        action_input_match = ACTION_INPUT_RE.search(text)
        final_answer_match = FINAL_ANSWER_RE.search(text)

        return {
            "thought": thought_match.group("thought").strip() if thought_match else "",
            "action": action_match.group("action").strip() if action_match else "",
            "action_input_raw": action_input_match.group("input").strip() if action_input_match else "",
            "action_input": {},
            "final_answer": final_answer_match.group("answer").strip() if final_answer_match else "",
        }

    def _execute_action(self, step: dict[str, Any]) -> str:
        """执行 Action，或把解析错误包装成 Observation 反馈给模型。"""

        action_name = str(step["action"]).strip()
        raw_action_input = str(step["action_input_raw"]).strip()

        if not action_name:
            observation = "Observation: 未检测到 Action，请按照 ReAct 格式继续。"
            self._record_trace(
                thought=step["thought"],
                action="",
                action_input={},
                observation=observation,
            )
            return observation

        if not raw_action_input:
            observation = "Observation: 缺少 Action Input，请重新给出合法工具调用。"
            self._record_trace(
                thought=step["thought"],
                action=action_name,
                action_input={},
                observation=observation,
            )
            return observation

        try:
            parsed_input = json.loads(raw_action_input)
        except json.JSONDecodeError:
            observation = "Observation: Action Input 不是合法 JSON，请重新给出合法工具调用。"
            self._record_trace(
                thought=step["thought"],
                action=action_name,
                action_input={},
                observation=observation,
            )
            return observation

        if not isinstance(parsed_input, dict):
            observation = "Observation: Action Input 必须是 JSON 对象，请重新给出合法工具调用。"
            self._record_trace(
                thought=step["thought"],
                action=action_name,
                action_input={},
                observation=observation,
            )
            return observation

        step["action_input"] = parsed_input
        tool_result = self.tool_registry.execute(action_name, parsed_input)
        observation = self._format_observation(action_name, tool_result)
        self._record_trace(
            thought=step["thought"],
            action=action_name,
            action_input=parsed_input,
            observation=observation,
        )
        return observation

    @staticmethod
    def _format_observation(action_name: str, tool_result: Any) -> str:
        """把 ToolResult 转成模型下一步可消费的 Observation 文本。"""

        if tool_result.ok:
            return f"Observation: {tool_result.content}"
        return f"Observation: {tool_result.error}"

    def _record_trace(
        self,
        thought: str,
        action: str,
        action_input: dict[str, Any],
        observation: str,
        final_answer: str = "",
    ) -> None:
        """记录当前一步 ReAct 轨迹，便于后续调试与教学。"""

        self._trace.append(
            {
                "thought": thought,
                "action": action,
                "action_input": dict(action_input),
                "observation": observation,
                "final_answer": final_answer,
            }
        )
