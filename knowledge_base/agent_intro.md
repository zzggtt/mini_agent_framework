# Agent 框架简介

一个基础的 Agent 框架通常包含以下核心模块：

1. Message：统一表示 system、user、assistant、tool 等消息。
2. LLM：负责和大模型 API 通信，把 Message 转成模型接口需要的格式。
3. Agent：负责组织上下文、维护 history，并驱动主循环。
4. Tool：把计算器、记忆、检索等外部能力包装成统一协议。
5. Memory：用于保存跨轮对话之外的长期记忆。
6. RAG：从本地知识库检索相关文档片段，再把结果注入上下文。

学习版 Agent 框架的重点不是一次做全，而是按阶段逐步搭建这些模块。
