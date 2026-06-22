# ReAct 简介

ReAct 是一种把推理和行动结合起来的 Agent 工作模式。

常见流程是：

1. Thought：模型先写出当前的思考。
2. Action：模型决定调用哪个工具。
3. Action Input：模型给出工具参数。
4. Observation：系统把工具执行结果返回给模型。
5. Final Answer：模型综合 observation 生成最终回答。

这种模式的价值在于：模型不需要只靠参数记忆硬答，而是可以边思考边调用外部能力。
