# Week 1 · 自检问答（Day 1–2）

> 面试口述素材。先自己答，再对照。

## Day 1 · 多轮对话 + 流式 + Token

**Q1：messages 的完整流转？**

```
启动 messages=[system] → append user → 整条发给 API → 流式接收
→ append assistant → 循环回「用户输入」
```

1. system 永远在最前且仅一条，user/assistant 交替追加
2. **无状态协议**：每轮重发**全量历史**——第 10 轮可能发 19 条
3. 多轮本质 = 客户端维护数组，每轮 +1 user、+1 assistant

**Q2：`include_usage=True` 的作用？**

- 流式**默认不返回 usage**；加此参数后**最后一个 chunk** 附带 `usage`（此时 `choices` 为空）
- 处理：`chunk.choices` 取内容、`chunk.usage` 取 token，两者互斥
- 不开只能 `tiktoken` 估算，估算 ≠ 账单

**Q3：为什么对话越长 input 越贵？**

- 每轮重发全量历史 → input ≈ 历史 + system + 新问题，线性增长
- 计费 = `input_tokens × 单价`；缓解：截断、摘要压缩、prompt caching

---

## Day 2 · Tool Calling Agent 循环

**Q1：四步协议？**

```
① 定义 tools(JSON Schema) → ② 模型返回 tool_calls
→ ③ 客户端执行 → ④ 回传 {role:"tool", tool_call_id} → 回到 ②
直到某轮无 tool_calls → content 即最终回答
```

- `arguments` 是 JSON **字符串**，须 `json.loads`
- 决策在模型，**执行永远在客户端**
- 一轮可并行 N 个 tool_calls，每个单独回传

**Q2：为什么 tool 消息必须带对应 `tool_call_id`？**

- 一一应答：发起 N 个必须回 N 条，缺/错 → API 400
- 并行时靠 id 对号入座；类比 HTTP 请求不能没响应

**Q3：`max_steps=8` 防什么？**

- 防死循环：反复调工具不给终答 → 每圈重发全量历史 → 烧钱
- 生产三件套：步数上限 + 超时 + 成本预算；LangGraph 对应 `recursion_limit`

**Q4：工具失败为何返回 JSON error 不抛异常？**

- 抛异常 → 缺 tool 回传 → API 400
- 返回 `{"error"}` 仍走 `role:"tool"` → 模型**看到原因**才能重试/换工具/如实说做不到
- 失败信息是给**模型**看的上下文，不是给解释器的

**Q5：工具是加载进 system prompt 的吗？assistant 会遍历工具链吗？**

| 误区 | 实际 |
|---|---|
| 塞进 system 文本 | `tools` **独立参数**，与 `messages` 平级 |
| 客户端遍历筛选 | **模型生成时一次性决策**，客户端被动执行 |

请求包 = messages + tools → 模型一次推理决定：输出文本（结束）或 tool_calls（执行后回传再决策）。

**Q6：`for tc in msg.tool_calls` 是预规划好的执行链吗？**

- 横向：for 按模型本轮输出原样执行，零筛选
- 纵向：**ReAct 走一步看一步**——每轮只决定下一步，链路多轮往返才浮现

```
轮1: tool_calls [A,B] → 执行回传 → 轮2: 看结果 → [C] → 轮3: 终答
```

**Q7：天气+计算，一次定两个还是分两次？**

- **独立**（`北京天气? 2的20次方?`）→ 通常**一条消息并行** 2 个 tool_calls，日志同 `tool #1` 下两行
- **依赖**（`多少度? 换华氏`）→ **必须分次**：先 get_weather，拿到数值后下一轮才能 calculator

实测日志（串行特征）：
```
[tool #1] get_weather({"city": "shenzhen"}) -> {"temp_c": 30, ...}
[tool #2] calculator({"expression": "30 * 9/5 + 32"}) -> {"result": 86.0}
```
步号不同（#1/#2）= 不同 API 轮次 = 串行；且 `30` 来自上一步结果，依赖链成立。
并行日志特征：两个工具**同为 `tool #1`**（一条消息里并列两个 tool_calls）。

独立倾向并行但不强制；并行 = 一条消息多 tool_calls，串行 = 多轮往返。

**Q8：手写循环 vs LangGraph？**

- 框架无魔法：`while + tool_calls 分发` 就是 Agent 核心
- 框架多给生产件：状态机/条件边、checkpoint、HITL、流式事件、trace
- 学框架时始终问：这层抽象对应手写循环哪一步？

---

## Day 3 · 提示词/上下文工程 + 结构化输出

**Q1：为什么用模板函数而不是 f-string 拼 prompt？**

- 集中管理：所有 prompt 一处可查、可版本化、可 A/B 测试
- 安全注入：`render()` 缺变量直接报错，f-string 会静默产出残缺 prompt
- 角色分层：system 放稳定角色与硬约束，user 模板只放可变数据（问题/文本/代码）
- 为 LangChain `ChatPromptTemplate` 做铺垫——概念同源

**Q2：few-shot 什么时候有益、什么时候有害？**

- 有益：格式要求（JSON schema）、风格模仿、少样本可覆盖的分类任务
- 有害：示例带偏见/过时 → 模型照抄错误模式；示例太长挤占预算；简单任务加示例反而降智
- 原则：先零样本试，失败再加 1–2 个针对性示例，不是越多越好

**Q3：上下文工程四要素？**

1. **预算分配**：system/工具定义/历史/新输入各占多少 token
2. **摘要压缩**：历史过长 → 截断（`trim_history`）或滚动摘要
3. **结构化注入**：检索结果/工具输出用明确分隔符包起来（如 `<<< >>>`），防指令混淆
4. **缓存意识**：稳定前缀（system+工具定义）放最前，利于 prompt caching 命中降价

**Q4：结构化输出的失败处理链路？（本脚本实现）**

```
请求 → 抠 JSON(容忍```包裹) → schema 校验
  ├─ 通过 → 输出
  └─ 失败 → 把错误回喂给模型(assistant原始输出 + "修正后只输出JSON") → 重试 ≤2 次
       └─ 耗尽 → 返回 {"error": "重试耗尽", "last_error": ...}
```

- 关键：**错误信息是给模型看的上下文**（同 Day 2 工具失败返回 JSON 的思路）
- `temperature=0`：结构化任务要可复现、少发挥

**Q5：为什么结构化任务用 `temperature=0`？**

- 降低采样随机性 → 同输入同输出，校验通过率高、便于回归测试
- 自由聊天才用 0.7 之类；抽取/评审/分类默认 0

**Q6：`trim_history` 截断策略有什么问题？生产怎么做？**

- 朴素截断会丢早期关键事实（用户第 1 轮说的偏好可能被裁掉）
- 生产手段：滚动摘要（旧历史压成一段 summary 保留在 system 后）、
  关键消息钉住（pin）、RAG 化历史（历史入向量库按相关性召回）
- LangGraph checkpoint 存全量 + 运行时按需组装，是同一问题的不同解法
