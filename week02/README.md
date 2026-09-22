# Week 2 · RAG 核心链路（项目① MVP）

**语料**：虚构产品「云雀 CRM」知识库（7 个 Markdown + 1 个 PDF），覆盖精确匹配/多跳/聚合/拒答场景
**向量库**：Chroma（入门，后续可平滑换 pgvector）

| Day | 主题 | 脚本 | 状态 |
|-----|------|------|------|
| Day 6 | 语料准备 + 文档解析 | `make_corpus.py` / `day06_load.py` | ✅ |
| Day 7 | 分块策略实验 | `day07_chunk.py` | ✅ |
| Day 8 | Embedding + Chroma 入库检索 | `day08_embed_store.py` | ✅ |
| Day 9 | 检索→生成全链路（项目① MVP） | `day09_rag.py` | ✅ |
| Day 10 | 失败模式实验 + 复盘 | — | ⬜ |

> 自检问答见 **[QA.md](./QA.md)**

## 运行

```powershell
# 生成语料（可重复运行，会清空重建 data/raw）
uv run week02/make_corpus.py

# 解析并统计
uv run week02/day06_load.py
uv run week02/day06_load.py admin_guide   # 查看某文件内容

# 分块策略对比
uv run week02/day07_chunk.py
uv run week02/day07_chunk.py 02_pricing   # 单文件三策略对比

# 向量化与检索 (首次会自动下载 BGE 模型, 走 hf-mirror)
uv run week02/embeddings.py                     # 验证 embedding
uv run week02/day08_embed_store.py build        # 建索引
uv run week02/day08_embed_store.py query "企业版多少钱"
uv run week02/day08_embed_store.py              # 交互检索

# RAG 全链路 (项目① MVP)
uv run week02/day09_rag.py "企业版多少钱"
uv run week02/day09_rag.py                      # 交互问答
```

## 语料说明

| 文件 | 用途 |
|------|------|
| `01_overview.md` | 架构/模块（多跳背景） |
| `02_pricing.md` | 定价数字（聚合问题） |
| `03_faq.md` | 问答对 |
| `04_api_spec.md` | 型号/端点（精确关键词匹配） |
| `05_security.md` | 合规（ISO 27001 / 等保三级） |
| `06_changelog.md` | 版本历史（时间问题） |
| `07_integration.md` | 集成（跨文档引用） |
| `admin_guide.pdf` | PDF 解析测试（2 页 5 章） |

## Day 6 自检

- [ ] 说出 RAG 第一步"数据接入"要产出什么结构
- [ ] 解释 metadata 的 source/page 在后续哪两个环节被用到
- [ ] 运行 `day06_load.py admin_guide` 确认 PDF 中文抽取正常
- [ ] 思考：为什么 PDF 按"页"存、Markdown 按"文件"存？（Day7 分块会用到）

## Day 7 自检

- [ ] 口述三种分块策略的差异（fixed 会切断句子 / recursive 找自然边界 / markdown 保标题语义）
- [ ] 观察：`fixed` 结尾常是半句，`markdown` 块长不均（42~721）
- [ ] 解释 `chunk_overlap` 的作用与代价
- [ ] 说出字符级重叠的缺陷（会从词中间切入，如 `' 万次'`）
- [ ] 思考：为什么混合检索（Week3）更适合**较小**分块（如 256）？

## Day 8 自检

- [ ] 口述向量库三要素（向量/document/metadata）
- [ ] 解释 BGE 为何 query 加指令前缀、passage 不加
- [ ] 说出 `similarity = 1 - distance` 与 `hnsw:space=cosine`
- [ ] 复现"段落书写不一致导致误排"的现象
- [ ] 记录本次检索的两个问题（块粒度、语义假阳性）

## Day 9 自检

- [x] RAG 全链路跑通：`企业版多少钱` → 正确价格 + 引用 [1]
- [x] 聚合问题：各套餐 API 配额 → 标准版/企业版答对
- [x] 拒答问题：指纹登录（语料没有）→ 正确回答"资料中未找到"
- [ ] 口述 RAG prompt 三原则（只依据资料 / 标注引用 / 不知道就说）
- [ ] 分析漏召：私有化版 API 配额在 `04_api_spec.md` 却未被检索到
