# RAG 简介

RAG 是 Retrieval-Augmented Generation 的缩写，中文通常叫“检索增强生成”。

在学习版框架里，第一版 RAG 可以先不接向量数据库，而是先做三件事：

1. 加载本地文档；
2. 把文档切成 chunks；
3. 根据用户问题检索相关 chunks。

这里的关键边界是：RAGTool 返回的是检索片段，不是最终答案。
最终答案仍然应该由 Agent 把检索结果放进上下文后，让 LLM 来生成。
