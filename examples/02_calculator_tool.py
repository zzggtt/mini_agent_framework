"""阶段七示例：直接运行 CalculatorTool。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_agents.tools.builtin.calculator import CalculatorTool


def main() -> None:
    """演示计算器工具如何独立运行。"""

    calculator = CalculatorTool()
    result = calculator.run({"expression": "2 + 3 * 4"})
    print(result)


if __name__ == "__main__":
    main()
