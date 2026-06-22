# Agent 框架实践路线

## 0. 目标与边界

当前目标不是直接复刻一个完整成熟框架，而是通过手写一个轻量版 Agent 框架，理解 Agent 框架的核心构成与运行机制。

推荐总路线（新人友好版）：

```text
Message
→ FakeLLM
→ Agent 基类
→ SimpleAgent
→ Config / Real LLM
→ ToolResult
→ ToolAgent
→ ReActAgent happy path
→ ReActAgent 错误恢复与 Trace
→ MemoryTool
→ RAGTool
→ Mini Agent Framework
→ FunctionCallAgent，可选升级
```

本路线遵循几个原则：

1. 先跑通，再抽象。
2. 先做最小版本，再逐步扩展。
3. 每个阶段都要有明确输入、输出和验证方式。
4. 不一开始引入复杂依赖，例如 LangChain、Qdrant、Neo4j、多 Agent 编排等。
5. 把 Memory、RAG、Search、Calculator 都看成 Tool，保持框架主线简单。
6. 单元测试优先使用 FakeLLM，不把真实模型调用作为默认测试依赖。
7. 文本 ReAct 先用于理解原理，后续再升级到原生 function calling / tool calling。
8. 对新人来说，优先跑通 `FakeLLM + SimpleAgent`，再接真实 LLM。
9. 不要求第一天创建完整框架目录，目录随阶段自然增长。
10. 每个高级能力都先做 happy path，再补错误处理和工程化细节。

***

## 1. 最终要做出的框架形态

本项目不要求第一天就创建完整目录。分成两个层次：

1. 第一阶段只创建最小可运行结构。
2. 随着 Tool、Memory、RAG 逐步出现，再扩展到完整框架结构。

### 1.1 第一阶段最小结构

```text
my_agent_framework/
├── my_agents/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── message.py
│   └── agents/
│       ├── __init__.py
│       └── simple_agent.py
├── examples/
├── tests/
│   ├── fakes.py
│   └── test_message.py
├── pyproject.toml
└── README.md
```

这个结构的目标是先跑通：

```text
Message → FakeLLM → SimpleAgent
```

### 1.2 最终完整结构

完整版本建议项目结构：

```text
my_agent_framework/
├── my_agents/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── message.py
│   │   ├── config.py
│   │   ├── llm.py
│   │   ├── agent.py
│   │   └── exceptions.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── simple_agent.py
│   │   ├── tool_agent.py
│   │   └── react_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── result.py
│   │   ├── registry.py
│   │   └── builtin/
│   │       ├── __init__.py
│   │       ├── calculator.py
│   │       ├── memory_tool.py
│   │       └── rag_tool.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── memory_item.py
│   │   └── simple_memory.py
│   └── rag/
│       ├── __init__.py
│       ├── document.py
│       ├── splitter.py
│       └── retriever.py
├── examples/
│   ├── 00_llm_test.py
│   ├── 01_simple_chat.py
│   ├── 02_calculator_tool.py
│   ├── 03_tool_agent.py
│   ├── 04_react_agent.py
│   ├── 05_memory_agent.py
│   └── 06_rag_agent.py
├── tests/
│   ├── fakes.py
│   ├── test_message.py
│   ├── test_llm.py
│   ├── test_agent.py
│   ├── test_tools.py
│   ├── test_calculator.py
│   ├── test_tool_agent.py
│   ├── test_react_agent.py
│   ├── test_memory.py
│   └── test_rag.py
├── knowledge_base/
│   └── agent_intro.md
├── .env.example
├── pyproject.toml
└── README.md
```

***

## 1A. 推荐执行顺序

后续章节仍会按模块详细说明，但新人实际执行时建议按下面顺序推进：

```text
阶段 1：项目初始化，uv，pytest，README 初版
阶段 2：Message
阶段 3：FakeLLM
阶段 4：Agent 基类 + SimpleAgent
阶段 5：真实 LLM + Config
阶段 6：ToolResult + Tool + ToolRegistry
阶段 7：CalculatorTool
阶段 8：ToolAgent，单次工具调用
阶段 9：ReActAgent happy path
阶段 10：ReActAgent 错误恢复 + trace
阶段 11：SimpleMemory
阶段 12：MemoryTool
阶段 13：DocumentLoader + Splitter
阶段 14：Retriever + RAGTool
阶段 15：README、examples、tests 整理
```

这个顺序的核心变化是：

1. `FakeLLM` 早于真实 LLM。
2. `SimpleAgent` 先依赖 `FakeLLM` 跑通。
3. 真实模型调用只作为模型接入层验证。
4. `ReActAgent` 拆成两个阶段实现。
5. `Memory` 和 `RAG` 都先做最小可理解版本。

***

## 2. 阶段一：项目初始化与环境准备

### 2.1 阶段目标

搭建一个可运行、可测试、可持续迭代的 Python 项目骨架。

### 2.2 需要准备

#### 技术准备

- Python 3.10+
- 项目管理工具：`uv`
- 一个兼容 OpenAI SDK 的模型服务
- `.env` 环境变量文件
- 基本依赖：

```bash
uv add openai python-dotenv pydantic pytest
```

推荐初始化方式：

