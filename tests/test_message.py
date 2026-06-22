"""阶段二测试：验证统一消息结构是否满足后续框架需要。"""

import pytest

from my_agents.core.message import Message, MessageRole


def test_create_user_message() -> None:
    """验证可以正确创建 user 消息。"""

    message = Message(role=MessageRole.USER, content="你好")

    assert message.role is MessageRole.USER
    assert message.content == "你好"


def test_create_assistant_message() -> None:
    """验证可以正确创建 assistant 消息。"""

    message = Message(role=MessageRole.ASSISTANT, content="你好，有什么可以帮你？")

    assert message.role is MessageRole.ASSISTANT
    assert message.content == "你好，有什么可以帮你？"


def test_to_dict_matches_openai_message_format() -> None:
    """验证 Message 能稳定转换成 OpenAI 风格的消息字典。"""

    message = Message(role=MessageRole.USER, content="请介绍 Agent")

    assert message.to_dict() == {
        "role": "user",
        "content": "请介绍 Agent",
    }


def test_from_dict_restores_message() -> None:
    """验证原始字典可以恢复成 Message 对象。"""

    message = Message.from_dict({"role": "assistant", "content": "Agent 是一种能行动的系统。"})

    assert message.role is MessageRole.ASSISTANT
    assert message.content == "Agent 是一种能行动的系统。"


def test_invalid_role_raises_value_error() -> None:
    """验证非法角色会被拒绝，避免脏数据进入框架主流程。"""

    with pytest.raises(ValueError):
        Message.from_dict({"role": "developer", "content": "not supported"})
