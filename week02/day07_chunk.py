"""Week2 Day7: 分块策略实验

学习目标:
1. 理解分块为何影响召回: 太大切不准, 太小丢上下文
2. 手写三种策略并对比:
   - 固定长度 (fixed): 最简单, 但会切断句子/表格
   - 递归分隔 (recursive): 按段落->句子->词 逐级回退, 尽量在自然边界切
   - 标题层级 (markdown): 按 # 标题切, 语义完整, 但块长不均
3. 参数: chunk_size (字符) / chunk_overlap (重叠)
4. 观察每个 chunk 携带的 metadata 是否足以做引用

用法:
  uv run week02/day07_chunk.py                 # 对比全部文档的三种策略
  uv run week02/day07_chunk.py 02_pricing      # 详细看单个文件
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from day06_load import Doc, load_all

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def approx_tokens(text: str) -> int:
    """粗估 token: 中文 ~1.6 字/token, 非中文 ~4 字符/token。"""
    cn = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return int(cn / 1.6 + (len(text) - cn) / 4)


# ---------------------------------------------------------------------------
# 策略 1: 固定长度
# ---------------------------------------------------------------------------

def fixed_chunks(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    """按字符数硬切, 每 size 个字符一块, 相邻块重叠 overlap。"""
    step = max(1, size - overlap)
    return [text[i : i + size] for i in range(0, len(text), step) if text[i : i + size].strip()]


# ---------------------------------------------------------------------------
# 策略 2: 递归字符分隔 (LangChain RecursiveCharacterTextSplitter 的思想简化版)
# ---------------------------------------------------------------------------

SEPARATORS = ["\n\n", "\n", "。", "！", "？", ". ", "；", ";", "，", ",", " ", ""]


def _recursive_split_no_overlap(text: str, size: int, separators: list[str]) -> list[str]:
    """递归核心: 只负责切, 不加重叠 (避免每层递归重复加重叠)。"""
    if len(text) <= size:
        return [text] if text.strip() else []

    for i, sep in enumerate(separators):
        if sep == "":
            break
        if sep in text:
            parts = text.split(sep)
            # 把分隔符拼回, 保持原文
            merged = [p + (sep if j < len(parts) - 1 else "") for j, p in enumerate(parts) if p]
            chunks: list[str] = []
            buf = ""
            for piece in merged:
                if len(buf) + len(piece) <= size:
                    buf += piece
                else:
                    if buf:
                        chunks.append(buf)
                    # 单个 piece 仍超长 -> 用更细的分隔符递归
                    if len(piece) > size:
                        chunks.extend(_recursive_split_no_overlap(piece, size, separators[i + 1 :]))
                        buf = ""
                    else:
                        buf = piece
            if buf:
                chunks.append(buf)
            return [c for c in chunks if c.strip()]

    # 所有分隔符都不适用 -> 硬切
    return fixed_chunks(text, size, 0)


def recursive_split(text: str, size: int, overlap: int, separators: list[str] | None = None) -> list[str]:
    """递归分隔 + 顶层统一加重叠。"""
    separators = separators if separators is not None else SEPARATORS
    chunks = _recursive_split_no_overlap(text, size, separators)
    if overlap > 0 and len(chunks) > 1:
        out = [chunks[0]]
        for prev, cur in zip(chunks, chunks[1:]):
            out.append(prev[-overlap:] + cur)
        return out
    return chunks


# ---------------------------------------------------------------------------
# 策略 3: Markdown 标题层级
# ---------------------------------------------------------------------------

def markdown_chunks(text: str, max_size: int = 800) -> list[tuple[str, str]]:
    """按 # 标题切, 返回 (heading, body)。超长的小节再用递归切。"""
    lines = text.split("\n")
    chunks: list[tuple[str, str]] = []
    heading = ""
    body: list[str] = []

    def flush() -> None:
        content = "\n".join(body).strip()
        if not content:
            return
        if len(content) <= max_size:
            chunks.append((heading, content))
        else:
            for sub in recursive_split(content, max_size, 50):
                chunks.append((heading, sub))

    for line in lines:
        if line.startswith("#"):
            flush()
            heading = line.lstrip("#").strip()
            body = []
        else:
            body.append(line)
    flush()
    return chunks


