"""阶段四示例：演示 SimpleAgent 如何与 FakeLLM 配合工作。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 直接运行 examples 目录下的脚本时，手动把项目根目录加入导入路径，
# 避免找不到 `my_agents` 包。
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_agents.agents.simple_agent import SimpleAgent
from tests.fakes import FakeLLM


def main() -> None:
    """运行一个两轮对话示例，帮助理解 history 的累积过程。"""

    agent = SimpleAgent(
        name="学习助手",
        llm=FakeLLM(["你好，我是学习助手。", "你刚才问我介绍自己。"]),
        system_prompt="你是一个帮助用户学习 Agent 开发的助手。",
    )

    print(agent.run("你好，请介绍一下你自己"))
    print(agent.run("我刚才问了什么？"))
    print(len(agent.get_history()))


if __name__ == "__main__":
    main()
