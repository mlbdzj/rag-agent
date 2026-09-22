# Week 2 复盘 · RAG 核心链路（项目① MVP）

## 五天做了什么

| Day | 主题 | 关键产出 |
|-----|------|----------|
| 6 | 文档解析 | `make_corpus.py` / `day06_load.py`：多格式 → 统一 Doc |
| 7 | 分块策略 | `day07_chunk.py`：fixed / recursive / markdown 三策略对比 |
| 8 | Embedding + 向量库 | `embeddings.py` / `day08_embed_store.py`：BGE + Chroma 入库检索 |
| 9 | RAG 全链路 | `day09_rag.py`：项目① MVP（检索→生成→引用） |
| 10 | 失败模式 | `day10_failures.py` + 失败模式分类 |

## RAG 管线全景（Week2 已实现的部分）

```
数据接入        解析         分块          向量化         存储        检索        生成
raw/*.md/pdf → Doc{text, → Chunk{text, → BGE encode → Chroma   → top-k   → LLM
                metadata}    metadata}                 (cosine)    + rerank*   + 引用
  Day6           Day6         Day7          Day8         Day8       Day8      Day9
                                                              (*Week3 补)
```

## 项目① MVP 能力边界

**擅长**：事实题、列表题、聚合题（9/10 通过），且能正确拒答语料外问题。

**瓶颈**：检索侧
- 关键词/型号/表格 → 纯向量弱（FM-1、FM-4）
- 块粒度 → 多主题同块竞争（FM-2）
- 语义假阳性 → 缺精确匹配兜底（FM-3）

## 技术选型记录

| 环节 | 选择 | 理由 |
|------|------|------|
| Embedding | BAAI/bge-small-zh-v1.5（本地） | 免费、中文好、512 维、~95MB |
| 向量库 | Chroma PersistentClient | 零配置、本地、学习友好 |
| 相似度 | cosine（hnsw:space=cosine） | BGE 归一化后标准做法 |
| 分块 | recursive, size=400, overlap=50 | 自然边界，先用默认值再调 |
| k | 5 | 召回与上下文成本的平衡 |

## 必须能口述的 8 个点

1. RAG 为什么存在：知识截止 / 幻觉 / 私有数据
2. 数据接入的统一结构 `{text, metadata}`，metadata 用于引用与过滤
3. 分块三策略取舍 + overlap 的作用与代价
4. BGE 的 query/passage 非对称编码
5. 向量库三要素 + 余弦相似度
6. RAG prompt 三原则（只依据资料 / 标注引用 / 不知道就说）
7. 纯向量检索的天然短板：关键词、型号、表格、数字
8. 检索质量决定回答质量——检索错则幻觉必然发生

## 实测踩到的真实坑（可写博客）

1. **PDF 多页 chunk id 冲突**：`source#chunk` 不唯一 → 加入 `page`
2. **段落书写不对称**：`标准版` 漏写产品名导致向量误排 → 块格式要一致
3. **表格漏召**：私有化版 API 配额信息在库中却检索不到 → Week3 混合检索解决
4. **transformers 5.x API 重命名**：`get_sentence_embedding_dimension` → `get_embedding_dimension`

## Week 3 预告

把 Naive RAG 升级为**生产级 Hybrid RAG**：
- 混合检索（向量 + BM25 + RRF 融合）
- Rerank 重排序（cross-encoder）
- LlamaIndex 重构
- 查询侧优化（多查询 / HyDE / 子问题分解）

目标：把 FM-1、FM-3 打掉，召回率可量化提升。
