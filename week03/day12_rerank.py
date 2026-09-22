"""Week3 Day12: Rerank 重排序 (cross-encoder)

为什么需要 Rerank:
  - 粗排(bi-encoder: 向量/BM25) 为速度牺牲精度: query 与 chunk 各自编码, 从不见面
  - 精排(cross-encoder): 把 (query, chunk) 成对送进模型逐条打分, 判断力强但慢
  - 生产范式: 粗排召回 top-N (保召回) -> rerank 精排 top-k (保精度)

模型: BAAI/bge-reranker-base (中文 cross-encoder, ~1.1GB, 首次下载走 hf-mirror)

用法:
  uv run week03/day12_rerank.py            # 对比 hybrid vs hybrid+rerank
  uv run week03/day12_rerank.py "私有化版的API配额是多少"
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

sys.path.insert(0, str(Path(__file__).parent))
from day11_hybrid import CASES, Retriever, gold_rank  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RERANK_MODEL = "BAAI/bge-reranker-base"
FETCH = 20   # 粗排候选深度
TOPK = 5
# BGE 系列 cross-encoder 与 embedding 同理: 查询需加指令前缀, 否则排序质量骤降
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


class Reranker:
    def __init__(self, model_name: str = RERANK_MODEL, use_instruction: bool = True) -> None:
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name, max_length=512)
        self.model_name = model_name
        self.use_instruction = use_instruction

    def rerank(self, query: str, texts: list[str]) -> list[float]:
        q = (QUERY_INSTRUCTION + query) if self.use_instruction else query
        pairs = [(q, t) for t in texts]
        scores = self.model.predict(pairs, show_progress_bar=False)
        return [float(s) for s in scores]


def hybrid_candidates(r: Retriever, query: str) -> list[int]:
    hits = r.hybrid_search(query, k=FETCH, fetch=FETCH)
    return [i for i, _ in hits]


def rerank_search(r: Retriever, rr: Reranker, query: str, k: int = TOPK) -> tuple[list[tuple[int, float]], float]:
    cand = hybrid_candidates(r, query)
    texts = [r.texts[i] for i in cand]
    t0 = time.perf_counter()
    scores = rr.rerank(query, texts)
    dt = (time.perf_counter() - t0) * 1000
    ranked = sorted(zip(cand, scores), key=lambda x: x[1], reverse=True)[:k]
    return ranked, dt


def compare(r: Retriever, rr: Reranker, k: int = TOPK) -> None:
    print(f"\n{'='*72}\n粗排(hybrid) vs 精排(hybrid+rerank)  hit@{k}\n{'='*72}")
    base_hits = 0
    rr_hits = 0
    for query, source, needle in CASES:
        base = r.hybrid_search(query, k=k, fetch=FETCH)
        reranked, dt = rerank_search(r, rr, query, k)
        b_rank = gold_rank(base, r, source, needle)
        r_rank = gold_rank(reranked, r, source, needle)
        base_hits += b_rank > 0
        rr_hits += r_rank > 0
        print(f"\n查询: {query}  (gold: {source} 含 {needle!r})")
        print(f"  hybrid         : {'HIT@#'+str(b_rank) if b_rank else 'MISS'}")
        print(f"  hybrid+rerank  : {'HIT@#'+str(r_rank) if r_rank else 'MISS'}   (精排耗时 {dt:.0f}ms/{len(hybrid_candidates(r, query))}条)")
    n = len(CASES)
    print(f"\n汇总 hit@{k}: hybrid={base_hits}/{n}  hybrid+rerank={rr_hits}/{n}")


def detail(r: Retriever, rr: Reranker, query: str, k: int = 5) -> None:
    cand = hybrid_candidates(r, query)
    print(f"\n粗排候选 {len(cand)} 条, 精排前 {k}:")
    reranked, dt = rerank_search(r, rr, query, k)
    for rank, (i, score) in enumerate(reranked, 1):
        print(f"  #{rank} rerank={score:+.4f}  {r.label(i)}")
        print(f"      {r.texts[i][:80]!r}")
    print(f"精排耗时: {dt:.0f}ms")


def main() -> None:
    r = Retriever()
    print(f"加载 reranker: {RERANK_MODEL} ...")
    rr = Reranker()
    if len(sys.argv) > 1:
        detail(r, rr, " ".join(sys.argv[1:]))
    else:
        compare(r, rr)


if __name__ == "__main__":
    main()
