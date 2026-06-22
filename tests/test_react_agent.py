"""阶段九到阶段十测试：验证 ReActAgent 的多步推理与恢复逻辑。"""

from __future__ import annotations

from my_agents.agents.react_agent import ReActAgent
from my_agents.tools.builtin.calculator import CalculatorTool
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM


def _build_agent(responses: list[str], max_iterations: int = 3, debug: bool = False) -> ReActAgent:
    """构造一个带 calculator 工具的 ReActAgent。"""

    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())
    return ReActAgent(
        name="ReAct 助手",
        llm=FakeLLM(responses),
        tool_registry=registry,
        system_prompt="你是一个帮助用户逐步推理的助手。",
        max_iterations=max_iterations,
        debug=debug,
    )


def test_react_agent_can_complete_happy_path_with_multiple_steps() -> None:
    """验证 ReActAgent 能完成一次标准的 Thought -> Action -> Observation -> Final Answer。"""

    agent = _build_agent(
        [
            'Thought: 需要先计算 15 * 23\nAction: calculator\nAction Input: {"expression": "15 * 23"}',
            "Thought: 345 不是偶数\nFinal Answer: 15 * 23 = 345，345 不是偶数。",
        ]
    )

    result = agent.run("请计算 15 * 23，然后判断结果是不是偶数。")

    assert result == "15 * 23 = 345，345 不是偶数。"
    trace = agent.get_trace()
    assert len(trace) == 2
    assert trace[0]["action"] == "calculator"
    assert trace[0]["action_input"] == {"expression": "15 * 23"}
    assert trace[0]["observation"] == "Observation: 345"
    assert trace[1]["final_answer"] == "15 * 23 = 345，345 不是偶数。"


def test_react_agent_returns_observation_for_invalid_json_and_allows_retry() -> None:
    """验证 Action Input 非法 JSON 时，会把错误作为 Observation 反馈给模型。"""

    agent = _build_agent(
        [
            'Thought: 我需要计算\nAction: calculator\nAction Input: not-json',
            'Thought: 重新给出合法 JSON\nAction: calculator\nAction Input: {"expression": "2 + 3 * 4"}',
            "Thought: 已得到结果\nFinal Answer: 结果是 14。",
        ]
    )

    result = agent.run("帮我计算 2 + 3 * 4")

    assert result == "结果是 14。"
    llm = agent.llm
    assert "Observation: Action Input 不是合法 JSON，请重新给出合法工具调用。" in llm.calls[1][-1].content
    assert agent.get_trace()[0]["observation"] == "Observation: Action Input 不是合法 JSON，请重新给出合法工具调用。"


def test_react_agent_returns_observation_for_unknown_tool_and_allows_retry() -> None:
    """验证未知工具错误会回到模型上下文中，模型可以修正后继续。"""

    agent = _build_agent(
        [
            'Thought: 先调用一个不存在的工具\nAction: missing\nAction Input: {"expression": "2 + 3"}',
            'Thought: 换成 calculator\nAction: calculator\nAction Input: {"expression": "2 + 3"}',
            "Thought: 已得到答案\nFinal Answer: 结果是 5。",
        ]
    )

    result = agent.run("帮我计算 2 + 3")

    assert result == "结果是 5。"
    llm = agent.llm
    assert "Observation: Unknown tool: missing" in llm.calls[1][-1].content
    assert agent.get_trace()[0]["action"] == "missing"
    assert agent.get_trace()[0]["observation"] == "Observation: Unknown tool: missing"


def test_react_agent_stops_after_max_iterations() -> None:
    """验证模型持续不给出 Final Answer 时，不会无限循环。"""

    agent = _build_agent(
        [
            "Thought: 我还要继续想",
            "Thought: 我还没准备好",
        ],
        max_iterations=2,
    )

    result = agent.run("请开始思考")

    assert result == "抱歉，我在最大迭代次数内仍未完成任务。"
    trace = agent.get_trace()
    assert len(trace) == 2
    assert trace[0]["observation"] == "Observation: 未检测到 Action，请按照 ReAct 格式继续。"
    assert trace[1]["observation"] == "Observation: 未检测到 Action，请按照 ReAct 格式继续。"


def test_react_agent_prefers_final_answer_when_action_and_final_answer_appear_together() -> None:
    """验证同时出现 Action 和 Final Answer 时，当前实现优先结束并返回最终答案。"""

    agent = _build_agent(
        [
            'Thought: 我已经知道答案\nAction: calculator\nAction Input: {"expression": "1 + 1"}\nFinal Answer: 结果是 2。',
        ]
    )

    result = agent.run("1 + 1 等于多少？")

    assert result == "结果是 2。"
    trace = agent.get_trace()
    assert len(trace) == 1
    assert trace[0]["final_answer"] == "结果是 2。"
    assert trace[0]["observation"] == ""
