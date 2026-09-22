# Week 2 · RAG 核心链路（项目① MVP）

**语料**：虚构产品「云雀 CRM」知识库（7 个 Markdown + 1 个 PDF），覆盖精确匹配/多跳/聚合/拒答场景
**向量库**：Chroma（入门，后续可平滑换 pgvector）

| Day | 主题 | 脚本 | 状态 |
|-----|------|------|------|
| Day 6 | 语料准备 + 文档解析 | `make_corpus.py` / `day06_load.py` | ✅ |
| Day 7 | 分块策略实验 | `day07_chunk.py` | ⬜ |
| Day 8 | Embedding + Chroma 入库检索 | `day08_embed_store.py` | ⬜ |
| Day 9 | 检索→生成全链路（项目① MVP） | `day09_rag.py` | ⬜ |
| Day 10 | 失败模式实验 + 复盘 | — | ⬜ |

## 运行

```powershell
# 生成语料（可重复运行，会清空重建 data/raw）
uv run week02/make_corpus.py

# 解析并统计
uv run week02/day06_load.py
uv run week02/day06_load.py admin_guide   # 查看某文件内容
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
