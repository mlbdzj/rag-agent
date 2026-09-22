# RAG + Agent 学习计划（8 周 · 逐日版）

> **定位**：AI 应用开发工程师 = Python 后端 + 生产级 RAG + LangGraph Agent 编排 + 评测与部署
> **投入**：每周 10–15 小时（每日约 2–2.5 小时 × 5–6 天）
> **技术栈**：OpenAI/Anthropic SDK → LangChain v1 → LlamaIndex 2.0 → LangGraph v0.2 → LangSmith/Langfuse → FastAPI + Docker
> **原则**：3 个递进项目全部开源；每个阶段记录踩坑笔记（面试素材）；学完即能讲清每个参数和指标的含义。

---

## 总览：8 周里程碑

| 周 | 主题 | 里程碑产出 |
|---|---|---|
| W1 | LLM 应用基础 + LangChain 入门 | 带 3 工具调用的 CLI 助手 |
| W2 | RAG 核心链路 | 项目① MVP：知识库问答（Naive RAG） |
| W3 | RAG 进阶（混合检索+Rerank+LlamaIndex） | 项目① 生产版 + 指标报告 |
| W4 | LangGraph 核心 + ReAct Agent | 项目② MVP：多步任务 Agent |
| W5 | 记忆/HITL/Checkpoint + 高级模式 | 项目② 完整版 |
| W6 | Agentic RAG 融合 | 项目③ 旗舰：Agentic RAG 系统 |
| W7 | 评测 + 可观测性 + 安全 | 项目③ 补 eval 套件 + trace 面板 |
| W8 | 部署 + 简历 + 面试冲刺 | 部署上线 + 简历 + 面试题库 |

---

## W1：LLM 应用基础 + LangChain 入门

**周目标**：脱离"只会在网页用 ChatGPT"的阶段，掌握 API 层的 Messages / Tool calling / 流式输出，用 LangChain 跑通第一个链。

### Day 1（~2h）：环境与 API 基础
- [ ] 安装 Python 3.11+、创建虚拟环境、`pip install openai anthropic python-dotenv`
- [ ] 申请 OpenAI 或国内等价 API Key（可同时用 DeepSeek/Qwen 兼容接口练手）
- [ ] 用原生 SDK 完成：chat 补全、system prompt、多轮 messages、流式输出（streaming）
- [ ] 理解 Token 计费：input/output token、`max_tokens`、为什么长上下文贵
- **验收**：写一个 CLI 脚本，支持多轮对话 + 流式打印 + 打印每次 token 用量

### Day 2（~2h）：Tool Calling（Agent 的地基）
- [ ] 学习 function/tool calling 协议：tools 定义（JSON Schema）→ model 返回 tool_calls → 执行 → 回传 tool result
- [ ] 手写一个"无框架 Agent 循环"：`while 有 tool_calls: 执行并回填`（**关键：先懂原理再用框架**）
- [ ] 实现 3 个工具：`get_weather`（mock）、`calculator`、`read_file`
- **验收**：CLI 助手能自主判断何时调用哪个工具，多步完成复合请求

### Day 3（~2h）：提示词与上下文工程
- [ ] 学习 prompt 模板化：变量注入、few-shot 示例的利弊（何时有害）
- [ ] 上下文工程四要素：预算分配、摘要压缩、结构化注入、缓存（prompt caching 成本模型）
- [ ] 结构化输出：JSON mode / `response_format` / 输出校验与重试
- **验收**：把 Day 2 的 CLI 升级为结构化输出（工具调用结果返回合法 JSON）

### Day 4（~2h）：LangChain v1 入门
- [ ] `pip install langchain langchain-openai`；学习模型抽象（同一代码切 OpenAI/其他模型）
- [ ] `ChatPromptTemplate`、消息类型（System/ Human/ AI/ Tool）
- [ ] 用 LangChain 重写 Day 2 的 Agent：`create_react_agent` 或等价 API + 自定义工具 `@tool`
- **验收**：对比原生 SDK 与 LangChain 版代码量，写 200 字笔记：抽象带来了什么、隐藏了什么（面试题素材）

