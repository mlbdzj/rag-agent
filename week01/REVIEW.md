# Week 1 复盘 · LLM 应用基础

## 五天做了什么

| Day | 主题 | 关键产出 | 核心概念 |
|-----|------|----------|----------|
| 1 | 多轮对话 | `day01_chat.py` | Messages 协议、流式、Token 计费 |
| 2 | 手写 Agent | `day02_tools.py` | Tool Calling 四步、while 循环、分发执行 |
| 3 | 提示词/结构化 | `day03_context.py` | 模板、few-shot、JSON 校验重试、上下文管理 |
| 4 | 框架重构 | `day04_langchain.py` | `@tool`、模型抽象、`create_agent` |
| 5 | 本地可观测 | `day05_observability.py` | 图可视化、回调追踪、token 记账 |

## 一张图看懂这条演进线

```
Day1  消息数组 + 流式                    →  会"说话"
Day2  + while 循环 + 工具分发            →  会"用工具" (手写 Agent)
Day3  + 模板/结构化/上下文管理          →  输出"可控"
Day4  用 create_agent 封装 Day2 循环    → 抽象升级
Day5  拆开看封装: 图 + 回调 + token      → 看得见内部
```

## 手写 vs 框架 对照表（面试核心）

| 环节 | Day2 手写 | Day4 LangChain |
|---|---|---|
| 工具 Schema | 手写 JSON | `@tool` + 注解/docstring |
| Agent 循环 | `while step < max` | `create_agent` 内建 |
| 消息拼装 | 手动 append | 框架管理 |
| 工具分发 | `for tc in tool_calls` | `tools` 节点自动 |
| 终止判断 | `if not msg.tool_calls` | `model -> __end__` 条件边 |
| 底层形态 | 普通函数 | `CompiledStateGraph` (LangGraph) |

**结论**：框架没有改变协议，只是把控制流封装成了一张图。

## 图结构 ↔ 手写循环 逐行对照

```
   LangGraph 图 (Day4/5 由 create_agent 生成)          手写循环 (day02_tools.py)
   ──────────────────────────────────────            ──────────────────────────────

            ┌───────────┐
            │ __start__ │
            └─────┬─────┘
                  │
                  ▼
        ┌───────────────────┐
        │      model        │ ◄──────────────────────┐
        │  (LLM 决策节点)    │                        │
        └─────────┬─────────┘                        │
                  │  条件边 (由 LangGraph 判定)       │
          ┌───────┴────────┐                        │
          │                │                         │
   (无 tool_calls)   (有 tool_calls)                 │
          │                │                         │
          ▼                ▼                         │
   ┌───────────┐   ┌───────────────┐               │
   │  __end__  │   │    tools      │               │
   │ (输出回答)│   │  (执行工具)    │               │
   └───────────┘   └───────┬───────┘               │
                            │  条件边                 │
                            └───────────────────────┘
```

| 图中的元素 | 对应手写代码 `day02_tools.py` | 说明 |
|---|---|---|
| `model` 节点 | `L188` `client.chat.completions.create(...)` | 发起 LLM 请求 |
| `model` 节点读取 | `L194` `choice = response.choices[0]` | 取模型输出 |
| 条件边 `model→__end__` | `L198` `if not msg.tool_calls:` → `L201 return` | 无工具 → 输出并结束 |
| `model→tools` 的消息拼装 | `L204-217` `append(assistant 含 tool_calls)` | 把决策记入历史 |
| `tools` 节点入口 | `L220` `for tc in msg.tool_calls:` | 遍历本轮调用 |
| `tools` 节点执行 | `L227` `dispatch_tool(name, args)` | 真正执行工具 |
| `tools` 回传消息 | `L229-231` `append({role:"tool"...})` | 结果记入历史 |
| 条件边 `tools→model` | `L186` `while step < max_steps:` 回到顶部 | 结果回喂，再决策 |
| `__start__` / `__end__` | 函数入口 / `return` | 哨兵节点 |

**读图口诀**：`model ⇄ tools` 是循环体，两条条件边就是 `if not tool_calls` 和 `while` 回跳；
框架把这三段控制流画成了带条件边的有向图 —— 这就是 LangGraph 的全部本质。


## 必须能口述的 8 个点

1. messages 无状态协议：每轮重发全量历史 → 越长越贵
2. Tool Calling 四步 + `tool_call_id` 一一对应
3. 工具不是塞进 system，是 `tools` 独立参数；决策在模型，执行在客户端
4. 并行（一条消息多 tool_calls）vs 串行（多轮往返）
5. `temperature=0` 用于结构化任务，采样任务用 0.7
6. 结构化输出失败 → 错误回喂重试（错误是给模型看的上下文）
7. `@tool` 封装数据结构，`create_agent` 封装程序结构
8. `create_agent` = LangGraph 图：`model` + `tools` 节点 + 条件边

## 实测踩到的真实坑（可写博客）

1. **模板大括号冲突**：`.format()` 把 JSON `{}` 当变量 → 双写 `{{}}` 转义
2. **Windows 管道编码**：stdin 乱码 + UTF-8 BOM 导致 `/mode` 失效 → `reconfigure` + 去 BOM
3. **DeepSeek prompt caching**：trace 里 `cache_read` 命中 system+tools 前缀，省钱

## Week 2 预告

从"会调用"转向 **RAG 核心链路**：文档解析 → 分块 → Embedding → 向量库 → 检索 → 生成。
项目① 企业知识库问答将从这里开始。
