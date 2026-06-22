"""阶段九到阶段十示例：演示 ReActAgent 的多步工具调用。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_agents.agents.react_agent import ReActAgent
from my_agents.tools.builtin.calculator import CalculatorTool
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM


def main() -> None:
    """运行一次典型的 ReAct 多步推理示例。"""

    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())

    llm = FakeLLM(
        [
            'Thought: 需要先计算 15 * 23\nAction: calculator\nAction Input: {"expression": "15 * 23"}',
            "Thought: 345 不是偶数\nFinal Answer: 15 * 23 = 345，345 不是偶数。",
        ]
    )

    agent = ReActAgent(
        name="ReAct 助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个帮助用户逐步推理的助手。",
        max_iterations=3,
    )

    print(agent.run("请计算 15 * 23，然后判断结果是不是偶数。"))
    print(agent.get_trace())


if __name__ == "__main__":
    main()
