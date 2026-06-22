"""阶段七测试：验证 CalculatorTool 的安全计算行为。"""

from __future__ import annotations

from my_agents.tools.builtin.calculator import CalculatorTool


def test_calculator_returns_expected_result_for_basic_expression() -> None:
    """验证基础表达式可以正确计算。"""

    calculator = CalculatorTool()

    result = calculator.run({"expression": "2 + 3 * 4"})

    assert result.ok is True
    assert result.content == "14"
    assert result.error == ""


def test_calculator_supports_parentheses_and_unary_operator() -> None:
    """验证括号和一元正负号可以正常工作。"""

    calculator = CalculatorTool()

    result = calculator.run({"expression": "-(2 + 3) * 4"})

    assert result.ok is True
    assert result.content == "-20"


def test_calculator_rejects_disallowed_syntax() -> None:
    """验证函数调用等不在白名单中的语法会被拒绝。"""

    calculator = CalculatorTool()

    result = calculator.run({"expression": "__import__('os').system('pwd')"})

    assert result.ok is False
    assert result.content == ""
    assert "表达式包含不被允许的语法" == result.error


def test_calculator_rejects_division_by_zero() -> None:
    """验证除以 0 会返回清晰错误。"""

    calculator = CalculatorTool()

    result = calculator.run({"expression": "1 / 0"})

    assert result.ok is False
    assert result.content == ""
    assert result.error == "不允许除以 0"