```bash
uv init my_agent_framework
cd my_agent_framework
uv add openai python-dotenv pydantic pytest
```

后续运行命令统一使用 `uv run`，例如：

```bash
uv run python --version
uv run pytest
```

如果你后面需要进入虚拟环境，也可以使用：

```bash
source .venv/bin/activate
```

但本路线默认不要求手动激活虚拟环境，优先使用 `uv run ...`。

#### 配置准备

`.env.example`：

```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
TEMPERATURE=0.7
```

如果使用其他 OpenAI-compatible 服务，只需要替换 `OPENAI_BASE_URL` 和 `LLM_MODEL`。

### 2.3 需要输出

- 项目基础目录。
- `.env.example`。
- `README.md` 初版。
- `examples/` 目录。
- `tests/` 目录。

### 2.4 验证内容

运行：

```bash
uv run python --version
uv run python -c "import openai, pydantic, dotenv; print('ok')"
uv run pytest
```

预期：

- Python 版本满足要求。
- 依赖可以正常导入。
- `pytest` 可以运行，即使暂时没有测试用例。

### 2.5 阶段完成标准

- 项目可以被 IDE 正常识别。
- 依赖安装成功。
- `.env.example` 清晰说明必需配置。
- 后续可以直接开始写核心模块。

***

## 3. 阶段二：实现 Message 消息系统

### 3.1 阶段目标

定义 Agent 框架内部统一的消息格式，用来承载 system、user、assistant、tool 等角色消息。

Message 是 Agent 数据流的基础。无论是普通对话、工具调用、记忆注入，还是 RAG 上下文，最终都会变成消息进入模型。

### 3.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.3.1 Message 类`

理解 OpenAI messages 格式：

```python
{"role": "user", "content": "你好"}
{"role": "assistant", "content": "你好，有什么可以帮你？"}
```

### 3.3 需要实现

文件：`my_agents/core/message.py`

建议包含：

- `MessageRole`
- `Message`
- `to_dict()`
- `from_dict()`，可选
- `__str__()`，方便调试

示例职责：

```python
Message(content="你好", role="user").to_dict()
```

输出：

```python
{"role": "user", "content": "你好"}
```

### 3.4 需要输出

- `my_agents/core/message.py`
- `tests/test_message.py`

测试点：

1. 可以创建 user 消息。
2. 可以创建 assistant 消息。
3. `to_dict()` 输出符合 OpenAI API 格式。
4. 非法 role 会被拒绝，或者至少在类型层面被限制。

### 3.5 验证内容

运行：

```bash
uv run pytest tests/test_message.py
```

手动验证：

```python
from my_agents.core.message import Message

msg = Message(content="你好", role="user")
print(msg.to_dict())
```

预期：

```python
{'role': 'user', 'content': '你好'}
```

### 3.6 阶段完成标准

- Message 能稳定转换成模型 API 需要的格式。
- 后续 Agent 不直接拼 dict，而是统一使用 Message。

---

## 4. 阶段三：FakeLLM 与测试基础设施

执行顺序建议：这是实际学习路线中的阶段三，应该在 `SimpleAgent` 之前完成。

### 4.1 阶段目标

为后续 Agent、ToolAgent、ReActAgent 测试准备一个稳定的假模型，避免单元测试依赖真实 API。

真实 LLM 调用适合作为手动集成验证，但不适合作为默认单元测试，因为它会受到 API Key、网络、费用、模型随机性和服务可用性的影响。

### 4.2 需要实现

文件：`tests/fakes.py`

建议包含：

- `FakeLLM`
- 固定回复队列
- 记录每次收到的 messages

示例：

```python
class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        return self.responses.pop(0)
```

### 4.3 需要输出

- `tests/fakes.py`
- `tests/test_llm.py` 或 `tests/test_agent.py` 中增加 FakeLLM 行为测试

### 4.4 验证内容

后续所有 Agent 单元测试默认使用 FakeLLM。

真实模型调用测试可以单独放在示例脚本或标记为 integration：

```bash
uv run pytest
uv run python examples/00_llm_test.py
```

### 4.5 阶段完成标准

- 不配置真实 API Key 时，核心单元测试也能运行。
- 需要真实模型的验证不会阻塞默认测试。

---

## 5. 阶段四：实现 Agent 基类与 SimpleAgent

### 5.1 阶段目标

做出第一个可以对话的 Agent。

这是整个框架的第一个里程碑。

第一版建议先使用 `FakeLLM` 验证 Agent 主循环，不依赖真实 API Key。

### 5.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.3.3 Agent 抽象基类`
- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.4.1 SimpleAgent`

需要理解：

```text
用户输入
→ 加入历史消息
→ 拼接 system_prompt + history
→ 调用 LLM
→ 保存 assistant 回复
→ 返回回答
```

### 5.3 需要实现

文件一：`my_agents/core/agent.py`

包含：

- `Agent` 抽象基类
- `run()` 抽象方法
- `add_message()`
- `get_history()`
- `clear_history()`

文件二：`my_agents/agents/simple_agent.py`

包含：

- `SimpleAgent.__init__()`
- `SimpleAgent.run(input_text)`
- system prompt 注入
- 对话历史维护

### 5.4 需要输出

- `my_agents/core/agent.py`
- `my_agents/agents/simple_agent.py`
- `examples/01_simple_chat.py`
- `tests/test_agent.py`

### 5.5 验证内容

示例：

```python
from my_agents.agents.simple_agent import SimpleAgent
from tests.fakes import FakeLLM

