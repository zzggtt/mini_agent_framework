"""阶段七：实现一个安全的计算器工具。

这一轮要解决的问题是：
1. 让工具系统第一次接入真实可执行能力，而不是只停留在 EchoTool 级别。
2. 使用 AST 做安全求值，避免直接执行任意 Python 表达式。
3. 只支持最小可理解的数学能力：加减乘除、括号、一元正负号。
"""

from __future__ import annotations

import ast

from my_agents.tools.base import Tool, ToolParameter
from my_agents.tools.result import ToolResult


class CalculatorTool(Tool):
    """安全计算基础数学表达式。"""

    name = "calculator"
    description = "安全计算数学表达式，只支持加减乘除、括号和一元正负号。"
    parameters = [
        ToolParameter(
            name="expression",
            type="string",
            description="要计算的数学表达式，例如 2 + 3 * 4",
        )
    ]

    def run(self, parameters: dict[str, str]) -> ToolResult:
        """计算表达式，并把结果统一包装成 ToolResult。"""

        expression = parameters.get("expression", "").strip()
        if not expression:
            return ToolResult(ok=False, content="", error="expression 不能为空")

        try:
            node = ast.parse(expression, mode="eval")
            result = self._eval_node(node.body)
        except ZeroDivisionError:
            return ToolResult(ok=False, content="", error="不允许除以 0")
        except (SyntaxError, ValueError, TypeError) as exc:
            return ToolResult(ok=False, content="", error=str(exc))

        return ToolResult(ok=True, content=self._format_number(result))

    def _eval_node(self, node: ast.AST) -> float:
        """递归计算 AST 节点，只接受白名单中的安全表达式。"""

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operand = self._eval_node(node.operand)
            return +operand if isinstance(node.op, ast.UAdd) else -operand

        if isinstance(node, ast.BinOp) and isinstance(
            node.op,
            (ast.Add, ast.Sub, ast.Mult, ast.Div),
        ):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._apply_binary_operator(node.op, left, right)

        raise ValueError("表达式包含不被允许的语法")

    @staticmethod
    def _apply_binary_operator(operator: ast.operator, left: float, right: float) -> float:
        """对二元运算符执行实际计算。"""

        if isinstance(operator, ast.Add):
            return left + right
        if isinstance(operator, ast.Sub):
            return left - right
        if isinstance(operator, ast.Mult):
            return left * right
        if isinstance(operator, ast.Div):
            return left / right
        raise ValueError("不支持的运算符")

    @staticmethod
    def _format_number(value: float) -> str:
        """把计算结果转成适合展示的文本。"""

        if value.is_integer():
            return str(int(value))
        return str(value)
