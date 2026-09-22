"""Week2 Day10: 失败模式测试集 + 复盘

目的: 用一组精心设计的问题"打脸"项目① MVP, 暴露 RAG 各类失败模式,
      作为 Week7 评测集的种子。

问题分七类:
  fact      事实题(应通过)
  list      列表题
  aggregate 聚合题(多值汇总)
  table     表格题
  multihop  多跳题(跨文档)
  keyword   精确关键词题(型号/编号)
  reject    拒答题(语料没有)

用法:
  uv run week02/day10_failures.py          # 跑全部
  uv run week02/day10_failures.py fact     # 只跑某类
  uv run week02/day10_failures.py --save   # 结果存到 notes/
"""

from __future__ import annotations

import sys
from pathlib import Path

from day09_rag import get_client, rag_once, search

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOTES = Path(__file__).parent / "notes"

CASES: list[tuple[str, str]] = [
    ("fact", "云雀 CRM 有哪些核心模块?"),
    ("fact", "企业版每月多少钱?"),
    ("list", "云雀 CRM 通过了哪些合规认证?"),
    ("aggregate", "标准版和企业版的 API 调用配额分别是多少?"),
    ("aggregate", "一次性购买 100 席位以上, 折扣最多能叠加到几折?"),
    ("table", "API 的默认 QPS 速率限制是多少?"),
    ("keyword", "私有化版(Skylark Private)的 API 配额是多少?"),
    ("multihop", "如果企业版用户忘记密码, 应该怎么处理?"),
    ("reject", "云雀 CRM 支持苹果手机的指纹登录吗?"),
    ("reject", "云雀 CRM 的 CEO 是谁?"),
]


def run_case(client, model: str, category: str, question: str) -> dict:
    hits = search(question, k=5)
    print("=" * 70)
    print(f"[{category}] {question}")
    print("-" * 70)
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        loc = m["source"] + (f" p.{m['page']}" if m.get("page") else "") + (f" · {m['heading']}" if m.get("heading") else "")
        print(f"  [{i}] sim={h['similarity']:.3f}  {loc}")
    reply = None
    try:
        from day09_rag import answer

        reply = answer(client, model, question, hits, verbose=False)
    except Exception as exc:  # noqa: BLE001
        reply = f"[ERROR] {exc}"
    print(f"\nAI> {reply}\n")
    return {"category": category, "question": question, "reply": reply,
            "sources": [h["metadata"]["source"] for h in hits]}


def main() -> None:
    only = None
    save = False
    for arg in sys.argv[1:]:
        if arg == "--save":
            save = True
        else:
            only = arg

    client, model = get_client()
    results = []
    for category, question in CASES:
        if only and category != only:
            continue
        results.append(run_case(client, model, category, question))

    if save:
        NOTES.mkdir(exist_ok=True)
        out = NOTES / "week2_failure_runs.md"
        lines = ["# Week2 失败模式测试结果\n"]
        for r in results:
            lines.append(f"## [{r['category']}] {r['question']}\n")
            lines.append(f"- 检索来源: {', '.join(r['sources'])}\n")
            lines.append(f"- 回答: {r['reply']}\n")
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"已保存: {out}")

    print(f"\n共跑 {len(results)} 个用例。请对照 notes/week2_failure_modes.md 归类。")


if __name__ == "__main__":
    main()
