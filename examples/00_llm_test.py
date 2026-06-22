"""阶段五示例：验证真实 LLM 封装是否可以完成一次文本对话。"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_agents.core.llm import LLM
from my_agents.core.message import Message, MessageRole


def main() -> None:
    """加载环境变量并发起一次最小真实模型调用。"""

    load_dotenv()

    llm = LLM()
    response = llm.chat(
        [
            Message(
                role=MessageRole.USER,
                content="请用一句话介绍 Agent 是什么",
            )
        ]
    )
    print(response)


if __name__ == "__main__":
    main()