### Day 5（~2h）：可观测性初体验 + 周复盘
- [ ] 注册 LangSmith（或开源替代 Langfuse），给 W1 程序接入 trace，观察每次调用的 prompt/响应/耗时
- [ ] 周复盘笔记：Messages 协议、Tool calling 流程图、Token 成本估算方法
- [ ] 预习：阅读 LlamaIndex 与 LangChain 定位差异（数据层 vs 编排层）
- **周产出**：`cli-assistant/` 仓库（原生版 + LangChain 版两个入口）

---

## W2：RAG 核心链路（项目① MVP）

**周目标**：手写一条完整 Naive RAG 管线，理解每个环节的参数含义。

### Day 6（~2h）：RAG 原理与语料准备
- [ ] 学习 RAG 为什么存在：知识截止、幻觉、私有数据三问题
- [ ] 选定语料（三选一）：公司产品文档 / 开源项目 docs / 你自己的笔记（≥50 页，含 PDF+Markdown 混合）
- [ ] 文档解析：`pypdf` / `unstructured` 或 LlamaParse（复杂 PDF 先用简单方案）
- **验收**：语料入库目录 `data/raw/`，统计页数与格式分布

### Day 7（~2h）：分块 Chunking
- [ ] 理解分块为什么影响召回：太大切不准、太小丢上下文
- [ ] 实验三种策略：固定长度、递归字符分隔、按标题层级；参数 `chunk_size` / `chunk_overlap`
- [ ] 记录直觉结论：256–512 token 起步、重叠 10–20%、代码/表格需特殊处理
- **验收**：可视化 3 种分块结果对比，写入笔记

### Day 8（~2h）：Embedding 与向量库
- [ ] `pip install chromadb langchain-chroma`；Embedding 选型：OpenAI text-embedding-3-small vs 本地 BGE-M3（了解维度概念，如 3072）
- [ ] 文档 → chunks → embeddings → Chroma 入库；持久化到本地
- [ ] 相似度检索 top-k，观察返回的 metadata 与距离分数
- **验收**：能对语料做 5 个测试问题的检索，肉眼判断相关性

### Day 9（~2h）：检索→生成全链路（项目① MVP）
- [ ] 组装链：`retriever → 相关 chunk 拼接 prompt → LLM 回答`
- [ ] Prompt 要求：仅依据资料回答、附引用来源（chunk 元数据）、答不出就说不知道
- [ ] 用 LangChain Expression Language 或朴素函数实现均可
- **验收**：`python ask.py "你的问题"` 得到带引用的回答 ✅ **项目① MVP 完成**

### Day 10（~2h）：MVP 暴露的问题 + 周复盘
- [ ] 用 10 个问题故意"打脸"MVP：多跳问题、关键词不匹配问题、需要聚合的问题
- [ ] 记录失败模式清单（W7 评测的种子）
- [ ] 周笔记：RAG 管线图 + 每个环节的失败模式
- **周产出**：`project1-rag-qa/` 仓库 MVP + `notes/week2-failure-modes.md`

---

## W3：RAG 进阶（混合检索 + Rerank + LlamaIndex）

**周目标**：把 Naive RAG 升级为生产级 Hybrid RAG，并用 LlamaIndex 重构；输出指标报告。

### Day 11（~2h）：混合检索（Hybrid Search）
- [ ] 理解为什么纯向量失效：专有名词、型号、缩写需要精确关键词匹配
- [ ] 实现 BM25（`rank_bm25` 或 Chroma 内置）+ 向量双路召回 → RRF（Reciprocal Rank Fusion）合并
- [ ] 分块策略微调：混合检索更适合较小分块（256 token / 30 overlap 起步）
- **验收**：在含专业术语的测试集上，混合检索召回优于纯向量（记录数字）

### Day 12（~2h）：Rerank 重排序
- [ ] 理解 cross-encoder vs bi-encoder：rerank 只处理收窄后的候选集（如 top 20 → top 5）
- [ ] 接入 BGE-Reranker-v2 或 Cohere Rerank（或 `bge-reranker-large` 本地推理）
- [ ] 管线升级：`hybrid recall top-20 → rerank → top-5 → LLM`
- **验收**：对比 rerank 前后答案质量，记录 3 个典型改善案例

### Day 13（~2h）：LlamaIndex 2.0 重构
- [ ] `pip install llama-index`；学习 `Settings` 全局配置（模型+Embedding）；**注意 2.0 已移除 ServiceContext**
- [ ] `VectorStoreIndex` / `Document` 加载、`hybrid_search=True`、`similarity_top_k`
- [ ] 用 LlamaIndex 10 行代码重构项目①，与 W2 手写版对比
- **验收**：同一测试集，LlamaIndex 版效果 ≥ 手写版；写笔记：何时用 LlamaIndex、何时手写

### Day 14（~2h）：查询侧优化（Advanced RAG 三板斧）
- [ ] 三选二实验并测效果：**查询重写**（多查询生成）、**HyDE**（假设性文档嵌入）、**子问题分解**（sub-question）
- [ ] 原则：一次只加一个改进并测量，不做技巧堆砌
- [ ] （选学）路由：简单问题走 Naive、复杂问题走分解
- **验收**：`experiments.md` 记录：每项技术在 10 题测试集上的得分变化

### Day 15（~2h）：项目① FastAPI 化 + 周复盘
- [ ] `pip install fastapi uvicorn`；暴露 `POST /ask`、`POST /ingest` 两个端点
- [ ] 补 README：架构图（mermaid）、技术选型理由、指标数字
- [ ] 周笔记：Hybrid RAG 架构图 + 各环节选型对比表（向量库/Reranker）
- **周产出**：**项目① 生产版完成** — `project1-rag-qa/`（FastAPI + 混合检索 + Rerank + 引用）

---

## W4：LangGraph 核心 + ReAct Agent（项目② MVP）

**周目标**：掌握状态机编排思维，实现一个能多步规划的 Agent。

### Day 16（~2h）：LangGraph 四大核心概念
- [ ] `pip install langgraph`；理解 State / Node / Edge（含条件边）/ Checkpoint
- [ ] 为什么弃链式：Agent 是"思考→行动→观察→再思考"的循环，链式无法回头
- [ ] 手写第一个图：`start → llm_node → tool_node → end`，条件边决定是否继续
- **验收**：画出 State 字段流转图（笔记）

### Day 17（~2h）：状态与内存管理
- [ ] 定义 TypedDict/Pydantic State；Reducer（`add_messages`）如何合并状态
- [ ] `MemorySaver` 持久化；`graph.get_state` / `update_state` 调试技巧
- [ ] 用 `graph.stream` / `graph.invoke` 观察每一步状态快照
- **验收**：一个能跨多次 invoke 保持对话状态的聊天图

### Day 18（~2h）：内置 ReAct Agent
- [ ] 使用 LangGraph 预置 Agent（`create_react_agent` 或 `langchain.agents`）+ 自定义工具
- [ ] 对比 W1 手写循环 vs 框架版：框架给了哪些生产特性
- [ ] 工具设计实践：工具描述写清楚（减少幻觉调用）、错误如何返回给模型
- **验收**：Agent 能拆解复合任务（如"查X并计算Y再总结"）多步完成

### Day 19（~2h）：项目② 启动——研究助理 Agent（MVP）
- [ ] 设计图结构：`plan → route(条件) → [web_search / read_doc / calculator] → reflect(条件) → report`
- [ ] 工具至少 4 个：网页搜索（可用 Tavily/serper 或本地 mock）、文件读取、计算器、笔记写入
- [ ] 条件边：检索结果不足 → 回到 plan 改写查询（**自我纠错循环雏形**）
- **验收**：✅ **项目② MVP**：输入研究主题，输出带步骤说明的报告草稿

### Day 20（~2h）：失败模式实验 + 周复盘
- [ ] 故意制造失败：工具抛异常、模型死循环、超长输出 → 观察图如何卡住
- [ ] 引入：节点级 try/except、`recursion_limit`、工具超时
- [ ] 周笔记：LangGraph 心智模型（对比 LangChain 链式）
- **周产出**：`project2-research-agent/` MVP + `notes/week4-failure-modes.md`

---

## W5：记忆 / HITL / 高级模式（项目② 完整版）

**周目标**：补齐生产级 Agent 三件套——持久化、人工审核、记忆系统。

