"""阶段十三到阶段十四测试：验证简化版 RAGTool。"""

from __future__ import annotations

from pathlib import Path

from my_agents.agents.tool_agent import ToolAgent
from my_agents.rag.document import DocumentLoader
from my_agents.rag.retriever import KeywordRetriever
from my_agents.rag.splitter import CharacterTextSplitter
from my_agents.tools.builtin.rag_tool import RAGTool
from my_agents.tools.registry import ToolRegistry
from tests.fakes import FakeLLM

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"


def test_document_loader_can_load_markdown_directory() -> None:
    """验证 DocumentLoader 可以从知识库目录加载 Markdown 文档。"""

    loader = DocumentLoader()

    documents = loader.load_directory(KNOWLEDGE_BASE_DIR)

    assert [document.source for document in documents] == [
        "agent_intro.md",
        "rag.md",
        "react.md",
    ]
    assert "Agent 框架通常包含以下核心模块" in documents[0].content


def test_splitter_keeps_source_and_heading_metadata() -> None:
    """验证切分后的 chunk 会保留 source 和标题信息。"""

    loader = DocumentLoader()
    splitter = CharacterTextSplitter(chunk_size=120, chunk_overlap=20, use_headings=True)

    documents = loader.load_path(KNOWLEDGE_BASE_DIR / "react.md")
    chunks = splitter.split_documents(documents)

    assert len(chunks) >= 1
    assert chunks[0].source == "react.md"
    assert chunks[0].metadata["heading"] == "# ReAct 简介"


def test_keyword_retriever_returns_relevant_react_chunks() -> None:
    """验证 Retriever 能返回和 ReAct 相关的高分 chunk。"""

    loader = DocumentLoader()
    splitter = CharacterTextSplitter(chunk_size=120, chunk_overlap=20, use_headings=True)
    retriever = KeywordRetriever(
        splitter.split_documents(loader.load_directory(KNOWLEDGE_BASE_DIR))
    )

    results = retriever.search("ReAct 是什么", top_k=3)

    assert results
    assert any(result.source == "react.md" for result in results)
    assert all(hasattr(result, "source") for result in results)
    assert all(hasattr(result, "score") for result in results)
    assert all(hasattr(result, "content") for result in results)


def test_rag_tool_supports_load_and_search() -> None:
    """验证 RAGTool 可以加载知识库并返回检索片段。"""

    tool = RAGTool()

    load_result = tool.run({"action": "load", "path": str(KNOWLEDGE_BASE_DIR)})
    search_result = tool.run({"action": "search", "query": "Agent 框架核心模块", "top_k": 2})

    assert load_result.ok is True
    assert load_result.metadata["document_count"] == 3
    assert search_result.ok is True
    assert search_result.metadata["count"] >= 1
    assert "source: agent_intro.md" in search_result.content
    assert "Message" in search_result.content


def test_rag_tool_returns_clear_message_when_nothing_matches() -> None:
    """验证搜索不到相关内容时会返回明确提示。"""

    tool = RAGTool(knowledge_base_path=KNOWLEDGE_BASE_DIR)

    result = tool.run({"action": "search", "query": "量子隧穿推进器", "top_k": 3})

    assert result.ok is True
    assert result.content == "知识库中没有足够信息。"
    assert result.metadata["count"] == 0


def test_tool_agent_can_answer_with_rag_context() -> None:
    """验证 ToolAgent 可以把检索结果注入上下文，再输出最终回答。"""

    registry = ToolRegistry()
    registry.register_tool(RAGTool(knowledge_base_path=KNOWLEDGE_BASE_DIR))
    llm = FakeLLM(
        [
            'Action: rag\nAction Input: {"action": "search", "query": "Agent 框架通常包含哪些核心模块", "top_k": 2}',
            "Final Answer: 根据知识库，Agent 框架通常包含 Message、LLM、Agent、Tool、Memory 和 RAG。source: agent_intro.md",
        ]
    )
    agent = ToolAgent(
        name="RAG 助手",
        llm=llm,
        tool_registry=registry,
        system_prompt="你是一个会基于本地知识库回答问题的助手。",
    )

    result = agent.run("根据知识库回答：Agent 框架通常包含哪些核心模块？")

    assert result == (
        "根据知识库，Agent 框架通常包含 Message、LLM、Agent、Tool、Memory 和 RAG。"
        "source: agent_intro.md"
    )
    assert "Tool: rag" in llm.calls[1][-1].content
    assert "source: agent_intro.md" in llm.calls[1][-1].content
    assert "Message" in llm.calls[1][-1].content