# ---------------------------------------------------------------------------
# 应用策略到 Doc
# ---------------------------------------------------------------------------

def apply_strategy(docs: list[Doc], strategy: str, **kwargs) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        if strategy == "fixed":
            texts = fixed_chunks(doc.text, **kwargs)
            out.extend(Chunk(t, {**doc.metadata, "chunk": i}) for i, t in enumerate(texts))
        elif strategy == "recursive":
            texts = recursive_split(doc.text, kwargs.get("size", 400), kwargs.get("overlap", 50))
            out.extend(Chunk(t, {**doc.metadata, "chunk": i}) for i, t in enumerate(texts))
        elif strategy == "markdown":
            for i, (heading, body) in enumerate(markdown_chunks(doc.text, kwargs.get("max_size", 800))):
                out.append(Chunk(body, {**doc.metadata, "chunk": i, "heading": heading}))
        else:
            raise ValueError(f"未知策略: {strategy}")
    return out


def summarize(name: str, chunks: list[Chunk]) -> None:
    sizes = [len(c.text) for c in chunks]
    if not sizes:
        print(f"  {name}: 0 块")
        return
    avg = sum(sizes) / len(sizes)
    print(
        f"  {name:<12} 块数={len(chunks):>3}  "
        f"长度 min/avg/max = {min(sizes):>4}/{avg:>6.0f}/{max(sizes):>5}  "
        f"粗估 tokens 合计={sum(approx_tokens(c.text) for c in chunks):,}"
    )


def compare_all(docs: list[Doc]) -> None:
    print("三种策略对比 (size=400, overlap=50, markdown max_size=800):\n")
    summarize("fixed", apply_strategy(docs, "fixed", size=400, overlap=50))
    summarize("recursive", apply_strategy(docs, "recursive", size=400, overlap=50))
    summarize("markdown", apply_strategy(docs, "markdown", max_size=800))

    print("\n--- 固定长度为何会切断句子? 看 02_pricing.md 前两块 ---")
    pricing = [d for d in docs if d.metadata["source"] == "02_pricing.md"][0]
    for i, t in enumerate(fixed_chunks(pricing.text, 400, 50)[:2]):
        print(f"\n[fixed #{i}] ...{t[-40:]!r}  <- 结尾")
        print(f"           切到了: {t[360:410]!r}")

    print("\n--- 递归分隔的边界 (同样 400) ---")
    for i, t in enumerate(recursive_split(pricing.text, 400, 50)[:2]):
        print(f"\n[recursive #{i}] 开头 {t[:40]!r}")
        print(f"                 结尾 {t[-40:]!r}")

    print("\n--- Markdown 标题块 (heading 作为 metadata) ---")
    for c in apply_strategy([pricing], "markdown", max_size=800)[:4]:
        print(f"  heading={c.metadata['heading']!r:<18} 长度={len(c.text)}  开头={c.text[:24]!r}")


def detail(docs: list[Doc], keyword: str) -> None:
    target = [d for d in docs if keyword in d.metadata["source"]]
    if not target:
        print(f"未找到 {keyword}")
        return
    for d in target:
        print("=" * 70)
        print(d)
        for name in ("fixed", "recursive", "markdown"):
            print(f"\n### {name}")
            for i, c in enumerate(apply_strategy([d], name, size=400, overlap=50, max_size=800)):
                head = f"[{c.metadata.get('heading','')}]" if c.metadata.get("heading") else ""
                print(f"  #{i} len={len(c.text):>4} {head} {c.text[:50]!r}")


def main() -> None:
    docs = load_all()
    if len(sys.argv) > 1:
        detail(docs, sys.argv[1])
    else:
        compare_all(docs)


if __name__ == "__main__":
    main()
