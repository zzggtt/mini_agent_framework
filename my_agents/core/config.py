"""阶段五：定义真实模型调用所需的配置对象。

这一轮要解决的问题是：
1. 把模型配置从 Agent 和 LLM 行为里拆出来，形成独立的数据对象。
2. 统一管理 model、api_key、base_url、temperature 等参数。
3. 让配置既可以从环境变量读取，也可以在代码里显式传入。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL = "deepseek-v3-2-251201"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_TEMPERATURE = 0.7


@dataclass(slots=True)
class Config:
    """保存一次真实模型调用所需的最小配置。"""

    model: str = DEFAULT_MODEL
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        """对关键配置做最小规范化，避免后续请求阶段再分散处理。"""

        self.model = self.model.strip()
        self.api_key = self.api_key.strip()
        self.base_url = self.base_url.strip()

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量读取配置，并在缺少关键字段时给出清晰报错。"""

        api_key = os.getenv("ARK_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "缺少 ARK_API_KEY，请先在 .env 或环境变量中配置真实模型密钥。"
            )

        model = os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        base_url = os.getenv("ARK_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
        temperature = cls._read_float_from_env(
            "TEMPERATURE",
            DEFAULT_TEMPERATURE,
        )
        max_tokens = cls._read_optional_int_from_env("MAX_TOKENS")

        return cls(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @staticmethod
    def _read_float_from_env(name: str, default: float) -> float:
        """从环境变量读取浮点值；未配置时返回默认值。"""

        raw_value = os.getenv(name, "").strip()
        if not raw_value:
            return default

        try:
            return float(raw_value)
        except ValueError as exc:
            raise ValueError(f"{name} 必须是合法浮点数，当前值为: {raw_value}") from exc

    @staticmethod
    def _read_optional_int_from_env(name: str) -> int | None:
        """从环境变量读取可选整数；未配置时返回 None。"""

        raw_value = os.getenv(name, "").strip()
        if not raw_value:
            return None

        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{name} 必须是合法整数，当前值为: {raw_value}") from exc
