"""阶段十一到阶段十二：实现轻量版显式记忆系统。

这一轮要解决的问题是：
1. 提供最小可用的长期记忆容器，支持新增、检索、枚举、删除和清空。
2. 第一版检索坚持关键词边界，不假装支持复杂语义理解。
3. 让 MemoryTool 后续只负责工具协议，而不重写底层记忆逻辑。
"""

from __future__ import annotations

import re

from my_agents.memory.memory_item import MemoryItem


class SimpleMemory:
    """用内存列表保存显式记忆，并提供基础关键词检索。"""

    def __init__(self) -> None:
        """初始化一个空的记忆仓库。"""

        self._items: list[MemoryItem] = []

    def add(
        self,
        content: str,
        memory_type: str = "semantic",
        importance: float = 1.0,
        metadata: dict[str, object] | None = None,
    ) -> MemoryItem:
        """新增一条记忆，并返回创建后的 MemoryItem。"""

        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("content 不能为空")

        item = MemoryItem(
            content=normalized_content,
            memory_type=memory_type,
            importance=importance,
            metadata=dict(metadata or {}),
        )
        self._items.append(item)
        return item

    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        """按关键词匹配记忆条目，并按相关度从高到低返回。"""

        normalized_query = query.strip()
        if not normalized_query or limit <= 0:
            return []

        scored_items: list[tuple[int, int, MemoryItem]] = []
        query_tokens = self._tokenize(normalized_query)

        for index, item in enumerate(self._items):
            score = self._score(normalized_query, query_tokens, item.content)
            if score > 0:
                scored_items.append((score, index, item))

        scored_items.sort(key=lambda entry: (-entry[0], -entry[1]))
        return [item for _, _, item in scored_items[:limit]]

    def list_all(self) -> list[MemoryItem]:
        """返回全部记忆条目的副本，避免外部直接修改内部列表。"""

        return list(self._items)

    def delete(self, memory_id: str) -> bool:
        """按 id 删除记忆；删除成功返回 True。"""

        for index, item in enumerate(self._items):
            if item.id == memory_id:
                del self._items[index]
                return True
        return False

    def clear(self) -> None:
        """清空全部记忆。"""

        self._items.clear()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """把查询切成最小关键词，用于第一版简单匹配。"""

        return [token for token in re.split(r"\s+", text) if token]

    def _score(self, query: str, query_tokens: list[str], content: str) -> int:
        """计算一条记忆与查询的简单匹配分数。"""

        score = 0
        if query in content:
            score += len(query) * 10

        for token in query_tokens:
            if token in content:
                score += len(token)

        return score
