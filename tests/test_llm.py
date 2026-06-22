"""阶段三与阶段五测试：验证 FakeLLM、Config、LLM 的核心契约。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from my_agents.core.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    Config,
)
from my_agents.core.llm import LLM
from my_agents.core.message import Message, MessageRole
from tests.fakes import FakeLLM


def test_fake_llm_returns_responses_in_order() -> None:
    """验证 FakeLLM 会按队列顺序依次返回预设回复。"""

    fake_llm = FakeLLM(["第一条回复", "第二条回复"])
    messages = [Message(role=MessageRole.USER, content="你好")]

    assert fake_llm.chat(messages) == "第一条回复"
    assert fake_llm.chat(messages) == "第二条回复"


def test_fake_llm_records_each_call_messages() -> None:
    """验证每次 chat 收到的消息都会被记录，便于后续断言上下文。"""

    fake_llm = FakeLLM(["ok"])
    first_messages = [Message(role=MessageRole.USER, content="第一问")]

    fake_llm.chat(first_messages)

    assert fake_llm.calls == [first_messages]


def test_fake_llm_raises_index_error_when_no_responses_left() -> None:
    """验证回复队列耗尽时会快速失败，避免测试静默通过。"""

    fake_llm = FakeLLM([])

    with pytest.raises(IndexError):
        fake_llm.chat([Message(role=MessageRole.USER, content="还在吗？")])


def test_config_from_env_loads_explicit_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 Config 可以从环境变量中读取显式配置值。"""

    monkeypatch.setenv("ARK_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("ARK_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("TEMPERATURE", "0.2")
    monkeypatch.setenv("MAX_TOKENS", "512")

    config = Config.from_env()

    assert config.api_key == "test-key"
    assert config.model == "deepseek-chat"
    assert config.base_url == "https://example.com/v1"
    assert config.temperature == 0.2
    assert config.max_tokens == 512


def test_config_from_env_uses_defaults_for_optional_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证未提供可选配置时，会回落到第一版默认值。"""

    monkeypatch.setenv("ARK_API_KEY", "test-key")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("ARK_BASE_URL", raising=False)
    monkeypatch.delenv("TEMPERATURE", raising=False)
    monkeypatch.delenv("MAX_TOKENS", raising=False)

    config = Config.from_env()

    assert config.model == DEFAULT_MODEL
    assert config.base_url == DEFAULT_BASE_URL
    assert config.temperature == DEFAULT_TEMPERATURE
    assert config.max_tokens is None


def test_config_from_env_raises_clear_error_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证缺少 API Key 时，会给出清晰错误提示。"""

    monkeypatch.delenv("ARK_API_KEY", raising=False)

    with pytest.raises(ValueError, match="缺少 ARK_API_KEY"):
        Config.from_env()


def test_llm_chat_uses_config_and_returns_text() -> None:
    """验证 LLM 会把 Message 转成请求 payload，并返回文本结果。"""

    fake_completions = _FakeCompletions(
        _build_response("Agent 是一种会根据上下文做决策并执行动作的系统。")
    )
    fake_client = _FakeClient(fake_completions)
    llm = LLM(
        config=Config(
            model="gpt-4o-mini",
            api_key="test-key",
            base_url="https://example.com/v1",
            temperature=0.3,
        ),
        client=fake_client,
    )

    result = llm.chat(
        [
            Message(role=MessageRole.SYSTEM, content="你是一个教学助手。"),
            Message(role=MessageRole.USER, content="什么是 Agent？"),
        ]
    )

    assert result == "Agent 是一种会根据上下文做决策并执行动作的系统。"
    assert fake_completions.calls == [
        {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一个教学助手。"},
                {"role": "user", "content": "什么是 Agent？"},
            ],
            "temperature": 0.3,
        }
    ]


def test_llm_chat_includes_max_tokens_when_configured() -> None:
    """验证配置了 max_tokens 时，会显式传递给底层客户端。"""

    fake_completions = _FakeCompletions(_build_response("ok"))
    llm = LLM(
        config=Config(
            api_key="test-key",
            max_tokens=256,
        ),
        client=_FakeClient(fake_completions),
    )

    llm.chat([Message(role=MessageRole.USER, content="你好")])

    assert fake_completions.calls[0]["max_tokens"] == 256


class _FakeCompletions:
    """模拟 OpenAI client.chat.completions 的最小行为。"""

    def __init__(self, response: SimpleNamespace) -> None:
        """保存预设响应，并记录每次 create 调用参数。"""

        self.response = response
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        """记录请求参数，并返回预设响应对象。"""

        self.calls.append(kwargs)
        return self.response


class _FakeClient:
    """模拟 LLM 初始化后实际依赖的最小 client 结构。"""

    def __init__(self, completions: _FakeCompletions) -> None:
        """构造出与 OpenAI SDK 兼容的 chat.completions 访问链。"""

        self.chat = SimpleNamespace(completions=completions)


def _build_response(content: str) -> SimpleNamespace:
    """快速构造一个带 choices[0].message.content 的假响应。"""

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )
