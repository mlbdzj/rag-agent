# rag-agent · RAG + Agent 学习工程

> 一个从零手写到生产级的 **RAG + Agent 应用开发**学习仓库。
> 逐日实现、量化评测、记录踩坑——目标是能讲清每个参数和指标背后的取舍。

- **定位**：AI 应用开发工程师 = Python 后端 + 生产级 RAG + LangGraph Agent 编排 + 评测与部署
- **技术栈**：OpenAI/Anthropic SDK → LangChain v1 → LlamaIndex 2.0 → LangGraph → FastAPI + Docker
- **学习计划**：见 [LEARNING_PLAN.md](./LEARNING_PLAN.md)
- **当前进度**：Week 3 · Day 13（详见下表）

---

## 目录结构

```
rag-agent/
├── week01/                # LLM 应用基础：Messages / Tool Calling / LangChain
│   ├── day01_chat.py          # 多轮对话 + 流式输出 + Token 统计
│   ├── day02_tools.py         # 手写 Tool Calling Agent 循环
│   ├── day03_context.py       # 提示词/上下文工程 + 结构化输出
│   ├── day04_langchain.py     # LangChain 重构
│   ├── day05_observability.py # 可观测性 + gen_ai 回调
│   ├── QA.md / REVIEW.md      # 面试自检问答 + 周复盘
├── week02/                # RAG 核心链路（项目① MVP）
│   ├── make_corpus.py         # 合成语料「云雀 CRM」知识库
│   ├── day06_load.py          # 文档解析（Markdown + PDF）
│   ├── day07_chunk.py         # 三种分块策略对比
│   ├── embeddings.py          # 本地 BGE Embedding（带磁盘缓存）
│   ├── day08_embed_store.py   # Chroma 入库与相似度检索
│   ├── day09_rag.py           # 检索→生成全链路（MVP）
│   ├── day10_failures.py      # 10 用例失败模式测试集
│   ├── data/raw/              # 语料（7 MD + 1 PDF）
│   └── notes/                 # 失败模式与实测记录
├── week03/                # RAG 进阶：混合检索 + Rerank + LlamaIndex
│   ├── day11_hybrid.py        # BM25 + 向量 + RRF 三路检索
│   ├── day12_rerank.py        # cross-encoder 精排
│   ├── day13_llamaindex.py    # LlamaIndex 2.0 重构
│   └── QA.md / notes/
├── src/rag_agent/         # 包入口
├── main.py
├── pyproject.toml         # uv 管理依赖
└── .env.example           # API Key 模板
```

---

## 快速开始

**环境**：Python ≥ 3.12，依赖用 [uv](https://docs.astral.sh/uv/) 管理。

```powershell
# 1. 安装依赖
uv sync

# 2. 配置 API Key（支持 OpenAI 及任何 OpenAI 兼容服务：DeepSeek / Qwen / Moonshot 等）
Copy-Item .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY（可选 OPENAI_BASE_URL / OPENAI_MODEL）

# 3. 从任意一天的脚本开始
uv run week01/day01_chat.py
uv run week02/make_corpus.py          # 生成语料
uv run week02/day09_rag.py "企业版多少钱"
uv run week03/day11_hybrid.py          # 混合检索对比
```

各周详细运行方式与自检清单见对应目录的 `README.md`。

---

## 进度总览

| 周 | 主题 | 关键产出 | 状态 |
|----|------|----------|------|
| W1 | LLM 应用基础 + LangChain | 带工具调用的 CLI 助手（原生版 + 框架版） | ✅ Day 1–5 |
| W2 | RAG 核心链路 | 项目① MVP：知识库问答 + 失败模式清单 | ✅ Day 6–10 |
| W3 | RAG 进阶 | 混合检索 / Rerank / LlamaIndex 重构 | 🔄 Day 11–13 |
| W4 | LangGraph + ReAct Agent | 项目② MVP：多步任务 Agent | ⬜ |
| W5 | 记忆 / HITL / 高级模式 | 项目② 完整版 | ⬜ |
| W6 | Agentic RAG 融合 | 项目③ 旗舰系统 | ⬜ |
| W7 | 评测 + 可观测性 + 安全 | eval 套件 + trace 面板 | ⬜ |
| W8 | 部署 + 简历 + 面试冲刺 | 部署上线 | ⬜ |

---

## 关键实测结论

这些是本仓库最值钱的部分——**用数字说话，而非“实现了 RAG”**。

**Week 2 · 失败模式**
- 10 用例测试集：**9 对 1 错**，失败根因定位到「私有化版表格行漏召」。
- 归纳 5 类失败模式：漏召 / 块粒度 / 语义假阳性 / 表格切散 / 拒答两难（见 `week02/notes/`）。

**Week 3 · 混合检索（Day 11）**
- `vector 4/6, bm25 5/6, hybrid 5/6`（hit@5）。
- BM25 在编号/专有名词上碾压向量（"ISO 27001"：vector MISS，bm25 排 #1）。
- 混合≈BM25 未明显胜出：小语料下「两路都出现但不相关」的块被 RRF 双重加分挤出 top-5。
- 结论：RRF 收益来自多路共识，代价是压低单路独家命中 → 需**更深候选池 + 融合后再 Rerank**。

**Week 3 · Rerank（Day 12，选型教训）**
- `hybrid 5/6` → 加 rerank 后反而 `4/6`：`bge-reranker-base` 太小，中文表格/碎片块不可靠。
- 干净 pair 上指令前缀有效，完整语料上只是必要条件。
- CPU 延迟约 4.3–4.7s/查询（20 候选）→ 生产需 GPU 或重排 API。
- **核心教训**：rerank 是独立且关键的一环，模型选型决定成败，不是“加了就变好”。

**Week 3 · LlamaIndex 2.0（Day 13）**
- 建索引从 ~100 行降到 ~15 行，但**同一失败用例仍然失败**——检索质量取决于数据/分块/策略，而非框架。
- 2.0 已移除 `ServiceContext`，改用全局 `Settings`。
- 因依赖冲突（`llama-index-llms-openai-like` 锁 `openai<1.108`），只用 LlamaIndex 做索引/检索，生成继续用自研 DeepSeek 客户端。

---

## 设计要点

- **先原理后框架**：W1 手写 Tool Calling 循环，W3 手写混合检索，再对比框架版。
- **本地 Embedding**：`BAAI/bge-small-zh`（走 hf-mirror 下载），带磁盘缓存避免重复编码。
- **可量化评测**：统一用 (来源文件, 唯一子串) 定位 gold 块，报 hit@5 与 gold 排名。
- **每个决策留痕**：参数取值、失败归因、选型对比全部写入各周 `QA.md` / `REVIEW.md` / `notes/`。

---

## 文档索引

- [LEARNING_PLAN.md](./LEARNING_PLAN.md) — 8 周逐日学习计划与项目规格
- [week01/README.md](./week01/README.md) · [QA](./week01/QA.md) · [REVIEW](./week01/REVIEW.md)
- [week02/README.md](./week02/README.md) · [QA](./week02/QA.md) · [失败模式](./week02/notes/week2_failure_modes.md)
- [week03/README.md](./week03/README.md) · [QA](./week03/QA.md)

---

## License

学习用途，自由取用。
