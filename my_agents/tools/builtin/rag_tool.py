"""阶段十三到阶段十四：把本地检索能力包装成 RAGTool。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from my_agents.rag.document import Document, DocumentLoader
from my_agents.rag.retriever import KeywordRetriever, RetrievedChunk
from my_agents.rag.splitter import CharacterTextSplitter, DocumentChunk
from my_agents.tools.base import Tool, ToolParameter
from my_agents.tools.result import ToolResult


class RAGTool(Tool):
    """通过统一工具协议暴露 load / search 两个 RAG 动作。"""

    name = "rag"
    description = "加载本地知识库，并检索与问题相关的文档片段。"
    parameters = [
        ToolParameter(
            name="action",
            type="string",
            description="要执行的 RAG 操作：load 或 search",
        ),
        ToolParameter(
            name="path",
            type="string",
            description="load 时要读取的文件或目录路径；search 时可选用于懒加载",
            required=False,
        ),
        ToolParameter(
            name="query",
            type="string",
            description="search 操作使用的查询文本",
            required=False,
        ),
        ToolParameter(
            name="top_k",
            type="integer",
            description="search 操作返回的最大片段数",
            required=False,
        ),
        ToolParameter(
            name="chunk_size",
            type="integer",
            description="load 时的 chunk 大小",
            required=False,
        ),
        ToolParameter(
            name="chunk_overlap",
            type="integer",
            description="load 时相邻 chunk 的重叠字符数",
            required=False,
        ),
    ]

    def __init__(
        self,
        knowledge_base_path: str | Path | None = None,
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        use_headings: bool = True,
    ) -> None:
        """初始化 RAGTool，并可选直接预加载一个本地知识库。"""

        self.loader = DocumentLoader()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_headings = use_headings
        self.documents: list[Document] = []
        self.chunks: list[DocumentChunk] = []
        self.retriever = KeywordRetriever()
        self.knowledge_base_path: str = ""

        if knowledge_base_path is not None:
            self.load_knowledge_base(knowledge_base_path)

    def run(self, parameters: dict[str, Any]) -> ToolResult:
        """根据 action 分发到知识库加载或检索逻辑。"""

        action = str(parameters.get("action", "")).strip().lower()
        if action == "load":
            return self._load(parameters)
        if action == "search":
            return self._search(parameters)
        return ToolResult(ok=False, content="", error=f"不支持的 rag action: {action}")

    def load_knowledge_base(
        self,
        path: str | Path,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> ToolResult:
        """加载本地知识库，并重新建立切分结果和检索索引。"""

        resolved_path = Path(path).expanduser().resolve()
        splitter = CharacterTextSplitter(
            chunk_size=chunk_size or self.chunk_size,
            chunk_overlap=chunk_overlap if chunk_overlap is not None else self.chunk_overlap,
            use_headings=self.use_headings,
        )

        documents = self.loader.load_path(resolved_path)
        chunks = splitter.split_documents(documents)

        self.documents = documents
        self.chunks = chunks
        self.retriever.set_chunks(chunks)
        self.knowledge_base_path = str(resolved_path)

        return ToolResult(
            ok=True,
            content=f"已加载 {len(documents)} 个文档，生成 {len(chunks)} 个 chunks。",
            metadata={
                "path": str(resolved_path),
                "document_count": len(documents),
                "chunk_count": len(chunks),
            },
        )

    def _load(self, parameters: dict[str, Any]) -> ToolResult:
        """处理显式 load 动作。"""

        raw_path = str(parameters.get("path", "")).strip()
        if not raw_path:
            return ToolResult(ok=False, content="", error="rag.load 需要非空 path")

        chunk_size = self._read_optional_int(parameters, "chunk_size")
        chunk_overlap = self._read_optional_int(parameters, "chunk_overlap")

        try:
            return self.load_knowledge_base(
                path=raw_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        except Exception as exc:
            return ToolResult(ok=False, content="", error=f"rag.load 执行失败: {exc}")

    def _search(self, parameters: dict[str, Any]) -> ToolResult:
        """处理 search 动作，并返回相关 chunks 而不是最终答案。"""

        query = str(parameters.get("query", "")).strip()
        if not query:
            return ToolResult(ok=False, content="", error="rag.search 需要非空 query")

        raw_path = str(parameters.get("path", "")).strip()
        if raw_path:
            load_result = self._load(parameters)
            if not load_result.ok:
                return load_result

        if not self.chunks:
            return ToolResult(ok=False, content="", error="知识库尚未加载，请先执行 rag.load")

        top_k = self._read_optional_int(parameters, "top_k") or 3
        results = self.retriever.search(query=query, top_k=top_k)
        if not results:
            return ToolResult(
                ok=True,
                content="知识库中没有足够信息。",
                metadata={"results": [], "count": 0, "query": query},
            )

        return ToolResult(
            ok=True,
            content=self._format_results(results),
            metadata={
                "results": [self._serialize_result(result) for result in results],
                "count": len(results),
                "query": query,
            },
        )

    @staticmethod
    def _format_results(results: list[RetrievedChunk]) -> str:
        """把检索命中的 chunks 格式化成适合注入 prompt 的文本。"""

        lines: list[str] = []
        for index, result in enumerate(results, start=1):
            lines.append(
                f"[{index}] source: {result.source} | score: {result.score}\n"
                f"content: {result.content}"
            )
        return "\n\n".join(lines)

    @staticmethod
    def _serialize_result(result: RetrievedChunk) -> dict[str, Any]:
        """把检索结果转成便于测试和调试的字典结构。"""

        return {
            "source": result.source,
            "score": result.score,
            "content": result.content,
            "metadata": dict(result.metadata),
        }

    @staticmethod
    def _read_optional_int(parameters: dict[str, Any], key: str) -> int | None:
        """把可选整数字段从参数字典中解析出来。"""

        value = parameters.get(key)
        if value is None or value == "":
            return None
        return int(value)