agent = SimpleAgent(
    name="学习助手",
    llm=FakeLLM(["你好，我是学习助手。", "你刚才问我介绍自己。"]),
    system_prompt="你是一个帮助用户学习 Agent 开发的助手。"
)

print(agent.run("你好，请介绍一下你自己"))
print(agent.run("我刚才问了什么？"))
print(len(agent.get_history()))
```

真实模型验证可以在完成 `Config` 与 `LLM` 调用层之后再做：

```python
from dotenv import load_dotenv
from my_agents.core.llm import LLM
from my_agents.agents.simple_agent import SimpleAgent

load_dotenv()

agent = SimpleAgent(
    name="学习助手",
    llm=LLM(),
    system_prompt="你是一个帮助用户学习 Agent 开发的助手。"
)

print(agent.run("你好，请介绍一下你自己"))
```

需要验证：

1. 第一次对话能返回。
2. 第二次对话能利用历史上下文。
3. `get_history()` 中包含 user 和 assistant 消息。
4. `clear_history()` 后历史为空。

### 5.6 阶段完成标准

- 可以完成连续对话。
- Agent 的状态由 `_history` 管理。
- 这是后续工具调用、记忆、RAG 的基础。

---

## 6. 阶段五：实现 Config 与真实 LLM 调用层

### 6.1 阶段目标

封装模型调用逻辑，让 Agent 不直接依赖 OpenAI SDK，而是依赖统一的 LLM 类。

注意：从新人学习顺序看，本阶段建议放在 `FakeLLM` 和 `SimpleAgent` 之后完成。也就是说，先用假模型理解 Agent 主循环，再接入真实模型。

这一层解决的问题是：

```text
Agent 不关心具体 API Key、base_url、model，只调用 llm.chat(messages)。
```

### 6.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.2 HelloAgentsLLM扩展`
- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.3.2 Config 类`

需要了解：

- `OpenAI(api_key=..., base_url=...)`
- `client.chat.completions.create(...)`
- OpenAI-compatible API 的基本用法

### 6.3 需要实现

文件一：`my_agents/core/config.py`

包含：

- `model`
- `api_key`
- `base_url`
- `temperature`
- `max_tokens`，可选，第一版可以先不实现
- `from_env()`

文件二：`my_agents/core/llm.py`

包含：

- `LLM.__init__()`
- `LLM.chat(messages)`
- `LLM.chat_text(prompt)`，可选，第一版可以先不实现

### 6.4 需要输出

- `my_agents/core/config.py`
- `my_agents/core/llm.py`
- `.env.example` 更新
- `examples/00_llm_test.py`
- `tests/test_llm.py`，可先只测配置加载，不强制真实请求

### 6.5 验证内容

#### 配置验证

```bash
uv run python -c "from my_agents.core.config import Config; print(Config.from_env())"
```

#### 模型调用验证

```python
from dotenv import load_dotenv
from my_agents.core.llm import LLM
from my_agents.core.message import Message

load_dotenv()
llm = LLM()
response = llm.chat([
    Message(role="user", content="请用一句话介绍 Agent 是什么")
])
print(response)
```

预期：

- 能返回自然语言回答。
- 如果 API Key 缺失，要给出清晰错误提示。

### 6.6 阶段完成标准

- LLM 能通过 `.env` 读取配置。
- LLM 能完成一次真实模型调用。
- Agent 层不需要直接使用 OpenAI SDK。

---

## 7. 阶段六：实现 Tool 抽象与 ToolRegistry

### 6.1 阶段目标

让框架具备扩展外部能力的基础。

Tool 系统要解决的问题是：

```text
Agent 不应该把计算、搜索、记忆、RAG 等能力写死在自己内部，而是通过 Tool 统一调用。
```

### 6.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.5 工具系统`
- 特别关注：`Tool`、`ToolParameter`、`ToolRegistry`

### 6.3 需要实现

文件一：`my_agents/tools/base.py`

包含：

- `ToolParameter`
- `Tool` 抽象基类
- `run(parameters)`
- `get_parameters()`
- `get_description()`，可选

文件二：`my_agents/tools/result.py`

包含：

- `ToolResult`
- `ok`
- `content`
- `error`
- `metadata`

建议所有工具都返回统一结果，避免有的工具返回字符串、有的工具返回 dict、有的工具直接抛异常。

示例：

```python
ToolResult(ok=True, content="14")
ToolResult(ok=False, content="", error="Unknown tool: search")
```

文件三：`my_agents/tools/registry.py`

包含：

- `register_tool(tool)`
- `get_tool(name)`
- `execute(name, parameters)`
- `get_tools_description()`

### 6.3.1 Tool 参数 schema 建议

第一版可以保持简单，但每个 Tool 最好能声明自己的参数结构：

```python
name = "calculator"
description = "计算数学表达式"
parameters = {
    "expression": {
        "type": "string",
        "description": "要计算的数学表达式"
    }
}
```

