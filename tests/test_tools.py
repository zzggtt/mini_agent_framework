"""阶段六测试：验证工具系统的注册、执行和错误包装。"""

from __future__ import annotations

import pytest

from my_agents.tools.base import Tool, ToolParameter
from my_agents.tools.registry import ToolRegistry
from my_agents.tools.result import ToolResult


class EchoTool(Tool):
    """一个最小测试工具：原样返回输入文本。"""

    name = "echo"
    description = "原样返回输入内容"
    parameters = [
        ToolParameter(
            name="text",
            type="string",
            description="要原样返回的文本内容",
        )
    ]

    def run(self, parameters: dict[str, str]) -> str:
        """读取 text 参数并直接返回。"""

        return parameters["text"]


class ResultTool(Tool):
    """用于验证 registry 支持工具直接返回 ToolResult。"""

    name = "result_tool"
    description = "直接返回 ToolResult"

    def run(self, parameters: dict[str, str]) -> ToolResult:
        """直接产出一个成功的 ToolResult。"""

        return ToolResult(ok=True, content=parameters["text"], metadata={"source": "tool"})


class ErrorTool(Tool):
    """用于验证工具执行异常会被统一包装。"""

    name = "error_tool"
    description = "执行时抛出异常"

    def run(self, parameters: dict[str, str]) -> str:
        """模拟工具内部执行失败。"""

        raise RuntimeError("boom")


def test_register_and_execute_tool_returns_success_result() -> None:
    """验证注册后的工具可以执行，并被包装成成功结果。"""

    registry = ToolRegistry()
    registry.register_tool(EchoTool())

    result = registry.execute("echo", {"text": "hello"})

    assert result.ok is True
    assert result.content == "hello"
    assert result.error == ""


def test_get_tool_returns_registered_tool() -> None:
    """验证可以通过名称取回已注册工具。"""

    registry = ToolRegistry()
    tool = EchoTool()
    registry.register_tool(tool)

    assert registry.get_tool("echo") is tool


def test_execute_unknown_tool_returns_clear_error() -> None:
    """验证调用未注册工具时，会返回清晰错误而不是抛异常。"""

    registry = ToolRegistry()

    result = registry.execute("missing", {"text": "hello"})

    assert result.ok is False
    assert result.content == ""
    assert result.error == "Unknown tool: missing"


def test_register_duplicate_tool_raises_value_error() -> None:
    """验证重复注册同名工具时行为明确。"""

    registry = ToolRegistry()
    registry.register_tool(EchoTool())

    with pytest.raises(ValueError, match="工具已注册：echo"):
        registry.register_tool(EchoTool())


def test_get_tools_description_includes_name_and_description() -> None:
    """验证工具说明文本中包含名称和描述。"""

    registry = ToolRegistry()
    registry.register_tool(EchoTool())

    descriptions = registry.get_tools_description()

    assert "echo" in descriptions
    assert "原样返回输入内容" in descriptions


def test_execute_tool_exception_is_wrapped_as_failed_result() -> None:
    """验证工具内部异常会被包装为失败结果。"""

    registry = ToolRegistry()
    registry.register_tool(ErrorTool())

    result = registry.execute("error_tool", {})

    assert result.ok is False
    assert result.content == ""
    assert "Tool execution failed: error_tool: boom" == result.error


def test_execute_supports_tool_returning_toolresult_directly() -> None:
    """验证 registry 支持工具直接返回 ToolResult。"""

    registry = ToolRegistry()
    registry.register_tool(ResultTool())

    result = registry.execute("result_tool", {"text": "hello"})

    assert result.ok is True
    assert result.content == "hello"
    assert result.metadata == {"source": "tool"}


def test_tool_parameter_schema_is_exposed_by_get_parameters() -> None:
    """验证工具可以暴露自己的参数 schema。"""

    tool = EchoTool()

    assert tool.get_parameters() == {
        "text": {
            "type": "string",
            "description": "要原样返回的文本内容",
            "required": True,
        }
    }