### Day 21（~2h）：Checkpoint 深水区
- [ ] `checkpointer` 配置：MemorySaver → SQLite/Postgres（生产路径）
- [ ] 中断与恢复：`interrupt()`、`Command(resume=...)`；模拟"审批后继续执行"
- [ ] 理解 checkpoint 存了什么：State 快照 + 消息历史 + 图配置（面试高频）
- **验收**：程序中途 kill 后可从断点恢复继续执行

### Day 22（~2h）：Human-in-the-loop 审批
- [ ] 危险工具（如"发送邮件""删文件"）前插入 interrupt 审批节点
- [ ] 设计审批 UI 的最小形态：CLI 输入 y/n + 修改参数后 resume
- [ ] 审计日志：谁在何时批准了什么操作
- **验收**：项目② 中"写入笔记"工具需人工确认才执行

### Day 23（~2h）：记忆系统
- [ ] 短期记忆：线程级 checkpointer 消息历史 + 窗口截断/摘要压缩
- [ ] 长期记忆：关键信息 → Embedding → 向量库；下次对话先检索相关记忆
- [ ] 记忆写入策略：不是全存，而是"值得记住的事实"（让模型自己决定）
- **验收**：跨会话记住用户偏好（如"我是金融从业者"）

### Day 24（~2h）：多 Agent 与子图（够用即可）
- [ ] Supervisor 模式：一个协调者把子任务分发给 worker 子图
- [ ] LangGraph 子图（subgraph）封装：检索 Agent + 写作 Agent 组合
- [ ] 知道何时**不用**多 Agent：单 Agent + 好工具 > 强行拆分（面试判断题）
- **验收**：项目② 升级为 supervisor + 2 worker（检索、写作）

### Day 25（~2h）：流式输出 + 周复盘
- [ ] 中间步骤流式返回（Agent 慢的体验解法：让用户看到正在做什么）
- [ ] `astream_events` 推送到 FastAPI SSE / WebSocket
- [ ] 周笔记：Agent 生产化清单（checkpoint/审批/记忆/流式/超时/幂等）
- **周产出**：**项目② 完整版** — `project2-research-agent/`（HITL + 记忆 + supervisor + 流式）

---

## W6：Agentic RAG 融合（项目③ 旗舰）

**周目标**：把 W3 的检索策略与 W4-5 的 Agent 编排融合——Agent 运行时决定"怎么检索"。

### Day 26（~2h）：架构设计
- [ ] 学习 5 层 RAG 架构：Naive → Hybrid → Graph → Advanced → **Agentic**（逐层叠加，非互斥）
- [ ] 设计项目③：企业知识库 + 多策略检索 + 自我纠错
- [ ] 画架构图：LlamaIndex（数据/检索层）+ LangGraph（编排层）+ 引用与审批
- **验收**：`project3-agentic-rag/docs/architecture.md`（mermaid 图 + 设计决策）

### Day 27（~2h）：检索策略工具化
- [ ] 把 4 种检索注册为 LangGraph 工具：`naive_search` / `hybrid_search` / `keyword_search` / `multi_query_search`
- [ ] 底层用 LlamaIndex QueryEngine 封装（工具函数内调用）
- [ ] 每个工具返回：chunks + 分数 + 来源元数据（供 Agent 判断质量）
- **验收**：Agent 能根据问题类型自主选择检索工具（观察 trace 中的选择）

### Day 28（~2h）：自我纠错循环
- [ ] `retrieve → assess(条件边) → 够用? → answer / 改写查询重试`
- [ ] 重试预算：最多 N 轮 + `recursion_limit` 双保险（防死循环）
- [ ] 兜底策略：检索始终不足 → 显式回答"资料中未找到"，拒绝硬编
- **验收**：故意构造难问题，观察 Agent 至少做 2 次检索策略切换

### Day 29（~2h）：引用、权限与 HITL
- [ ] 回答强制带引用：chunk id → 可回溯到原文段落（citation 链路打通）
- [ ] 元数据权限过滤：按 department/user 字段在检索层过滤（ACL 雏形）
- [ ] 高风险操作（如"更新知识库"）走 HITL 审批
- **验收**：✅ **项目③ 核心功能完成** — 多策略路由 + 自纠错 + 引用 + 权限