这样后续可以更自然地升级到 OpenAI function calling / tool calling schema。

### 6.4 需要输出

- `my_agents/tools/base.py`
- `my_agents/tools/result.py`
- `my_agents/tools/registry.py`
- `tests/test_tools.py`

### 6.5 验证内容

准备一个假的测试工具：

```python
class EchoTool(Tool):
    name = "echo"
    description = "原样返回输入内容"

    def run(self, parameters):
        return parameters["text"]
```

验证：

```python
registry.register_tool(EchoTool())
result = registry.execute("echo", {"text": "hello"})
```

预期：

```text
result.ok == True
result.content == "hello"
```

还要验证：

1. 未注册工具调用时有清晰错误。
2. 重复注册工具时行为明确。
3. `get_tools_description()` 能输出工具名称和描述。
4. 工具执行异常会被包装为 `ToolResult(ok=False, error=...)`，而不是直接让 Agent 主循环崩溃。

### 6.6 阶段完成标准

- 所有工具都可以通过统一接口执行。
- Agent 未来只依赖 ToolRegistry，而不直接依赖具体工具。
- 所有工具结果都通过 ToolResult 返回。

***

## 8. 阶段七到阶段八：实现 CalculatorTool 与第一版工具调用 Agent

### 7.1 阶段目标

让 Agent 第一次具备“调用外部工具”的能力。

先不要直接上复杂 function calling，可以先实现一个 `ToolAgent`，只支持“单次工具调用”。它用于承接 SimpleAgent 到 ReActAgent 之间的过渡。

注意：这一阶段的文本协议主要用于理解原理，可靠性不如后续的原生 function calling / tool calling。

### 7.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.5.2 自定义工具开发`

需要理解：

```text
模型输出 Action
→ 程序解析 Action
→ ToolRegistry 执行工具
→ 把 Observation 返回给模型
→ 模型生成最终答案
```

### 7.3 需要实现

文件：`my_agents/tools/builtin/calculator.py`

支持：

- 加法
- 减法
- 乘法
- 除法
- 括号

第一版目标是“安全地演示工具接入”，不是实现完整数学引擎。

建议用安全的 AST 解析，不要直接 `eval()`。

AST 安全限制建议：

- 只允许数字、`+`、`-`、`*`、`/`、括号、一元正负号。
- 是否允许 `**` 要明确；第一版可以先不支持。
- 禁止变量名、函数调用、属性访问、下标访问、列表、字典、集合、lambda、import 等任意 Python 表达式。

然后新增 `ToolAgent`：

- 注入 `tool_registry`
- 在 prompt 中加入可用工具说明
- 解析模型输出中的 `Action` 和 `Action Input`
- 执行一次工具调用后，把 Observation 交回模型生成最终答案

`ToolAgent` 与 `ReActAgent` 的区别：

| Agent       | 能力     | 使用场景         |
| ----------- | ------ | ------------ |
| SimpleAgent | 不调用工具  | 普通对话         |
| ToolAgent   | 单次工具调用 | 学习工具调用链路     |
| ReActAgent  | 多轮工具调用 | 学习思考、行动、观察循环 |

### 7.4 需要输出

- `my_agents/tools/builtin/calculator.py`
- `my_agents/agents/tool_agent.py`
- `examples/02_calculator_tool.py`
- `examples/03_tool_agent.py`
- `tests/test_calculator.py`
- `tests/test_tool_agent.py`

### 7.5 验证内容

#### 工具单测

```python
calculator.run({"expression": "2 + 3 * 4"})
```

预期：

```text
14
```

#### Agent 集成测试

```python
agent.run("帮我计算 2 + 3 * 4")
```

预期：

- Agent 能决定调用 calculator。
- 工具返回 14。
- Agent 最终用自然语言回答。

### 7.6 阶段完成标准

- 工具可以单独运行。
- Agent 可以通过 ToolRegistry 调用工具。
- 你能清楚解释工具调用链路。

***

## 9. 阶段九到阶段十：实现 ReActAgent

### 8.1 阶段目标

实现一个标准的 ReAct 执行循环，让 Agent 具备多步推理和多次工具调用能力。

本阶段对新人来说难度最高，建议拆成两个小阶段：

1. 小阶段 A：严格格式 happy path，只处理模型输出完全符合要求的情况。
2. 小阶段 B：错误恢复与 trace，再处理解析失败、未知工具、最大循环次数等问题。

ReAct 核心格式：

```text
Thought: 我需要计算这个表达式
Action: calculator
Action Input: {"expression": "2 + 3 * 4"}
Observation: 14
Final Answer: 结果是 14
```

### 8.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第七章 构建你的Agent框架.md]] 中 `7.4.2 ReActAgent`

需要准备：

- ReAct system prompt
- 工具描述文本
- Action 解析函数
- 最大循环次数，例如 `max_iterations=3`

### 8.3 需要实现

文件：`my_agents/agents/react_agent.py`

#### 小阶段 A：happy path

- `ReActAgent.run()`
- `_build_prompt()`
- `_parse_action()`
- `_execute_action()`
- 遇到 `Final Answer` 时停止
- 使用 `FakeLLM` 固定输出，验证主循环

