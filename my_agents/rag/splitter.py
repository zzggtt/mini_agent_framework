"""阶段十三：实现简化版文档切分器。

这一轮要解决的问题是：
1. 把长文档切成更短的 chunk，便于后续检索。
2. 第一版支持按字符数切分，并可选先按 Markdown 标题分段。
3. 为每个 chunk 保留 source、chunk_index、标题等元数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from my_agents.rag.document import Document

HEADING_RE = re.compile(r"^(#{1,6}\s+.+)$", re.MULTILINE)


@dataclass(slots=True)
class DocumentChunk:
    """表示一段可被检索的文档切片。"""

    content: str
    source: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


class CharacterTextSplitter:
    """使用字符窗口切分文档，并可选感知 Markdown 标题。"""

    def __init__(
        self,
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        use_headings: bool = True,
    ) -> None:
        """初始化切分参数，并校验窗口配置是否合法。"""

        if chunk_size <= 0:
            raise ValueError("chunk_size 必须大于 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap 不能小于 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_headings = use_headings

    def split_documents(self, documents: list[Document]) -> list[DocumentChunk]:
        """批量切分多份文档，并返回扁平化后的全部 chunks。"""

        chunks: list[DocumentChunk] = []
        for document in documents:
            chunks.extend(self.split_document(document))
        return chunks

    def split_document(self, document: Document) -> list[DocumentChunk]:
        """切分单份文档，并给每个 chunk 附加来源元数据。"""

        if not document.content.strip():
            return []

        sections = self._split_sections(document.content)
        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for heading, section_text in sections:
            for start, end, chunk_text in self._slice_text(section_text):
                metadata = dict(document.metadata)
                metadata.update(
                    {
                        "start_char": start,
                        "end_char": end,
                    }
                )
                if heading:
                    metadata["heading"] = heading

                chunks.append(
                    DocumentChunk(
                        content=chunk_text,
                        source=document.source,
                        chunk_index=chunk_index,
                        metadata=metadata,
                    )
                )
                chunk_index += 1

        return chunks

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        """按标题预切分文档；关闭时返回单个整文 section。"""

        if not self.use_headings:
            return [("", text.strip())]

        matches = list(HEADING_RE.finditer(text))
        if not matches:
            return [("", text.strip())]

        sections: list[tuple[str, str]] = []
        leading_text = text[: matches[0].start()].strip()
        if leading_text:
            sections.append(("", leading_text))

        for index, match in enumerate(matches):
            heading = match.group(1).strip()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            section_text = heading if not body else f"{heading}\n{body}"
            sections.append((heading, section_text.strip()))

        return [section for section in sections if section[1]]

    def _slice_text(self, text: str) -> list[tuple[int, int, str]]:
        """按字符窗口把 section 进一步切成多个 chunk。"""

        normalized_text = text.strip()
        if not normalized_text:
            return []

        slices: list[tuple[int, int, str]] = []
        start = 0
        text_length = len(normalized_text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk_text = normalized_text[start:end].strip()
            if chunk_text:
                slices.append((start, end, chunk_text))
            if end >= text_length:
                break
            start = end - self.chunk_overlap

        return slices
