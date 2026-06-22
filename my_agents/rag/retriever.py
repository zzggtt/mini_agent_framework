"""阶段十四：实现简化版关键词 Retriever。

这一轮要解决的问题是：
1. 在没有向量数据库的前提下，先完成最小可用的文本检索。
2. 支持按 query 对 chunks 打分，并返回 top_k 结果。
3. 让搜索结果同时携带 source、score、content 和 metadata。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from my_agents.rag.splitter import DocumentChunk

TOKEN_RE = re.compile(r"[a-zA-Z0-9_+-]+|[\u4e00-\u9fff]+")


@dataclass(slots=True)
class RetrievedChunk:
    """表示一次检索命中的 chunk 及其分数。"""

    content: str
    source: str
    score: int
    metadata: dict[str, Any] = field(default_factory=dict)


class KeywordRetriever:
    """基于关键词匹配和简单打分实现第一版检索。"""

    def __init__(self, chunks: list[DocumentChunk] | None = None) -> None:
        """初始化检索器，并可选直接注入已有 chunks。"""

        self._chunks: list[DocumentChunk] = list(chunks or [])

    def set_chunks(self, chunks: list[DocumentChunk]) -> None:
        """替换当前检索语料，适合在知识库重新加载后调用。"""

        self._chunks = list(chunks)

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """向当前检索语料追加新的 chunks。"""

        self._chunks.extend(chunks)

    def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        """按 query 检索相关 chunks，并返回分数最高的前 top_k 条。"""

        normalized_query = query.strip()
        if not normalized_query or top_k <= 0:
            return []

        query_tokens = self._tokenize(normalized_query)
        scored_chunks: list[tuple[int, int, DocumentChunk]] = []

        for index, chunk in enumerate(self._chunks):
            score = self._score_chunk(normalized_query, query_tokens, chunk)
            if score > 0:
                scored_chunks.append((score, index, chunk))

        scored_chunks.sort(key=lambda item: (-item[0], item[1]))
        return [
            RetrievedChunk(
                content=chunk.content,
                source=chunk.source,
                score=score,
                metadata=dict(chunk.metadata),
            )
            for score, _, chunk in scored_chunks[:top_k]
        ]

    def _score_chunk(
        self,
        query: str,
        query_tokens: list[str],
        chunk: DocumentChunk,
    ) -> int:
        """计算单个 chunk 与 query 的简单相关度分数。"""

        content = chunk.content.casefold()
        source = chunk.source.casefold()
        heading = str(chunk.metadata.get("heading", "")).casefold()
        normalized_query = query.casefold()

        score = 0
        if normalized_query in content:
            score += len(normalized_query) * 10

        for token in query_tokens:
            if token in content:
                score += len(token) * 3
            if token in heading:
                score += len(token) * 2
            if token in source:
                score += len(token)

        return score

    def _tokenize(self, text: str) -> list[str]:
        """把 query 拆成英文词和中文二元片段，提升第一版召回率。"""

        tokens: list[str] = []
        for part in TOKEN_RE.findall(text.casefold()):
            if re.fullmatch(r"[a-zA-Z0-9_+-]+", part):
                tokens.append(part)
                continue

            if len(part) <= 2:
                tokens.append(part)
                continue

            for index in range(len(part) - 1):
                tokens.append(part[index : index + 2])

        deduplicated_tokens: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            if token and token not in seen:
                deduplicated_tokens.append(token)
                seen.add(token)
        return deduplicated_tokens