小阶段 A 暂时只支持严格格式：

```text
Thought:
Action:
Action Input:
Final Answer:
```

如果输出格式不符合要求，可以直接返回清晰错误，不必在第一版做复杂修复。

#### 小阶段 B：错误恢复与 trace

- `max_iterations` 控制
- Action Input JSON 解析失败时，把错误作为 Observation 反馈给模型
- 工具名不存在时，把错误作为 Observation 反馈给模型
- 同时出现 `Action` 和 `Final Answer` 时行为要明确
- `debug` 或 `trace` 机制，用来记录每一步 Thought / Action / Observation

### 8.4 需要输出

- `my_agents/agents/react_agent.py`
- `examples/04_react_agent.py`
- `tests/test_react_agent.py`

### 8.5 验证内容

测试问题：

```text
请计算 15 * 23，然后判断结果是不是偶数。
```

预期链路：

```text
Thought: 需要先计算 15 * 23
Action: calculator
Observation: 345
Thought: 345 不是偶数
Final Answer: 15 * 23 = 345，345 不是偶数。
```

需要验证：

小阶段 A 先验证：

1. Agent 能解析严格格式的 `Action` 和 `Action Input`。
2. Agent 能执行工具并生成 Observation。
3. Agent 能在看到 `Final Answer` 时停止。
4. 单元测试使用 FakeLLM 固定输出，避免真实模型格式漂移导致测试不稳定。

小阶段 B 再验证：

1. Agent 不会无限循环。
2. 工具名不存在时能返回明确错误。
3. 工具参数格式错误时能给模型一次修正机会。
4. 最终回答不暴露过多内部调试信息，除非 debug 模式开启。
5. `get_trace()` 能查看执行轨迹。

### 8.5.1 ReAct 文本解析注意事项

文本 ReAct 协议容易遇到格式问题，例如：

- 模型漏写 `Action Input`。
- `Action Input` 不是合法 JSON。
- 同时输出 `Action` 和 `Final Answer`。
- 工具名拼写错误。
- Markdown 代码块、中文冒号、多余解释干扰解析。

第一版可以先用严格格式提示词 + 简单解析器，但要把解析失败当成可恢复错误：

```text
Observation: Action Input 不是合法 JSON，请重新给出合法工具调用。
```

不要让解析错误直接中断整个 Agent，除非超过最大循环次数。

### 8.5.2 Trace 建议

为了方便学习和调试，建议 ReActAgent 保存执行轨迹：

```python
[
    {
        "thought": "需要先计算 15 * 23",
        "action": "calculator",
        "action_input": {"expression": "15 * 23"},
        "observation": "345"
    }
]
```

默认最终回答不展示 trace，但可以通过 debug 模式或 `get_trace()` 查看。

### 8.6 阶段完成标准

- Agent 能完成“思考 → 行动 → 观察 → 回答”的闭环。
- 这是一个基础可用的 Agent 框架雏形。

***

## 10. 阶段十一到阶段十二：实现简单记忆系统 MemoryTool

### 9.1 阶段目标

让 Agent 能记住用户信息，并在后续对话中检索使用。

注意：这一阶段不要直接实现完整第八章的四层记忆系统。先做轻量版本。

第一版只做显式记忆，不做自动记忆。也就是说：

```text
用户明确说“请记住...” → Agent 才调用 memory.add
用户明确询问“我之前...” → Agent 才调用 memory.search
```

暂时不要实现：

1. 自动抽取用户画像。
2. 自动总结长期记忆。
3. 记忆重要性评分。
4. 记忆衰减。
5. 周期性反思。

需要明确：Memory 不等于 History。

| 概念      | 作用       | 生命周期  | 使用方式              |
| ------- | -------- | ----- | ----------------- |
| History | 当前会话上下文  | 当前会话内 | 通常直接进入 prompt     |
| Memory  | 重要信息长期保存 | 可跨会话  | 先检索，再选择性注入 prompt |

History 记录“刚刚聊了什么”，Memory 记录“值得以后记住什么”。

### 9.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第八章 记忆与检索.md]] 中 `8.2 记忆系统：让智能体拥有记忆`
- 特别关注：`MemoryTool` 的统一 `execute(action, **kwargs)` 思想

### 9.3 需要实现

文件一：`my_agents/memory/memory_item.py`

字段建议：

- `id`
- `content`
- `memory_type`
- `importance`
- `created_at`
- `metadata`

文件二：`my_agents/memory/simple_memory.py`

支持：

- `add(content, memory_type="semantic")`
- `search(query, limit=5)`
- `list_all()`
- `delete(id)`
- `clear()`
- 可选：JSON 文件持久化

第一版检索可以从简单关键词开始，但测试用例要匹配能力边界。不要假设关键词检索能稳定理解“用户叫什么”这种语义问题。

测试时应该使用能被关键词匹配命中的查询，例如：

```text
张三
Agent 开发
```

不要在第一版单测里要求它稳定回答：

```text
用户叫什么？
我在学什么？
```

这些问题依赖 Agent 把自然语言问题改写成合适的检索词，属于 Agent 集成能力，不属于最小版 `SimpleMemory` 的能力。

