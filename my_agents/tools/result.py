"""阶段六：统一工具执行结果。

这一轮要解决的问题是：
1. 避免不同工具返回值风格不一致，污染后续 Agent 主循环。
2. 把成功结果、错误信息和附加元数据放进统一结构里。
3. 让 ToolRegistry 能稳定包装未知工具和工具执行异常。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolResult:
    """表示一次工具执行后的统一结果。"""

    ok: bool
    content: Any = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
