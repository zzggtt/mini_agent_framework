"""阶段八示例：演示 ToolAgent 的单次工具调用链路。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_agents.agents.tool_agent import ToolAgent
from my_agents.tools.builtin.calculator import CalculatorTool
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM


def main() -> None:
    """运行一次模型决定调用 calculator 的最小示例。"""

    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())

    llm = FakeLLM(
        [
            'Action: calculator\nAction Input: {"expression": "2 + 3 * 4"}',
            "Final Answer: 计算结果是 14。",
        ]
    )

    agent = ToolAgent(
        name="工具助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个帮助用户调用工具的助手。",
    )

    print(agent.run("帮我计算 2 + 3 * 4"))


if __name__ == "__main__":
    main()
