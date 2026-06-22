"""阶段十一到阶段十二测试：验证轻量版记忆系统与工具接入。"""

from __future__ import annotations

from my_agents.agents.tool_agent import ToolAgent
from my_agents.memory.simple_memory import SimpleMemory
from my_agents.tools.builtin.memory_tool import MemoryTool
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM


def test_simple_memory_add_and_search_by_keyword() -> None:
    """验证 SimpleMemory 可以按关键词命中显式记忆。"""

    memory = SimpleMemory()
    memory.add("用户叫张三，正在学习 Agent 开发")

    by_name = memory.search("张三")
    by_topic = memory.search("Agent 开发")

    assert [item.content for item in by_name] == ["用户叫张三，正在学习 Agent 开发"]
    assert [item.content for item in by_topic] == ["用户叫张三，正在学习 Agent 开发"]


def test_simple_memory_delete_and_clear() -> None:
    """验证删除单条记忆与清空记忆都能正常工作。"""

    memory = SimpleMemory()
    first = memory.add("用户叫张三")
    memory.add("用户正在学习 Agent 开发")

    deleted = memory.delete(first.id)
    remaining = memory.list_all()

    assert deleted is True
    assert [item.content for item in remaining] == ["用户正在学习 Agent 开发"]

    memory.clear()
    assert memory.list_all() == []


def test_memory_tool_supports_add_search_summary_and_clear() -> None:
    """验证 MemoryTool 对外暴露的四个操作都可用。"""

    memory = SimpleMemory()
    tool = MemoryTool(memory=memory)

    add_result = tool.run({"action": "add", "content": "用户叫张三，正在学习 Agent 开发"})
    search_result = tool.run({"action": "search", "query": "Agent 开发"})
    summary_result = tool.run({"action": "summary"})
    clear_result = tool.run({"action": "clear"})

    assert add_result.ok is True
    assert add_result.content == "用户叫张三，正在学习 Agent 开发"
    assert search_result.ok is True
    assert search_result.content == "用户叫张三，正在学习 Agent 开发"
    assert summary_result.ok is True
    assert "- 用户叫张三，正在学习 Agent 开发" in summary_result.content
    assert clear_result.ok is True
    assert clear_result.content == "记忆已清空。"
    assert memory.list_all() == []


def test_memory_tool_returns_clear_error_for_missing_query() -> None:
    """验证 search 缺少 query 时返回明确错误。"""

    tool = MemoryTool(memory=SimpleMemory())

    result = tool.run({"action": "search"})

    assert result.ok is False
    assert result.error == "memory.search 需要非空 query"


def test_tool_agent_can_use_memory_tool_across_multiple_turns() -> None:
    """验证同一个 ToolAgent 可以跨轮写入并检索长期记忆。"""

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

    first_result = agent.run("请记住我叫张三，正在学习 Agent 开发")
    second_result = agent.run("我现在在学习什么？")

    assert first_result == "好的，我记住了。"
    assert second_result == "你正在学习 Agent 开发。"
    assert [item.content for item in memory.list_all()] == [
        "用户叫张三，正在学习 Agent 开发"
    ]
