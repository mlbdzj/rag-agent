# Week 3 · RAG 进阶（混合检索 + Rerank + LlamaIndex）

**前提**：复用 week02 的语料（云雀 CRM）与 BGE Embedding
**目标**：把 Naive RAG 升级为生产级 Hybrid RAG，打掉 Week2 的 FM-1/FM-3

| Day | 主题 | 脚本 | 状态 |
|-----|------|------|------|
| Day 11 | 混合检索 BM25 + 向量 + RRF | `day11_hybrid.py` | ✅ |
| Day 12 | Rerank 重排序（cross-encoder） | `day12_rerank.py` | ⬜ |
| Day 13 | LlamaIndex 2.0 重构 | `day13_llamaindex.py` | ⬜ |
| Day 14 | 查询侧优化（多查询/HyDE/子问题） | `day14_query.py` | ⬜ |
| Day 15 | 项目① FastAPI 化 + 复盘 | `app.py` | ⬜ |

## 运行

```powershell
uv run week03/day11_hybrid.py                 # 三路检索对比
uv run week03/day11_hybrid.py "私有化版的API配额是多少"   # 单查询明细
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
