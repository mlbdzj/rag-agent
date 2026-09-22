# Week 3 · 自检问答（混合检索/Rerank/查询优化）

> 面试口述素材。先自己答，再对照。

## Day 11 · 混合检索

**Q1：为什么需要混合检索？纯向量或纯 BM25 各自短板是什么？**

- 纯向量（bi-encoder）：懂语义/改写，但对**关键词、型号、编号、表格、数字**不敏感
  - 例："ISO 27001"、"SK-2000"、"6 折" 这类 token 在向量空间信号弱
- 纯 BM25：精确词匹配强（尤其稀有词/术语），但不懂同义与改写
  - 例："产品按部署形态分几个版本" vs 原文"产品线"——BM25 词不匹配就召回不到
- 混合：两路并行召回，互补盲区

**Q2：RRF 为什么只融合排名、不融合分数？**

- 不同检索器分数量纲不可比：向量是余弦 0~1，BM25 是无界分值
- 归一化分数会引入假设与调参负担；排名是**天然可比的序信息**
- `score(d) = Σ 1/(k + rank(d))`，k=60 抑制头部过强，强调多路共识
- 优点：无需调权重、鲁棒；缺点：忽略分数差距，可能压低单路独家命中

**Q3：本语料下为什么混合没有明显胜出？**

- 语料小（34 块）且主题重叠，大量块在两路都出现
- RRF 让"两路都出现但一般相关"的块双重加分，把 gold 表块（vector#7/bm25#10）挤出 top-5
- 修法：加大 fetch、加权 RRF、**融合后 Rerank**（Day12）
- 结论：**RRF 不是银弹**，收益依赖两个检索器的互补性与候选深度

**Q4：中文 BM25 为什么需要分词？**

- BM25 基于词频，中文需先切词（jieba），否则按字计算会破坏词粒度统计
- 停用词（的/了/是）过滤可降低噪声、提升关键词权重
- 分块要小（256）：高频词落在小块里 IDF 信号更集中

**Q5：hit@k 与 MRR 的区别？**

- hit@k：top-k 里有没有 gold（是/否），适合快速对比
- MRR：gold 排名倒数的均值（1/rank），对"排得靠前"敏感
- 检索评测应两者都看：hit@k 看召回，MRR/Rank 看排序质量

---

## Day 12 · Rerank 重排序

**Q1：bi-encoder 与 cross-encoder 的区别？**

| | bi-encoder（向量/BM25 粗排） | cross-encoder（重排） |
|---|---|---|
| 输入 | query 与 doc **各自**编码 | (query, doc) **成对**输入 |
| 交互 | 无（只在向量空间比） | 全交叉注意力，逐对判断 |
| 速度 | 快，可预计算 doc 向量 | 慢，每次查询现算 |
| 用途 | 海量召回（top-N） | 小候选精排（top-k） |

**Q2：为什么生产是"粗排 + 精排"两段式？**

- 粗排：从百万文档里快速召回 top-N（保**召回**，宁滥勿缺）
- 精排：对 N 个候选精算相关性，选出 top-k（保**精度**）
- 若只用 cross-encoder 全库打分：O(N) 次模型推理，不可接受
- 若只用粗排：精度不足，假阳性混入

**Q3：RRF 之后为什么还要 Rerank？**

- RRF 只融合**排名**，不判断真实相关性，且会压低单路独家命中
- Rerank 真正逐条读 (query, chunk)，把"两路都出现但无关"的块挤下去
- 两者互补：RRF 保召回与稳定，Rerank 提精度

**Q4：本次 rerank 为什么效果反而变差？**

- `bge-reranker-base` 太小，在中文表格/碎片块上不可靠
- 例：含 "ISO 27001" 的块被排到 #16，无关块排前面
- 延迟高（20 条 ~4.5s CPU）
- **教训**：rerank 模型选型决定成败；base 不够，应选 v2-m3 / GTE / Cohere 等

**Q5：BGE 重排器也要加查询指令前缀吗？**

- 实测：加前缀能让干净 pair 的顺序由错变对（必要条件）
- 但完整语料上仍不足 → 前缀是必要非充分，模型能力才是关键
- 一般建议：BGE 系列统一用 `为这个句子生成表示以用于检索相关文章：`

**Q6：重排的延迟如何优化？**

- 控制候选数 N（如 20~50，不是 100+）
- 用 GPU 或 ONNX/量化推理
- 用托管重排 API（Cohere/Jina）
- 缓存 query 的 rerank 结果（同 query 重复时）

---

## Day 13 · LlamaIndex

**Q1：LlamaIndex 的核心抽象链条？**

```
Document(原始) --SentenceSplitter--> Node(块) --VectorStoreIndex--> Index
                                                    |
                                          as_retriever() -> Retriever -> NodeWithScore
```

- `Document`：原始文本 + metadata
- `Node`：分块后的最小检索单元（含元数据与关系）
- `Index`：把 Node 组织起来（VectorStoreIndex 存向量）
- `Retriever`：查询时返回带 score 的 Node 列表

**Q2：LlamaIndex 2.0 与旧版的区别？**

- 旧版：`ServiceContext.from_defaults(llm=..., embed_model=...)`
- 2.0：全局 `Settings.llm / Settings.embed_model / Settings.chunk_size`，已移除 ServiceContext
- 迁移时把 ServiceContext 配置改为 Settings 赋值即可

**Q3：如何让 LlamaIndex 用本地模型且不联网？**

- `HuggingFaceEmbedding(model_name=<本地快照路径>)`：直接指向 `~/.cache/huggingface/.../snapshots/<hash>`
- 设 `HF_HUB_OFFLINE=1`：强制只用缓存，杜绝任何下载
- 适合内网/离线环境，也避免每次误触发联网

**Q4：用了 LlamaIndex，FM-1 为什么还是失败？**

- 同一问题"私有化版 API 配额"，LlamaIndex 检索 top-5 仍无正确表块
- **结论：检索成败取决于语料结构、分块策略、检索方式，而不是框架**
- 框架只是把流程标准化，解决不了"表格被切散 + 纯向量不敏感"的根本问题
- 真正的解法：表格结构化、混合检索、更强重排（Week3 Day11/12 的方向）

**Q5：手写管线 vs LlamaIndex 怎么选？**

| 维度 | 手写 | LlamaIndex |
|---|---|---|
| 代码量 | 多（~100 行） | 少（~15 行） |
| 可控性 | 完全可控，易定制 | 需熟悉其抽象与扩展点 |
| 生态 | 无 | 连接器/索引/检索器丰富 |
| 调试 | 透明 | 有黑盒性 |

- 学习阶段：手写一遍懂原理，再用框架提效
- 生产：数据链路复杂选 LlamaIndex；要极致控制可手写关键环节


