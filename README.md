# My Agent Framework

一个面向学习的 Mini Agent Framework，用来从零手写并理解 Agent 框架的核心链路。

这个项目不是一套大而全的生产框架，而是一条可运行、可测试、可逐步拆解的学习路线：  
`Message -> LLM -> Agent -> Tool -> ReAct -> Memory -> RAG`

## 这个项目适合谁

适合下面这类需求：

- 想从零理解 Agent 框架，而不是直接套现成框架
- 想把 `Message / Tool / ReAct / Memory / RAG` 串成一条清楚的主链
- 想要一套能运行、能测试、能逐步讲解的学习型项目
- 想在后续把学习版逐步演进到更真实的工具调用框架

## 你能学到什么

当前项目已经覆盖这些核心模块：

- `Message`：统一消息对象与角色定义
- `LLM`：最小真实模型封装
- `SimpleAgent`：最小对话 Agent
- `Tool / ToolRegistry / ToolResult`：工具抽象、注册与执行
- `ToolAgent`：单次工具调用链路
- `ReActAgent`：多步 `Thought -> Action -> Observation -> Final Answer`
- `SimpleMemory / MemoryTool`：轻量显式记忆
- `Document / Splitter / Retriever / RAGTool`：简化版本地知识库检索

项目同时提供：

- `examples/`：最小可运行示例
- `tests/`：核心链路测试
- `docs/`：时序图、walkthrough 和设计说明

## 一分钟上手

本项目使用 `uv` 管理 Python 环境。

```bash
uv sync
uv run pytest
uv run python examples/01_simple_chat.py
```

如果你只想快速浏览完整学习链路，建议按下面顺序运行：

```bash
uv run python examples/01_simple_chat.py
uv run python examples/03_tool_agent.py
uv run python examples/04_react_agent.py
uv run python examples/05_memory_agent.py
uv run python examples/06_rag_agent.py
```

## 学习路径

建议按这条顺序阅读和运行：

1. `Message`：理解 system / user / assistant / tool 这些消息对象
2. `LLM`：理解消息如何转换成模型接口输入
3. `SimpleAgent`：理解 history 如何积累
4. `Tool`：理解外部能力如何被统一包装
5. `ToolAgent`：理解单次工具调用
6. `ReActAgent`：理解多步推理循环
7. `Memory`：理解显式长期记忆
8. `RAG`：理解“检索”和“生成”的边界

## 环境变量配置

学习版大部分示例和测试都使用 `FakeLLM`，默认**不依赖真实模型**。

如果你想体验真实模型调用，请准备 `.env` 文件：

```bash
cp .env.example .env
```

然后在 `.env` 中配置：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
OPENAI_MODEL=deepseek-v3-2-251201
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=
```

当前真实模型入口主要用于：

- `examples/00_llm_test.py`
- `my_agents/core/llm.py`

## 快速开始

先跑完整测试，确认环境正常：

```bash
uv run pytest
```

再逐个运行学习版示例：

```bash
uv run python examples/01_simple_chat.py
uv run python examples/02_calculator_tool.py
uv run python examples/03_tool_agent.py
uv run python examples/04_react_agent.py
uv run python examples/05_memory_agent.py
uv run python examples/06_rag_agent.py
```

如果你想单独验证真实模型封装：

```bash
uv run python examples/00_llm_test.py
```

## 项目结构

```text
my_agents/
  core/
    message.py
    config.py
    llm.py
    agent.py
  agents/
    simple_agent.py
    tool_agent.py
    react_agent.py
  tools/
    base.py
    result.py
    registry.py
    builtin/
      calculator.py
      memory_tool.py
      rag_tool.py
  memory/
    memory_item.py
    simple_memory.py
  rag/
    document.py
    splitter.py
    retriever.py

