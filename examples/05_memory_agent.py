"""阶段十一到阶段十二示例：演示显式记忆写入与检索。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_agents.agents.tool_agent import ToolAgent
from my_agents.memory.simple_memory import SimpleMemory
from my_agents.tools.builtin.memory_tool import MemoryTool
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM


def main() -> None:
    """演示 Agent 如何通过 memory 工具完成显式记忆。"""

    memory = SimpleMemory()
    registry = ToolRegistry()
    registry.register_tool(MemoryTool(memory=memory))

    llm = FakeLLM(
        [
            'Action: memory\nAction Input: {"action": "add", "content": "用户叫张三，正在学习 Agent 开发"}',
            "Final Answer: 好的，我记住了。",
            'Action: memory\nAction Input: {"action": "search", "query": "Agent 开发"}',
            "Final Answer: 你正在学习 Agent 开发。",
        ]
    )

    agent = ToolAgent(
        name="记忆助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个会使用记忆工具的助手。",
    )

    print(agent.run("请记住我叫张三，正在学习 Agent 开发"))
    print(agent.run("我现在在学习什么？"))


if __name__ == "__main__":
    main()
