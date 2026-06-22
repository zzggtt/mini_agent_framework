"""阶段十一：定义最小可用的记忆条目结构。

这一轮要解决的问题是：
1. 把长期记忆从普通字符串提升为带元数据的结构化对象。
2. 为后续搜索、删除、展示和持久化保留稳定字段。
3. 让 Memory 和 History 在数据结构层面明确分离。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class MemoryItem:
    """表示一条可长期保存的记忆。"""

    content: str
    memory_type: str = "semantic"
    importance: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