examples/
tests/
docs/
knowledge_base/
```

## SimpleAgent 示例

文件：[examples/01_simple_chat.py](file:///Users/bytedance/code/my_agent_framework/examples/01_simple_chat.py)

作用：

- 演示 `SimpleAgent` 如何维护历史消息
- 演示 `FakeLLM` 如何作为稳定替身参与测试与教学

运行：

```bash
uv run python examples/01_simple_chat.py
```

## ToolAgent 示例

文件：[examples/03_tool_agent.py](file:///Users/bytedance/code/my_agent_framework/examples/03_tool_agent.py)

作用：

- 演示单次工具调用链路
- 演示 `Action -> ToolResult -> Observation -> Final Answer`

运行：

```bash
uv run python examples/03_tool_agent.py
```

## ReActAgent 示例

文件：[examples/04_react_agent.py](file:///Users/bytedance/code/my_agent_framework/examples/04_react_agent.py)

作用：

- 演示多步推理
- 演示 `Thought -> Action -> Observation -> Final Answer`

运行：

```bash
uv run python examples/04_react_agent.py
```

## Tool 示例

文件：[examples/02_calculator_tool.py](file:///Users/bytedance/code/my_agent_framework/examples/02_calculator_tool.py)

作用：

- 独立验证 `CalculatorTool`
- 观察工具输入、输出和错误处理

运行：

```bash
uv run python examples/02_calculator_tool.py
```

## Memory 示例

文件：[examples/05_memory_agent.py](file:///Users/bytedance/code/my_agent_framework/examples/05_memory_agent.py)

作用：

- 演示显式记忆写入和检索
- 演示 Agent 如何通过 `MemoryTool` 跨轮获取记忆内容

运行：

```bash
uv run python examples/05_memory_agent.py
```

## RAG 示例

文件：[examples/06_rag_agent.py](file:///Users/bytedance/code/my_agent_framework/examples/06_rag_agent.py)

作用：

- 演示本地知识库加载、切分、检索和回答流程
- 用更详细的打印展示 `ToolAgent` 如何消费 `RAGTool` 的结果

运行：

```bash
uv run python examples/06_rag_agent.py
```

## 测试说明

当前测试集覆盖以下核心链路：

- `test_message.py`：消息结构
- `test_llm.py`：配置与真实 LLM 封装
- `test_agent.py`：`SimpleAgent`
- `test_tools.py`：工具基础协议
- `test_calculator.py`：计算器工具
- `test_tool_agent.py`：单次工具调用
- `test_react_agent.py`：多步 ReAct
- `test_memory.py`：显式记忆
- `test_rag.py`：简化版 RAG

完整运行：

```bash
uv run pytest
```

## 文档导航

项目内还有几份配套讲解文档：

- [stage1-4-walkthrough.md](file:///Users/bytedance/code/my_agent_framework/docs/stage1-4-walkthrough.md)
- [config-llm-agent-sequence.md](file:///Users/bytedance/code/my_agent_framework/docs/config-llm-agent-sequence.md)
- [react-agent-sequence.md](file:///Users/bytedance/code/my_agent_framework/docs/react-agent-sequence.md)
- [tool-protocol-comparison-sequence.md](file:///Users/bytedance/code/my_agent_framework/docs/tool-protocol-comparison-sequence.md)

## 当前限制

这个项目是学习版框架，目前有明确边界：

- `ToolAgent` 和 `ReActAgent` 仍然使用文本协议，不是原生 OpenAI function calling
- 默认示例优先使用 `FakeLLM`，目标是稳定演示，不是生产级接入
- `Memory` 和 `RAG` 都是轻量实现，重点在结构清晰而不是召回质量
- `LLM.chat()` 当前只返回纯文本，不返回结构化 tool-calling 结果

## 后续计划

后续升级方向包括：

- Tool 层升级为结构化 tool-calling schema
- 参数自动校验
- 更规范的工具调用日志
- 异步工具支持
- 把学习版实现与真实协议版实现拆成更清晰的两条路线