### Day 30（~2h）：FastAPI 服务化 + 周复盘
- [ ] 项目③ 封装为服务：`POST /chat`（SSE 流式）、`POST /ingest`、`GET /health`
- [ ] 错误处理：LLM 超时重试、工具失败降级、幂等 token（防止工具重复执行——面试高频）
- [ ] 周笔记：Agentic RAG vs Pipeline RAG 的取舍（延迟 200ms vs 8-12s、何时异步）
- **周产出**：`project3-agentic-rag/` 可运行服务

---

## W7：评测 + 可观测性 + 安全（区分度最高的一周）

**周目标**：把项目③ 从"能跑"变成"能量化、可归因、够安全"——这是 2026 面试最强信号。

### Day 31（~2h）：Golden Dataset 构建
- [ ] 从 W2 的失败清单 + 真实用户问题出发，构建 30–50 条测试集（问题 + 标准答案 + 标准来源）
- [ ] 数据集分层：简单事实题 / 多跳题 / 聚合题 / 无关问题（拒答题）
- [ ] 存放 `evals/dataset.jsonl`，纳入版本管理
- **验收**：测试集覆盖 4 类问题，每类 ≥8 条

### Day 32（~2h）：RAG 评测指标与脚本
- [ ] 检索侧：Recall@k、MRR（能手推计算即可）
- [ ] 生成侧：Faithfulness（忠实度/幻觉）、Answer Relevance、Correctness
- [ ] 用 LLM-as-judge（`ragas` 或手写 judge prompt）跑批量评测，输出分数表
- **验收**：`make eval` 一键跑分；对比 W3 三种配置的分数

### Day 33（~2h）：Agent 评测
- [ ] 指标：任务成功率、平均步数、工具调用准确率、单任务成本（token×单价）、p95 延迟
- [ ] 写 5 条端到端任务用例（含 1 条必失败的无关任务，测拒答）
- [ ] 回归：改动 prompt/分块后重跑，防止退化
- **验收**：`evals/agent_report.md` 含任务成功率与成本估算

### Day 34（~2h）：可观测性
- [ ] 项目③ 全量接入 LangSmith 或 Langfuse：trace 每步的 prompt、检索结果、工具入参出参、耗时
- [ ] 练习"失败归因"：随机抽 3 个失败 case，定位是检索错、prompt 错、模型错还是工具错
- [ ] 关键指标看板：成本、延迟、失败率
- **验收**：能对着 trace 讲清一个失败 case 的根因与修复（面试故事素材）

### Day 35（~2h）：安全与 Guardrails + 周复盘
- [ ] 学 OWASP Top 10 for LLM：重点 LLM06 **Excessive Agency**（权限最小化、kill switch、沙箱）
- [ ] 防提示注入：用户输入与系统指令隔离、工具输出不直接信任、危险工具白名单
- [ ] PII 脱敏意识：日志不打敏感数据；超时/限流/并发限制
- [ ] 周笔记：项目③ 的 eval 结果 + 一次完整 failure 分析报告
- **周产出**：**项目③ 达到"生产级叙事"** — eval 分数 + trace + 安全清单

---

## W8：部署 + 简历 + 面试冲刺

### Day 36（~2h）：容器化
- [ ] 三个项目写 `Dockerfile` + `docker-compose`（app + 向量库若需要）
- [ ] 环境变量管理：API Key 走 `.env`，绝不入库
- **验收**：`docker compose up` 一条命令跑起项目③

### Day 37（~2h）：CI/CD 与部署
- [ ] GitHub Actions：lint + eval 冒烟测试（PR 必跑）
- [ ] 部署任选其一：云服务器 / Railway·Render / 阿里云函数计算；配 `/health` 探活
- [ ] （加分）画一张部署架构图
- **验收**：公网可访问的 demo 链接 ✅

### Day 38（~2h）：简历改造
- [ ] 项目区按 STAR + 量化写法：
  - ❌ "实现了 RAG 系统"
  - ✅ "构建混合检索 RAG（BM25+向量+Rerank），召回率 62%→81%，带引用与 ACL 权限过滤，Langfuse 全链路追踪"
