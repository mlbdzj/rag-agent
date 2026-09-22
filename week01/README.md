# Week 1 · LLM 应用基础

| Day | 主题 | 脚本 | 状态 |
|-----|------|------|------|
| Day 1 | 多轮对话 + 流式输出 + Token 统计 | `day01_chat.py` | ✅ |
| Day 2 | Tool Calling 手写 Agent 循环 | `day02_tools.py` | ✅ |
| Day 3 | 提示词/上下文工程 + 结构化输出 | `day03_context.py` | ✅ |
| Day 4 | LangChain 重构 | `day04_langchain.py` | ⬜ |
| Day 5 | LangSmith 接入 + 周复盘 | — | ⬜ |

> 自检问答（面试口述素材）见 **[QA.md](./QA.md)**

## 运行

```powershell
# 配置 Key（仓库根目录，已有 .env 则跳过）
Copy-Item ..\.env.example ..\.env   # 然后填入 DeepSeek Key

uv run week01/day01_chat.py
uv run week01/day02_tools.py
uv run week01/day03_context.py
```

## Day 3 自检

- [ ] 说出模板 vs f-string 的三个理由
- [ ] 判断：哪些场景该加 few-shot、哪些不该
- [ ] 口述上下文工程四要素
- [ ] extract 模式贴一段含人名/公司/日期的文本，观察校验-重试链路
- [ ] 故意问无结构的信息，观察 `重试耗尽` 兜底
- [ ] 解释为何结构化任务 `temperature=0`

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
