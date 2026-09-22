# Week 1 · LLM 应用基础

| Day | 主题 | 脚本 | 状态 |
|-----|------|------|------|
| Day 1 | 多轮对话 + 流式输出 + Token 统计 | `day01_chat.py` | ✅ |
| Day 2 | Tool Calling 手写 Agent 循环 | `day02_tools.py` | ✅ |
| Day 3 | 提示词/上下文工程 + 结构化输出 | `day03_context.py` | ✅ |
| Day 4 | LangChain 重构 | `day04_langchain.py` | ✅ |
| Day 5 | LangSmith 接入 + 周复盘 | — | ⬜ |

> 自检问答（面试口述素材）见 **[QA.md](./QA.md)**

## 运行

```powershell
# 配置 Key（仓库根目录，已有 .env 则跳过）
Copy-Item ..\.env.example ..\.env   # 然后填入 DeepSeek Key

uv run week01/day01_chat.py
uv run week01/day02_tools.py
uv run week01/day03_context.py
uv run week01/day04_langchain.py
```

## Day 4 自检

- [x] 口述 @tool 如何把函数变成工具 Schema
- [x] 说明模型抽象的价值（换服务商只改 base_url）
- [x] 指出 create_agent 的每个参数对应手写循环的哪一步
- [x] 验证 `type(agent).__name__ == CompiledStateGraph`（底层是 LangGraph）
- [x] 实测并行/串行/文件读取三种场景
- [x] 口述：框架省了什么、隐藏了什么

## Day 3 自检

- [x] 说出模板 vs f-string 的三个理由（见 QA.md Q1）
- [x] 判断：哪些场景该加 few-shot、哪些不该（见 QA.md Q2）
- [x] 口述上下文工程四要素（见 QA.md Q3）
- [x] extract 模式贴一段含人名/公司/日期的文本，观察校验-重试链路（实测：张志东/腾讯/6602亿全抽出）
- [x] 观察重试兜底：无结构信息→合法空数组直通；`test_day03_selfcheck.py` mock 验证重试耗尽
- [x] 解释为何结构化任务 `temperature=0`（`chat_with_schema` 第143行，chat 模式 0.7 对比）

## Day 1 自检

- [x] 画出 messages 完整流转图
- [x] 解释 `include_usage=True`
- [x] 口述：为何上下文越长 input 越贵
- [x] `/system` 换指令观察行为变化

## Day 2 自检

- [x] 口述 Tool Calling 四步协议
- [x] 解释 `tool_call_id` 一一对应
- [x] 说明 `max_steps=8` 防什么
- [x] 工具失败为何返回 JSON 而非抛异常
- [ ] 实测：并行（天气+计算）vs 串行（温度→华氏）