- [ ] 技能区分三档：熟练 / 使用过 / 了解（别虚标）
- [ ] 准备 1 页版 + 完整版各一份
- **验收**：简历初稿 + 三个项目的 GitHub README 全部翻新（架构图/指标/演示 GIF）

### Day 39（~2h）：面试题库（上）——RAG 专场
- [ ] 刷题并写出自己的答案（对照 W2-W3 笔记）：
  - pgvector vs Pinecone vs Qdrant 选型？HNSW vs IVFFlat？
  - 何时用混合检索？纯向量何时失效？
  - 分块、Embedding、检索、Rerank、Prompt——哪个环节优化 ROI 最高？
  - "RAG 已死 vs Fine-tune 永生"怎么看？（答：互补，高频变化数据用 RAG…）
  - 1000 万文档的 RAG 架构怎么设计？
- **验收**：8 道题各 150 字口述稿

### Day 40（~2h）：面试题库（下）——Agent 专场
- [ ] LangChain vs LangGraph vs LlamaIndex 区别？为什么社区转向 LangGraph？
- [ ] Checkpoint 存了什么？interrupt 后如何恢复？
- [ ] 工具执行成功但 LLM 请求超时，如何防重复执行？（幂等键）
- [ ] Agent 中途失败如何续跑？何时用多 Agent？
- [ ] 何时**放弃框架手写** Agent？框架黑盒难调试怎么办？
- [ ] OWASP LLM06 Excessive Agency 的缓解措施？
- [ ] MCP 是什么？（了解 spec、stdio vs Streamable HTTP 即可）
- **验收**：10 道题口述稿 + 3 个项目深挖故事（各准备"最难的 bug""一个被 eval 抓出的问题"）

### Day 41–42（机动，~3h）：查漏补缺
- [ ] 重跑三项目 eval，更新 README 数字
- [ ] 模拟面试：找朋友或对着镜子讲 3 个项目 + 5 道高频题
- [ ] 把 W1–W7 笔记整理成 3 篇可公开发表的技术复盘（投掘金/知乎，链接放简历）

---

## 附录 A：三大项目规格

### 项目① `project1-rag-qa` — 企业知识库问答
- 技术：LangChain/LlamaIndex + Chroma/pgvector + BM25 + Rerank + FastAPI
- 必备：混合检索、重排序、引用来源、`POST /ask` `/ingest`、README 指标
- 量化目标：Recall@5 ≥ 0.8（自建测试集）

### 项目② `project2-research-agent` — 研究助理 Agent
- 技术：LangGraph（State/条件边/Checkpoint/interrupt）+ Supervisor 子图
- 必备：多步规划、自我纠错、HITL 审批、短期+长期记忆、流式输出
- 量化目标：任务成功率 ≥ 80%（5–10 条端到端用例）

### 项目③ `project3-agentic-rag`（旗舰）— Agentic RAG 系统
- 技术：LlamaIndex 检索层 + LangGraph 编排层 + LangSmith/Langfuse + Docker
- 必备：多策略检索路由、查询改写重试、强制引用、元数据 ACL、eval 套件、guardrails
- 量化目标：忠实度 ≥ 0.85、拒答正确、单次问答成本可计算、trace 可归因

## 附录 B：每周自检问题（能流畅口述 = 过关）

- W1：Tool calling 的完整消息流是什么？框架帮你省了什么？
- W2：你的 chunk_size 是多少？为什么？检索失败有哪几类？
- W3：混合检索两路怎么融合？Rerank 为什么能提升且延迟可接受？
- W4：LangGraph 的 State 里有什么？条件边在哪用到？
- W5：checkpoint 保存了什么？如何从 interrupt 恢复？
- W6：Agent 如何决定用哪种检索？检索不足时怎么兜底？
- W7：你的 Faithfulness 怎么算的？举一个 eval 抓出的真实 bug
- W8：10 道高频面试题 + 3 个项目深挖（难点、量化结果、取舍）

## 附录 C：时间不够时的裁剪顺序

1. **保**：W2-W3（RAG）+ W4（LangGraph 核心）+ W7（评测）——求职刚需
2. **简**：W5 多 Agent（懂 supervisor 概念即可）、W1 Day3（上下文工程速览）
3. **勿删**：项目③ 的 eval 与 README 量化数字——比多学一个框架值钱
