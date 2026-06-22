"""阶段十三：定义 RAG 使用的最小文档结构与加载器。

这一轮要解决的问题是：
1. 把知识库原始文本抽象成统一的 Document 对象。
2. 让本地 `.md` / `.txt` 文件可以被稳定加载进系统。
3. 为后续切分和检索准备统一输入结构，而不是直接操作文件路径。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Document:
    """表示一份进入 RAG 流程前的原始文档。"""

    content: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentLoader:
    """负责把本地文件系统中的文档加载成 Document。"""

    SUPPORTED_SUFFIXES = {".md", ".txt"}

    def __init__(self, encoding: str = "utf-8") -> None:
        """初始化加载器，并记录默认文件编码。"""

        self.encoding = encoding

    def load_path(self, path: str | Path) -> list[Document]:
        """加载单个文件或整个目录，并统一返回 Document 列表。"""

        resolved_path = Path(path).expanduser().resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"路径不存在：{resolved_path}")

        if resolved_path.is_file():
            return [self.load_file(resolved_path)]

        return self.load_directory(resolved_path)

    def load_file(self, file_path: str | Path) -> Document:
        """加载单个支持的文本文件。"""

        resolved_path = Path(file_path).expanduser().resolve()
        if not resolved_path.is_file():
            raise FileNotFoundError(f"文件不存在：{resolved_path}")
        if not self._is_supported_file(resolved_path):
            raise ValueError(f"暂不支持的文件类型：{resolved_path.suffix}")

        content = resolved_path.read_text(encoding=self.encoding).strip()
        return Document(
            content=content,
            source=resolved_path.name,
            metadata={
                "path": str(resolved_path),
                "suffix": resolved_path.suffix,
            },
        )

    def load_directory(self, directory_path: str | Path) -> list[Document]:
        """递归加载目录下全部支持的文本文件。"""

        resolved_path = Path(directory_path).expanduser().resolve()
        if not resolved_path.is_dir():
            raise NotADirectoryError(f"目录不存在：{resolved_path}")

        documents: list[Document] = []
        for file_path in sorted(resolved_path.rglob("*")):
            if file_path.is_file() and self._is_supported_file(file_path):
                documents.append(self.load_file(file_path))
        return documents

    @classmethod
    def _is_supported_file(cls, path: Path) -> bool:
        """判断给定文件是否属于当前支持的知识库格式。"""

        return path.suffix.lower() in cls.SUPPORTED_SUFFIXES
