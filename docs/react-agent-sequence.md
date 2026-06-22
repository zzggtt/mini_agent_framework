# ReActAgent.run() 时序图与 messages 演化图

这份文档的目标不是复述代码，而是把 `ReActAgent.run()` 里最关键的两件事画清楚：

- 一轮任务里，`LLM / Agent / ToolRegistry / Tool` 是怎么协作的
- `messages` 列表在每一步是如何逐渐变长的

对应代码：

- [react\_agent.py](file:///Users/bytedance/code/my_agent_framework/my_agents/agents/react_agent.py)

***

## 1. 总体时序图

下面这张图描述的是一次典型的多轮 ReAct 流程：

```text
用户
 │
 │ 1. 输入问题
 ▼
ReActAgent.run()
 │
 │ 2. 写入 user message 到 history
 │ 3. 构造初始 messages
 │
 │ 4. llm.chat(messages)
 ▼
LLM
 │
 │ 5. 返回 Thought / Action / Action Input
 ▼
ReActAgent
 │
 │ 6. 解析 Action
 │ 7. 调用 ToolRegistry.execute()
 ▼
ToolRegistry
 │
 │ 8. 查找工具并执行
 ▼
CalculatorTool
 │
 │ 9. 返回 ToolResult
 ▼
ToolRegistry
 │
 │ 10. 返回统一 ToolResult
 ▼
ReActAgent
 │
 │ 11. 格式化为 Observation
 │ 12. 把 assistant + tool message 追加到 messages
 │
 │ 13. llm.chat(updated_messages)
 ▼
LLM
 │
 │ 14. 返回新一轮 Thought / Action
 │    或 Final Answer
 ▼
ReActAgent
 │
 │ 15. 如果是 Final Answer -> 结束
 │ 16. 如果还是 Action -> 重复下一轮
 ▼
用户
```

***

## 2. 典型案例

这里用项目里的示例问题：

```text
请计算 15 * 23，然后判断结果是不是偶数。
```

配合示例输出：

```text
Thought: 需要先计算 15 * 23
Action: calculator
Action Input: {"expression": "15 * 23"}
```

然后工具返回：

```text
Observation: 345
```

最后模型给出：

```text
Thought: 345 不是偶数
Final Answer: 15 * 23 = 345，345 不是偶数。
```

***

## 3. run() 主流程图

`ReActAgent.run()` 的逻辑可以压缩成下面这张流程图：

```text
开始
 │
 ├─ 清空 trace
 ├─ 把 user message 写入 history
 ├─ build_prompt() 构造初始 messages
 │
 └─ for i in range(max_iterations):
      │
      ├─ llm.chat(messages)
      ├─ append assistant message
      ├─ parse_action()
      │
      ├─ 有 Final Answer ?
      │    ├─ 是 -> 记录 trace -> 写入 history -> 返回答案
      │    └─ 否
      │
      ├─ execute_action()
      │    ├─ 解析失败 -> 生成错误 Observation
      │    ├─ 工具不存在 -> 生成错误 Observation
      │    ├─ 工具执行成功 -> 生成正常 Observation
      │    └─ 记录 trace
      │
      ├─ append tool message
      └─ 进入下一轮
 
循环结束
 │
 ├─ 返回“达到最大迭代次数”的兜底答案
 └─ 写入 history
```

***

## 4. messages 演化图

这一部分最关键。

`ReActAgent` 真正的核心不是“会循环”，而是：

```text
messages 会在单次 run 中不断增长
```

也就是说，模型每一轮看到的上下文，都是“上一轮基础上继续追加”的结果。

***

## 5. 第 0 步：初始状态

刚进入 `run()` 时：

- `history` 里先加入当前用户输入
- `_build_prompt()` 会生成一份初始 `messages`

此时的 `messages` 大致是：

```text
[
  system: 你是一个帮助用户逐步推理的助手。
  system: 你是一个会使用 ReAct 模式解决问题的助手...
  user: 请计算 15 * 23，然后判断结果是不是偶数。
]
```

这里有两个重点：

- 第一条 `system` 是你的业务角色设定
- 第二条 `system` 是 ReAct 协议说明

***

## 6. 第 1 轮：模型先输出 Action

第一次调用：

```text
llm.chat(messages)
```

模型返回：

```text
Thought: 需要先计算 15 * 23
Action: calculator
Action Input: {"expression": "15 * 23"}
```

这时 `run()` 会先把它追加成一条 `assistant` 消息：

```text
[
  system: 你是一个帮助用户逐步推理的助手。
  system: 你是一个会使用 ReAct 模式解决问题的助手...
  user: 请计算 15 * 23，然后判断结果是不是偶数。
  assistant: Thought: 需要先计算 15 * 23
             Action: calculator
             Action Input: {"expression": "15 * 23"}
]
```

这一步非常重要，因为它意味着：

```text
模型自己的中间推理，也会成为后续上下文的一部分
```

***

## 7. 第 1 轮：执行工具并追加 Observation

接下来程序会：

- 解析 `Action: calculator`
- 解析 `Action Input`
- 调用 `ToolRegistry.execute("calculator", {"expression": "15 * 23"})`
- 得到 `ToolResult(ok=True, content="345")`
- 格式化成：

```text
Observation: 345
```

然后把它作为一条 `tool` 消息追加到 `messages`：

```text
[
  system: 你是一个帮助用户逐步推理的助手。
  system: 你是一个会使用 ReAct 模式解决问题的助手...
  user: 请计算 15 * 23，然后判断结果是不是偶数。
  assistant: Thought: 需要先计算 15 * 23
             Action: calculator
             Action Input: {"expression": "15 * 23"}
  tool: Observation: 345
]
```

这里就是 ReAct 的灵魂：

```text
assistant 提出动作
tool 返回观察
assistant 再基于观察继续思考
```

***

## 8. 第 2 轮：模型基于 Observation 继续推理

第二次调用：

```text
llm.chat(updated_messages)
```

此时模型已经能看到：

- 用户原始问题
- 自己上一轮的 `Thought / Action`
- 工具返回的 `Observation: 345`

所以它可以继续输出：

```text
Thought: 345 不是偶数
Final Answer: 15 * 23 = 345，345 不是偶数。
```

程序会先把它追加成 `assistant` 消息：

```text
[
  system: 你是一个帮助用户逐步推理的助手。
  system: 你是一个会使用 ReAct 模式解决问题的助手...
  user: 请计算 15 * 23，然后判断结果是不是偶数。
  assistant: Thought: 需要先计算 15 * 23
             Action: calculator
             Action Input: {"expression": "15 * 23"}
  tool: Observation: 345
  assistant: Thought: 345 不是偶数
             Final Answer: 15 * 23 = 345，345 不是偶数。
]
```

然后检测到 `Final Answer`，结束循环。

***

## 9. history 与 messages 的区别

这一步很容易混。

在一次 `run()` 内部：

- `messages` 是“本轮任务临时上下文”
- `history` 是“对用户暴露的会话状态”

当前实现里：

- `messages` 会保存中间过程
  - assistant 的 Thought / Action
  - tool 的 Observation
- `history` 最终只保留
  - user 输入
  - final assistant answer

也就是说：

```text
messages 更详细
history 更干净
trace 最完整
```

***

## 10. trace 演化图

除了 `messages`，`ReActAgent` 还会维护 `_trace`。

对于上面的例子，最终 trace 类似：

```python
[
    {
        "thought": "需要先计算 15 * 23",
        "action": "calculator",
        "action_input": {"expression": "15 * 23"},
        "observation": "Observation: 345",
        "final_answer": "",
    },
    {
        "thought": "345 不是偶数",
        "action": "",
        "action_input": {},
        "observation": "",
        "final_answer": "15 * 23 = 345，345 不是偶数。",
    },
]
```

可以把它理解成：

```text
messages 是“模型看到的上下文”
trace 是“程序记录的结构化过程”
```

***

## 11. 错误恢复时 messages 怎么演化

如果模型输出：

```text
Thought: 我需要计算
Action: calculator
Action Input: not-json
```

程序不会直接崩掉，而是生成：

```text
Observation: Action Input 不是合法 JSON，请重新给出合法工具调用。
```

这时 `messages` 会变成：

```text
[
  system: ...
  system: ...
  user: 帮我计算 2 + 3 * 4
  assistant: Thought: 我需要计算
             Action: calculator
             Action Input: not-json
  tool: Observation: Action Input 不是合法 JSON，请重新给出合法工具调用。
]
```

下一轮模型看到这条 Observation 后，就有机会修正为：

```text
Thought: 重新给出合法 JSON
Action: calculator
Action Input: {"expression": "2 + 3 * 4"}
```

所以错误恢复的关键就是：

```text
把“解析失败”也当成一种 Observation
```

***

## 12. 为什么多轮 ReAct 能成立

多轮 ReAct 成立，靠的不是某个神奇函数，而是下面这 3 件事一起成立：

- 模型每一步输出结构化文本
- 程序把结构化文本转换成真实动作或错误 Observation
- `messages` 把这些中间结果完整串起来，交给下一轮模型继续推理

压缩成一句话就是：

```text
上一轮的 assistant 输出 + tool 反馈
会成为下一轮 assistant 推理的输入
```

这就是 ReAct 和单轮 `ToolAgent` 的本质差别。

***

## 13. 最简时序图

如果你想脑中记一个最短版本，可以记这张图：

```text
user
  -> ReActAgent
  -> LLM: Thought + Action
  -> ToolRegistry
  -> Tool
  -> ToolRegistry: ToolResult
  -> ReActAgent: Observation
  -> LLM: Thought + Final Answer
  -> ReActAgent
  -> user
```

***

## 14. 最简 messages 演化图

如果只记一版最核心的 `messages` 演化，记这个：

```text
初始：
[system, system, user]

第 1 轮模型后：
[system, system, user, assistant(Action)]

第 1 轮工具后：
[system, system, user, assistant(Action), tool(Observation)]

第 2 轮模型后：
[system, system, user, assistant(Action), tool(Observation), assistant(Final Answer)]
```

这就是当前 `ReActAgent.run()` 最核心的上下文演化。

***

## 15. 一句话总结

`ReActAgent.run()` 的本质就是：

```text
不断把“模型的思考结果”转成“可执行动作”，
再把“动作的结果”转成“下一轮模型继续思考的输入”。
```

而 `messages`，就是承载这条循环链路的那张“推理工作台”。
