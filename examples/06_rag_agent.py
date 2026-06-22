"""阶段十三到阶段十四示例：演示 Agent 基于本地知识库回答问题。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_agents.agents.tool_agent import ToolAgent
from my_agents.core.message import Message, MessageRole
from my_agents.tools.builtin.rag_tool import RAGTool
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM


def print_section(title: str) -> None:
    """打印清晰的分节标题，便于观察一次调用链路。"""

    print(f"\n{'=' * 20} {title} {'=' * 20}")


def print_messages(messages: list[Message]) -> None:
    """按顺序打印一组消息，帮助理解 prompt 是如何组装的。"""

    for index, message in enumerate(messages, start=1):
        print(f"[{index}] role={message.role.value}")
        print(message.content)
        print("-" * 60)


class VerboseToolAgent(ToolAgent):
    """在不修改正式 Agent 逻辑的前提下，打印完整单次工具调用流程。"""

    def run_with_trace(self, input_text: str) -> str:
        """执行一次调用，并把规划、工具执行和最终回答完整打印出来。"""

        print_section("1. 用户问题")
        print(input_text)

        user_message = Message(role=MessageRole.USER, content=input_text)
        self.add_message(user_message)

        planning_messages = self._build_planning_messages()
        print_section("2. 第一次调用 LLM 前的 messages")
        print_messages(planning_messages)

        assistant_plan = self.llm.chat(planning_messages)
        print_section("3. Agent 第一次思考 / 决策结果")
        print(assistant_plan)

        action_name, action_input = self._parse_action_response(assistant_plan)
        if action_name is None:
            final_answer = self._extract_final_answer(assistant_plan)
            self.add_message(Message(role=MessageRole.ASSISTANT, content=final_answer))
            print_section("4. 无需调用工具，直接回答")
            print(final_answer)
            return final_answer

        print_section("4. 解析出的工具调用")
        print(f"Action: {action_name}")
        print(f"Action Input: {action_input}")

        tool_result = self.tool_registry.execute(action_name, action_input)
        print_section("5. 工具执行得到的 ToolResult")
        print(f"ok: {tool_result.ok}")
        print(f"content:\n{tool_result.content}")
        print(f"error: {tool_result.error}")
        print(f"metadata: {tool_result.metadata}")

        observation = self._format_observation(action_name, tool_result)
        print_section("6. ToolResult 转成 Observation")
        print(observation)

        final_messages = planning_messages + [
            Message(role=MessageRole.ASSISTANT, content=assistant_plan),
            Message(role=MessageRole.TOOL, content=observation),
        ]
        print_section("7. 第二次调用 LLM 前的 messages")
        print_messages(final_messages)

        final_answer_raw = self.llm.chat(final_messages)
        print_section("8. Agent 基于 Observation 生成最终回答")
        print(final_answer_raw)

        final_answer = self._extract_final_answer(final_answer_raw)
        self.add_message(Message(role=MessageRole.ASSISTANT, content=final_answer))

        print_section("9. 最终返回给用户的答案")
        print(final_answer)
        return final_answer


def main() -> None:
    """演示 ToolAgent 如何通过 RAGTool 使用本地知识库。"""

    registry = ToolRegistry()
    registry.register_tool(
        RAGTool(knowledge_base_path=PROJECT_ROOT / "knowledge_base")
    )

    llm = FakeLLM(
        [
            (
                "Thought: 我需要先检索本地知识库，找到关于 Agent 框架核心模块的片段。\n"
                'Action: rag\nAction Input: {"action": "search", "query": "Agent 框架核心模块", "top_k": 2}'
            ),
            (
                "Thought: 检索结果已经给出了核心模块和来源，我可以据此组织最终回答。\n"
                "Final Answer: 根据知识库，Agent 框架通常包含 Message、LLM、Agent、Tool、Memory 和 RAG 等核心模块。source: agent_intro.md"
            ),
        ]
    )

    agent = VerboseToolAgent(
        name="RAG 助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个会基于本地知识库回答问题的助手。",
    )

    agent.run_with_trace("根据知识库回答：Agent 框架通常包含哪些核心模块？")


if __name__ == "__main__":
    main()
