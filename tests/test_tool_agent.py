"""阶段八测试：验证 ToolAgent 的单次工具调用链路。"""

from __future__ import annotations

from my_agents.agents.tool_agent import ToolAgent
from my_agents.core.message import MessageRole
from my_agents.tools.base import Tool, ToolParameter
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM


class EchoTool(Tool):
    """测试用工具：把 text 原样返回。"""

    name = "echo"
    description = "原样返回输入文本"
    parameters = [
        ToolParameter(
            name="text",
            type="string",
            description="要原样返回的文本",
        )
    ]

    def run(self, parameters: dict[str, str]) -> str:
        """返回 text 参数的值。"""

        return parameters["text"]


def test_tool_agent_can_complete_single_tool_call() -> None:
    """验证 ToolAgent 能完成一次工具调用并产出自然语言答案。"""

    registry = ToolRegistry()
    registry.register_tool(EchoTool())
    llm = FakeLLM(
        [
            'Action: echo\nAction Input: {"text": "14"}',
            "Final Answer: 计算结果是 14。",
        ]
    )
    agent = ToolAgent(
        name="工具助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个帮助用户调用工具的助手。",
    )

    result = agent.run("帮我计算 2 + 3 * 4")

    assert result == "计算结果是 14。"
    assert len(llm.calls) == 2
    assert "echo" in llm.calls[0][1].content
    assert "原样返回输入文本" in llm.calls[0][1].content
    assert "Tool: echo" in llm.calls[1][-1].content
    assert "Content: 14" in llm.calls[1][-1].content


def test_tool_agent_returns_plain_answer_when_model_chooses_no_tool() -> None:
    """验证模型不调用工具时，ToolAgent 会直接返回自然语言回答。"""

    registry = ToolRegistry()
    registry.register_tool(EchoTool())
    llm = FakeLLM(["Final Answer: 这是一个普通回答。"])
    agent = ToolAgent(
        name="工具助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个帮助用户调用工具的助手。",
    )

    result = agent.run("你好")

    assert result == "这是一个普通回答。"
    history = agent.get_history()
    assert len(history) == 2
    assert [message.role for message in history] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
    ]


def test_tool_agent_passes_unknown_tool_error_back_to_model_context() -> None:
    """验证未知工具错误会进入 Observation，供模型生成最终回答。"""

    registry = ToolRegistry()
    llm = FakeLLM(
        [
            'Action: missing\nAction Input: {"text": "hello"}',
            "Final Answer: 当前没有这个工具。",
        ]
    )
    agent = ToolAgent(
        name="工具助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个帮助用户调用工具的助手。",
    )

    result = agent.run("请调用 missing 工具")

    assert result == "当前没有这个工具。"
    assert "Status: error" in llm.calls[1][-1].content
    assert "Unknown tool: missing" in llm.calls[1][-1].content
