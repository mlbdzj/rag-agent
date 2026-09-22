"""Week3 Day11: 混合检索 (BM25 + 向量 + RRF 融合)

为什么需要混合检索:
  - 纯向量: 语义强, 但对关键词/型号/编号/表格/数字弱 (FM-1)
  - 纯 BM25: 精确词匹配强, 但不懂语义 (同义、改写就召回不到)
  - 混合: 两路互补, 用 RRF 融合, 兼顾召回与精度

RRF (Reciprocal Rank Fusion):
  score(d) = sum_over_rankers  1 / (k + rank(d))   (k 常取 60)
  只依赖"排名"不依赖"分数", 免去不同检索器分数量纲不一致的问题

用法:
  uv run week03/day11_hybrid.py            # 对比三路检索
  uv run week03/day11_hybrid.py "私有化版的API配额是多少"
"""

from __future__ import annotations

import sys
from pathlib import Path

import jieba

# 复用 week02 的解析/分块/向量
sys.path.insert(0, str(Path(__file__).parent.parent / "week02"))
from day06_load import load_all  # noqa: E402
from day07_chunk import apply_strategy  # noqa: E402
from embeddings import BGEEmbedder  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHUNK_SIZE = 256      # 混合检索更适合较小分块 (BM25 关键词信号更集中)
CHUNK_OVERLAP = 30
RRF_K = 60


# ---------------------------------------------------------------------------
# 中文分词 (BM25 需要)
# ---------------------------------------------------------------------------

STOPWORDS = set("的了吗呢啊是在和与及等对于把被这那有也就都而及其之或一个我们你他她它")


def tokenize(text: str) -> list[str]:
    return [t for t in jieba.lcut(text.lower()) if t.strip() and t not in STOPWORDS and not t.isspace()]


# ---------------------------------------------------------------------------
# 检索器
# ---------------------------------------------------------------------------

class Retriever:
    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> None:
        self.docs = load_all()
        self.chunks = apply_strategy(self.docs, "recursive", size=chunk_size, overlap=overlap, max_size=800)
        self.texts = [c.text for c in self.chunks]
        self.meta = [c.metadata for c in self.chunks]
        print(f"分块: {len(self.chunks)} 个 (size={chunk_size}, overlap={overlap})")

        # BM25 索引
        from rank_bm25 import BM25Okapi

        self.tokenized = [tokenize(t) for t in self.texts]
        self.bm25 = BM25Okapi(self.tokenized)

        # 向量索引 (内存)
        self.embedder = BGEEmbedder()
        print("编码全部块 (BGE)...")
        self.vectors = self.embedder.encode_passages(self.texts)

    # --- 向量检索 ---
    def vector_search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        q = self.embedder.encode_query(query)
        scored = []
        for i, v in enumerate(self.vectors):
            sim = sum(a * b for a, b in zip(q, v))  # 已归一化
            scored.append((i, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    # --- BM25 检索 ---
    def bm25_search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        tokens = tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:k]

    # --- RRF 融合 ---
    def hybrid_search(self, query: str, k: int = 10, fetch: int = 20) -> list[tuple[int, float]]:
        vec = self.vector_search(query, fetch)
        bm = self.bm25_search(query, fetch)
        scores: dict[int, float] = {}
        for ranker in (vec, bm):
            for rank, (idx, _) in enumerate(ranker):
                scores[idx] = scores.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:k]

    def label(self, idx: int) -> str:
        m = self.meta[idx]
        loc = m["source"] + (f" p.{m['page']}" if m.get("page") else "") + (f" · {m['heading']}" if m.get("heading") else "")
        return loc


# ---------------------------------------------------------------------------
# 对比测试
# ---------------------------------------------------------------------------

# (query, gold 来源文件, gold 唯一子串)
CASES = [
    ("私有化版的API配额是多少", "04_api_spec.md", "服务器规格"),      # FM-1 关键词/表格
    ("API的默认QPS速率限制是多少", "04_api_spec.md", "QPS"),
    ("企业版每月多少钱", "02_pricing.md", "599"),
    ("一次性购买100席位折扣最多几折", "02_pricing.md", "6 折"),
    ("云雀CRM通过了哪些合规认证", "05_security.md", "ISO 27001"),
    ("产品按部署形态分成哪几个版本", "01_overview.md", "产品线"),      # 改写题, 向量应占优
]


def gold_rank(hits: list[tuple[int, float]], r: Retriever, source: str, needle: str) -> int:
    """gold 块在结果中的名次 (1 起); 未召回返回 0。"""
    for rank, (i, _) in enumerate(hits, 1):
        if r.meta[i]["source"] == source and needle in r.texts[i]:
            return rank
    return 0


def compare(r: Retriever, k: int = 5) -> None:
    methods = (("vector", r.vector_search), ("bm25", r.bm25_search), ("hybrid", r.hybrid_search))
    print(f"\n{'='*72}\n三路检索对比: hit@{k} 与 gold 块排名\n{'='*72}")
    stats = {name: 0 for name, _ in methods}
    for query, source, needle in CASES:
        print(f"\n查询: {query}")
        print(f"  gold: {source} 含 {needle!r}")
        for name, fn in methods:
            hits = fn(query, k)
            rank = gold_rank(hits, r, source, needle)
            ok = rank > 0
            stats[name] += ok
            tag = f"HIT@#{rank}" if ok else "MISS"
            print(f"    [{tag:>8}] {name:<7}")
    print(f"\nhit@{k} 汇总: " + "  ".join(f"{name}={stats[name]}/{len(CASES)}" for name, _ in methods))


def detail(r: Retriever, query: str, k: int = 5) -> None:
    for name, fn in (("vector", r.vector_search), ("bm25", r.bm25_search), ("hybrid", r.hybrid_search)):
        print(f"\n### {name}")
        for rank, (i, score) in enumerate(fn(query, k), 1):
            snippet = r.texts[i][:70].replace("\n", " ")
            print(f"  #{rank} score={score:.4f} {r.label(i)}")
            print(f"      {snippet}...")


def main() -> None:
    r = Retriever()
    if len(sys.argv) > 1:
        detail(r, " ".join(sys.argv[1:]))
    else:
        compare(r)


if __name__ == "__main__":
    main()
