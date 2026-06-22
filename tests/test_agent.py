"""阶段四测试：验证最小对话 Agent 的主循环和状态管理。"""

from my_agents.agents.simple_agent import SimpleAgent
from my_agents.core.message import MessageRole
from tests.fakes import FakeLLM


def test_simple_agent_returns_first_response() -> None:
    """验证第一次对话能正常返回模型回复。"""

    agent = SimpleAgent(
        name="学习助手",
        llm=FakeLLM(["你好，我是学习助手。"]),
        system_prompt="你是一个帮助用户学习 Agent 开发的助手。",
    )

    result = agent.run("你好，请介绍一下你自己")

    assert result == "你好，我是学习助手。"


def test_simple_agent_uses_system_prompt_and_history_on_second_turn() -> None:
    """验证第二轮对话时，会把 system prompt 和历史消息一起传给模型。"""

    fake_llm = FakeLLM(["你好，我是学习助手。", "你刚才问我介绍自己。"])
    agent = SimpleAgent(
        name="学习助手",
        llm=fake_llm,
        system_prompt="你是一个帮助用户学习 Agent 开发的助手。",
    )

    agent.run("你好，请介绍一下你自己")
    agent.run("我刚才问了什么？")

    second_call = fake_llm.calls[1]

    assert [message.role for message in second_call] == [
        MessageRole.SYSTEM,
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.USER,
    ]
    assert [message.content for message in second_call] == [
        "你是一个帮助用户学习 Agent 开发的助手。",
        "你好，请介绍一下你自己",
        "你好，我是学习助手。",
        "我刚才问了什么？",
    ]


def test_get_history_contains_user_and_assistant_messages() -> None:
    """验证一轮对话结束后，history 中会保存 user 和 assistant 消息。"""

    agent = SimpleAgent(
        name="学习助手",
        llm=FakeLLM(["你好，我是学习助手。"]),
        system_prompt="你是一个帮助用户学习 Agent 开发的助手。",
    )

    agent.run("你好，请介绍一下你自己")
    history = agent.get_history()

    assert len(history) == 2
    assert [message.role for message in history] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
    ]


def test_clear_history_removes_all_messages() -> None:
    """验证 clear_history() 能清空当前会话状态。"""

    agent = SimpleAgent(
        name="学习助手",
        llm=FakeLLM(["你好，我是学习助手。"]),
        system_prompt="你是一个帮助用户学习 Agent 开发的助手。",
    )

    agent.run("你好，请介绍一下你自己")
    agent.clear_history()

    assert agent.get_history() == []
