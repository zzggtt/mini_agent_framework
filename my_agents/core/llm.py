"""阶段五：封装真实模型调用层。

这一轮要解决的问题是：
1. Agent 只依赖统一的 llm.chat(messages) 接口，而不直接接触 OpenAI SDK。
2. 把 Message 对象转换成模型接口能识别的请求格式。
3. 把模型响应中的文本内容提取成框架内部统一使用的字符串。
"""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from my_agents.core.config import Config
from my_agents.core.message import Message


class LLM:
    """对真实聊天模型进行最小封装。"""

    def __init__(self, config: Config | None = None, client: Any | None = None) -> None:
        """初始化真实模型调用器。

        设计目的：
        1. `config` 负责提供模型、密钥、地址和采样参数。
        2. `client` 默认使用 OpenAI SDK 创建，测试时也可以注入假客户端。
        """

        self.config = config or Config.from_env()
        self.client = client or OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    def chat(self, messages: list[Message]) -> str:
        """发送一组消息给模型，并提取文本回复。"""

        payload = [message.to_dict() for message in messages]
        request_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": payload,
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            request_kwargs["max_tokens"] = self.config.max_tokens

        response = self.client.chat.completions.create(**request_kwargs)
        return self._extract_response_text(response)

    def _extract_response_text(self, response: Any) -> str:
        """从 OpenAI 风格响应中提取 assistant 文本内容。"""

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError) as exc:
            raise ValueError("模型响应格式不合法，无法读取 assistant 内容。") from exc

        text = self._normalize_content_to_text(content)
        if not text:
            raise ValueError("模型返回了空内容，当前框架只支持文本回复。")
        return text

    @staticmethod
    def _normalize_content_to_text(content: Any) -> str:
        """把不同形式的 content 统一整理成纯文本。"""

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_value = item.get("text", "")
                    if text_value:
                        text_parts.append(str(text_value))
            return "".join(text_parts).strip()

        return ""