可选检索策略：

1. 最小版：字符串包含 / 简单关键词重合。
2. 进阶版：jieba 分词或字符 n-gram。
3. 再进阶：TF-IDF。
4. 后续升级：embedding 检索。

文件三：`my_agents/tools/builtin/memory_tool.py`

支持操作：

- `add`
- `search`
- `summary`
- `clear`

### 9.4 需要输出

- `my_agents/memory/memory_item.py`
- `my_agents/memory/simple_memory.py`
- `my_agents/tools/builtin/memory_tool.py`
- `examples/05_memory_agent.py`
- `tests/test_memory.py`

### 9.5 验证内容

#### 记忆工具单测

```python
memory.add("用户叫张三，正在学习 Agent 开发")
memory.search("张三")
memory.search("Agent 开发")
```

预期：

```text
用户叫张三，正在学习 Agent 开发
```

#### Agent 集成测试

```python
agent.run("请记住我叫张三，正在学习 Agent 开发")
agent.run("我现在在学习什么？")
```

预期：

```text
你正在学习 Agent 开发。
```

说明：这个集成测试依赖 Agent 能把用户问题转成合适的 memory search query。单测中不要直接要求简单关键词检索理解复杂语义。

### 9.6 阶段完成标准

- Agent 可以主动写入记忆。
- Agent 可以根据问题检索记忆。
- 记忆逻辑通过 Tool 形式接入，而不是写死在 Agent 内部。

***

## 11. 阶段十三到阶段十四：实现简化版 RAGTool

### 10.1 阶段目标

让 Agent 能基于本地文档回答问题。

第一版 RAG 不需要向量数据库，可以先用关键词检索或简单 TF-IDF。

建议第一版把 `RAGTool` 定义为“检索工具”，不在工具内部直接调用 LLM 生成最终答案。

推荐链路：

```text
用户问题
→ Agent 判断需要查知识库
→ RAGTool.search 返回相关 chunks
→ Agent 把 chunks 作为 Observation / Context
→ LLM 生成带来源的最终答案
```

这样可以保持 Agent 主循环清晰，也更容易理解 RAG 如何增强上下文。

### 10.2 需要准备

阅读：

- \[\[1 - 📥 Raw/Hello-Agents-第八章 记忆与检索.md]] 中 `8.3 RAG系统：知识检索增强`
- \[\[1 - 📥 Raw/Hello-Agents-第八章 记忆与检索.md]] 中 `8.4 构建智能文档问答助手`

准备本地知识库：

```text
knowledge_base/
├── agent_intro.md
├── react.md
└── rag.md
```

### 10.3 需要实现

文件一：`my_agents/rag/document.py`

包含：

- `Document`
- `DocumentLoader`
- 读取 `.md` / `.txt`

文件二：`my_agents/rag/splitter.py`

包含：

- 按字符数切分
- 按标题切分，可选
- chunk metadata

文件三：`my_agents/rag/retriever.py`

第一版支持：

- 关键词匹配
- 简单相似度打分
- 返回 top\_k chunks

文件四：`my_agents/tools/builtin/rag_tool.py`

支持：

- `load`
- `search`
- `ask`，后续可选；第一版建议不实现

第一版 `RAGTool` 的职责边界：

1. 只负责加载文档、切分文档和检索相关片段。
2. 返回的是 chunks，不是最终答案。
3. 不直接调用 LLM。
4. 不写入 Memory，除非用户显式要求。
5. 最终回答由 Agent 把检索结果交给 LLM 后生成。

### 10.4 需要输出

- `my_agents/rag/document.py`
- `my_agents/rag/splitter.py`
- `my_agents/rag/retriever.py`
- `my_agents/tools/builtin/rag_tool.py`
- `knowledge_base/agent_intro.md`
- `examples/06_rag_agent.py`
- `tests/test_rag.py`

### 10.5 验证内容

#### Retriever 单测

```python
retriever.search("ReAct 是什么", top_k=3)
```

预期：

- 返回包含 ReAct 相关内容的 chunk。
- 每个结果包含 source、score、content。

#### Agent 集成测试

```python
agent.run("根据知识库回答：Agent 框架通常包含哪些核心模块？")
```

预期回答应来自本地文档，而不是模型自由发挥。

需要验证：

1. 找不到相关文档时，Agent 应说明“知识库中没有足够信息”。
2. 回答中最好带来源，例如 `source: agent_intro.md`。
3. RAGTool 不应污染长期记忆，除非显式要求写入。
4. RAGTool.search 返回的是检索片段，不是模型自由发挥的答案。

### 10.6 阶段完成标准

- Agent 可以基于本地 Markdown 文档回答问题。
- RAG 作为 Tool 接入。
- 检索结果可以被注入 prompt。

***

## 12. 阶段十五：整理成 Mini Agent Framework

### 11.1 阶段目标

把前面零散实现整理成一个结构清晰、可复用、可演示的小框架。

### 11.2 需要准备

检查：

- 模块导入路径是否统一。
- 示例是否都能运行。
- README 是否能指导别人从零跑通。
- 测试是否覆盖核心链路。

### 11.3 需要输出

#### README.md

