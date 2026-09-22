# Week 3 · RAG 进阶（混合检索 + Rerank + LlamaIndex）

**前提**：复用 week02 的语料（云雀 CRM）与 BGE Embedding
**目标**：把 Naive RAG 升级为生产级 Hybrid RAG，打掉 Week2 的 FM-1/FM-3

| Day | 主题 | 脚本 | 状态 |
|-----|------|------|------|
| Day 11 | 混合检索 BM25 + 向量 + RRF | `day11_hybrid.py` | ✅ |
| Day 12 | Rerank 重排序（cross-encoder） | `day12_rerank.py` | ✅ |
| Day 13 | LlamaIndex 2.0 重构 | `day13_llamaindex.py` | ⬜ |
| Day 14 | 查询侧优化（多查询/HyDE/子问题） | `day14_query.py` | ⬜ |
| Day 15 | 项目① FastAPI 化 + 复盘 | `app.py` | ⬜ |

> 自检问答见 **[QA.md](./QA.md)** ｜ 实测记录见 **[notes/](./notes/)**

## 运行

```powershell
uv run week03/day11_hybrid.py                 # 三路检索对比
uv run week03/day11_hybrid.py "私有化版的API配额是多少"   # 单查询明细

uv run week03/day12_rerank.py                 # 粗排 vs 精排对比
uv run week03/day12_rerank.py "私有化版的API配额是多少"
```

## 关键设计

- **分块**：size=256 / overlap=30（混合检索更适合较小块，BM25 关键词信号更集中）
- **BM25**：`rank_bm25` + `jieba` 中文分词 + 停用词过滤
- **RRF**：`score = Σ 1/(k + rank)`，k=60，只融合排名不融合分数
- **评测口径**：用 (来源文件, 唯一子串) 定位 gold 块，报 hit@5 与 gold 排名

## Day 11 自检

- [x] 实现三路检索并用 RRF 融合
- [x] 量化：`vector 4/6, bm25 5/6, hybrid 5/6`
- [ ] 口述为什么混合检索能互补（关键词 vs 语义）
- [ ] 解释 RRF 为什么用排名而非分数
- [ ] 分析：为什么本语料下混合没明显胜出？

## Day 11 实测结论（重要）

1. **BM25 在关键词/编号/表格上碾压纯向量**
   - "ISO 27001"：vector MISS，bm25 排 #1
2. **混合 ≈ BM25，未明显胜出**
   - 合成语料里大量块在两路都出现，RRF 给它们双重加分
   - gold 表块（vector#7 / bm25#10）被"两路都出现但不相关"的块挤出 top-5
3. **"私有化版 API 配额"三路全 MISS**
   - 表格行被 256 字符分块切散（FM-4），粗排根本召回不到
   - → 需**更深候选池 + Rerank**（Day12）；长期需表格结构化

## 对 RRF 的准确认识

- RRF 的收益来自"多路共识"，**代价是压低单路独家命中**
- 块级评测 + 小语料会放大这一效应
- 生产修正：加大 fetch 深度、加权 RRF（如 vector 权重更高）、**融合后再 Rerank**

## Day 12 自检

- [x] 实现 cross-encoder 精排（候选来自混合检索 top-20）
- [x] 量化：`hybrid 5/6` vs `hybrid+rerank 4/6`（base 模型）
- [ ] 口述 bi-encoder vs cross-encoder 的区别
- [ ] 解释"粗排保召回、精排保精度"的分工
- [ ] 分析：为什么 base 重排器效果反而变差？生产该怎么选？

## Day 12 实测结论（重要，选型教训）

实测：`hybrid hit@5 = 5/6` → 加 rerank 后 `4/6`（不升反降）。

1. **`bge-reranker-base` 太小，中文表格/碎片块上不可靠**
   - "私有化版 API 配额"：gold 块精排仅第 #8（top 是无关的定价块）
   - "合规认证"：gold 块（含 ISO 27001）精排第 #16（top 是同一文档的其他块）
2. **查询指令前缀对 BGE 重排器也生效，但不足以保证效果**
   - 干净 pair 上：加前缀 `[0.028, 0.002, 0.000]`（顺序正确）
   - 不加前缀：`[0.071, 0.092, 0.000]`（顺序错误）
   - 完整语料上：指令只是必要条件，非充分条件
3. **CPU 延迟高**：20 条候选约 4.3–4.7 秒/查询 → 生产需 GPU 或重排 API
4. **选型建议**（本机不下载，仅记录）：
   - 本地：`BAAI/bge-reranker-v2-m3`、`Alibaba-NLP/gte-multilingual-reranker-base`
   - API：Cohere Rerank、Jina Reranker

**核心教训**：rerank 是独立且关键的一环，**模型选型决定成败**；
粗排/融合做得再好，重排器太弱也会把正确块排下去。别把 rerank 当"加了就变好"的万能开关。

## 附：为什么每次运行较慢

- 每个 `uv run` 进程都要冷启动 torch + sentence-transformers + 加载模型（约 20–40s）
- 首次会下载模型到 `~/.cache/huggingface/hub`
- 已给 embedding 加磁盘缓存（`week02/data/embed_cache/`），避免重复编码