应包含：

1. 项目介绍。
2. 安装方式。
3. 环境变量配置。
4. 快速开始。
5. SimpleAgent 示例。
6. ToolAgent 示例。
7. ReActAgent 示例。
8. Tool 示例。
9. Memory 示例。
10. RAG 示例。
11. 当前限制与后续计划。

#### examples

至少包含：

```text
00_llm_test.py
01_simple_chat.py
02_calculator_tool.py
03_tool_agent.py
04_react_agent.py
05_memory_agent.py
06_rag_agent.py
```

#### tests

至少包含：

```text
fakes.py
test_message.py
test_llm.py
test_agent.py
test_tools.py
test_calculator.py
test_tool_agent.py
test_react_agent.py
test_memory.py
test_rag.py
```

### 11.4 验证内容

完整运行：

```bash
uv run pytest
```

逐个运行示例：

```bash
uv run python examples/01_simple_chat.py
uv run python examples/02_calculator_tool.py
uv run python examples/03_tool_agent.py
uv run python examples/04_react_agent.py
uv run python examples/05_memory_agent.py
uv run python examples/06_rag_agent.py
```

### 11.5 阶段完成标准

- 新用户按照 README 可以跑通项目。
- 每个核心模块都有最小示例。
- 每个阶段的核心能力都有测试覆盖。
- 你可以画出完整运行链路。

***

## 13. 推荐每阶段节奏安排

如果每天投入 1-2 小时，建议准备三种节奏。不要把所有能力都压进同一个时间表里。

### 12.1 7 天体验版

目标：理解 Agent 最核心主线，先不做 Memory 和 RAG。

| 天数    | 任务                               | 交付物             |
| ----- | -------------------------------- | --------------- |
| Day 1 | 项目初始化 + Message                  | 项目骨架、Message 测试 |
| Day 2 | FakeLLM                          | 稳定测试替身          |
| Day 3 | Agent 基类 + SimpleAgent           | 基础聊天 Demo       |
| Day 4 | Config + 真实 LLM                  | 真实调用示例          |
| Day 5 | ToolResult + Tool + ToolRegistry | 工具注册与统一结果       |
| Day 6 | CalculatorTool                   | 计算器工具和安全 AST 测试 |
| Day 7 | ToolAgent                        | 单次工具调用 Demo     |

7 天体验版完成后，你应该能解释：

```text
Message → FakeLLM / LLM → SimpleAgent → ToolRegistry → ToolResult
```

### 12.2 14 天完整版

目标：跑通 ReAct、Memory、RAG，形成 Mini Agent Framework v0.1。

| 天数     | 任务                               | 交付物                       |
| ------ | -------------------------------- | ------------------------- |
| Day 1  | 项目初始化 + Message                  | 项目骨架、Message 测试           |
| Day 2  | FakeLLM + Message 完善             | 稳定测试替身                    |
| Day 3  | Agent 基类 + SimpleAgent           | 基础聊天 Demo                 |
| Day 4  | Config + 真实 LLM                  | 真实调用示例                    |
| Day 5  | ToolResult + Tool + ToolRegistry | 工具注册与统一结果                 |
| Day 6  | CalculatorTool                   | 计算器工具和安全 AST 测试           |
| Day 7  | ToolAgent                        | 单次工具调用 Demo               |
| Day 8  | ReActAgent happy path            | 严格格式多步工具调用 Demo           |
| Day 9  | ReActAgent 错误恢复与 trace           | 可调试的执行轨迹                  |
| Day 10 | SimpleMemory                     | 记忆存储与检索                   |
| Day 11 | MemoryTool + Agent 集成            | 记忆 Demo                   |
| Day 12 | 文档加载 + 切分                        | 本地知识库索引                   |
| Day 13 | Retriever + RAGTool              | 文档检索 Demo                 |
| Day 14 | README + 测试整理                    | Mini Agent Framework v0.1 |

### 12.3 21 天稳健版

目标：补齐边界测试、错误提示、README 和示例质量。

| 阶段        | 天数        | 重点                                               |
| --------- | --------- | ------------------------------------------------ |
| 基础阶段      | Day 1-5   | Message、FakeLLM、SimpleAgent、真实 LLM               |
| 工具阶段      | Day 6-9   | ToolResult、ToolRegistry、CalculatorTool、ToolAgent |
| ReAct 阶段  | Day 10-13 | happy path、解析失败、未知工具、trace                       |
| Memory 阶段 | Day 14-15 | SimpleMemory、MemoryTool、显式记忆 Demo                |
| RAG 阶段    | Day 16-18 | DocumentLoader、Splitter、Retriever、RAGTool        |
| 整理阶段      | Day 19-21 | README、examples、pytest、复盘问题                      |

***

## 14. 每个阶段的复盘问题

每完成一个阶段，都回答这几个问题：

1. 这个模块解决什么问题？
2. 它的输入是什么？
3. 它的输出是什么？
4. 它依赖哪些模块？
5. 哪些逻辑不应该放在这个模块里？
6. 如果这个模块坏了，Agent 会表现出什么问题？

示例：

| 模块            | 输入                 | 输出               | 解决的问题       |
| ------------- | ------------------ | ---------------- | ----------- |
| Message       | role + content     | API message dict | 标准化上下文      |
| FakeLLM / LLM | messages           | assistant text   | 稳定测试或调用真实模型 |
| Agent         | user input         | final answer     | 组织执行流程      |
| ToolRegistry  | tool name + params | tool result      | 管理外部能力      |
| ReActAgent    | task + tools       | final answer     | 多步推理与行动     |
| MemoryTool    | add/search action  | memory result    | 保存和检索用户信息   |
| RAGTool       | query              | chunks           | 检索本地文档片段    |

***

## 15. 不建议一开始做的事情

当前阶段先不要做：

1. 多 Agent 协作。
2. 复杂任务规划器。
3. 图数据库 Neo4j。
4. Qdrant / Milvus 等向量数据库。
5. 长期记忆自动反思与总结。
6. 复杂异步工具执行。
7. Web UI。
8. 插件市场。
9. 类 LangChain 的重型抽象。
10. 过度通用的 Provider 适配层。

原因：这些会分散你对 Agent 主循环的理解。

优先理解：

```text
Message → FakeLLM / LLM → Agent Loop → Tool → Observation → Final Answer
```

***

## 16. 推荐的最小成功闭环

### 15.1 体验版最小闭环

如果只做 7 天体验版，应该能支持下面这个过程：

```python
agent.run("你好，请介绍一下你自己")
agent.run("帮我计算 12 * 8")
```

理想结果：

1. 第一问完成基础对话。
2. 第二问调用计算器工具。
3. 你能解释 `Message → Agent → ToolRegistry → ToolResult` 的链路。

### 15.2 完整版最小闭环

如果要形成 Mini Agent Framework v0.1，应该能支持下面这个完整过程：

```python
agent.run("请记住我叫张三，我正在学习 Agent 开发")
agent.run("帮我计算 12 * 8")
agent.run("我现在正在学习什么？")
agent.run("根据知识库解释 ReAct Agent 的工作流程")
```

理想结果：

1. 第一问写入记忆。
2. 第二问调用计算器。
3. 第三问检索记忆。
4. 第四问调用 RAG。

这就是一个基础 Agent 框架的完整雏形。

***

## 17. 最终验收清单

### 功能验收

- [ ] 能完成基础对话。
- [ ] 能维护对话历史。
- [ ] 能注册工具。
- [ ] 工具统一返回 ToolResult。
- [ ] 能调用计算器工具。
- [ ] 能完成单次工具调用 ToolAgent。
- [ ] 能执行 ReAct 循环。
- [ ] 能查看 ReAct 执行 trace。
- [ ] 能写入记忆。
- [ ] 能检索记忆。
- [ ] 能加载本地文档。
- [ ] 能检索文档片段。
- [ ] 能基于文档生成回答。

### 工程验收

- [ ] 目录结构清晰。
- [ ] 模块职责单一。
- [ ] 示例脚本能运行。
- [ ] 核心逻辑有测试。
- [ ] 默认单元测试不依赖真实 LLM，使用 FakeLLM。
- [ ] README 能指导别人运行。
- [ ] `.env.example` 不包含真实密钥。
- [ ] 错误提示清楚。

### 理解验收

你应该能解释清楚：

- Agent 和普通 LLM 调用有什么区别？
- Message 为什么重要？
- ToolRegistry 解决了什么问题？
- ToolResult 为什么重要？
- ToolAgent 和 ReActAgent 有什么区别？
- ReAct 为什么需要 Observation？
- Memory 和 History 有什么区别？
- RAG 和 Memory 有什么区别？
- 为什么 Memory 和 RAG 都可以被看成 Tool？

***

## 18. 后续升级方向

等 Mini Agent Framework 跑通后，再考虑升级：

### 17.1 LLM 层升级

- 支持多个 provider。
- 支持 streaming。
- 支持 retry。
- 支持 token usage 统计。

### 17.2 Tool 层升级

- 支持 OpenAI function calling schema。
- 支持参数自动校验。
- 支持工具调用日志。
- 支持异步工具。
- 从文本 ReAct 协议升级到结构化 tool calling，减少 Action 解析失败。

### 17.3 Memory 层升级

- 从 JSON 升级到 SQLite。
- 从关键词检索升级到 embedding 检索。
- 区分 working / episodic / semantic memory。
- 加入 memory importance 和 decay。

### 17.4 RAG 层升级

- 使用 embedding 模型。
- 接入 Qdrant / Chroma。
- 支持 Markdown 标题层级切分。
- 支持引用来源。
- 支持 query rewrite。
- 支持 HyDE / 多查询检索。

### 17.5 Agent 层升级

- FunctionCallAgent / ToolCallingAgent。
- Plan-and-Solve Agent。
- Reflection Agent。
- 多 Agent 协作。

***

## 19. 一句话总结

你的实践重点不是一次性搭出完整复杂框架，而是按下面这条主线逐步长出来：

```text
先让 Agent 会说话，
再让 Agent 会用工具，
再让 Agent 会多步行动，
再让 Agent 会记住信息，
最后让 Agent 能查资料回答。
```

这条路线跑通后，你就已经理解了 Agent 框架最核心的工程骨架。
