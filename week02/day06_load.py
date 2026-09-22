"""Week2 Day6: 文档解析 —— 把 data/raw 的混合格式读成统一结构

学习目标:
1. 理解 RAG 第一步"数据接入": 不同格式 -> 统一的 {text, metadata} 结构
2. Markdown 直接读文本; PDF 用 pypdf 逐页抽取
3. metadata 的重要性: source / page / format (后续引用与过滤都靠它)

用法:
  uv run week02/day06_load.py            # 解析全部并打印统计
  uv run week02/day06_load.py 02_pricing # 只解析某文件并打印内容
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAW_DIR = Path(__file__).parent / "data" / "raw"


@dataclass
class Doc:
    """统一文档结构: 文本 + 元数据 (page 用于 PDF, 为 md 时为 0)。"""

    text: str
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:  # noqa: D105
        src = self.metadata.get("source", "?")
        page = self.metadata.get("page")
        loc = f" p.{page}" if page else ""
        return f"<Doc {src}{loc} ({len(self.text)}字)>"


def load_markdown(path: Path) -> list[Doc]:
    """Markdown: 整个文件作为一个 Doc, 保留标题行便于后续按标题分块。"""
    text = path.read_text(encoding="utf-8").strip()
    return [Doc(text=text, metadata={"source": path.name, "format": "markdown"})]


def load_pdf(path: Path) -> list[Doc]:
    """PDF: 逐页抽取, 每页一个 Doc (page 从 1 开始)。"""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    docs: list[Doc] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        docs.append(Doc(text=text, metadata={"source": path.name, "format": "pdf", "page": i}))
    return docs


def load_all(raw_dir: Path = RAW_DIR) -> list[Doc]:
    """按扩展名分派解析器, 读取目录下全部文档。"""
    docs: list[Doc] = []
    for path in sorted(raw_dir.iterdir()):
        suffix = path.suffix.lower()
        if suffix in (".md", ".markdown", ".txt"):
            docs.extend(load_markdown(path))
        elif suffix == ".pdf":
            docs.extend(load_pdf(path))
        else:
            print(f"  [跳过] 不支持格式: {path.name}")
    return docs


def print_stats(docs: list[Doc]) -> None:
    print(f"\n共加载 {len(docs)} 个 Doc")
    by_source: dict[str, int] = {}
    chars = 0
    for d in docs:
        by_source[d.metadata["source"]] = by_source.get(d.metadata["source"], 0) + 1
        chars += len(d.text)
    for src, n in by_source.items():
        print(f"  {src}: {n} 个 Doc")
    print(f"  文本合计: {chars:,} 字符 (粗估 ~{int(chars/1.6):,} tokens)")


def main() -> None:
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        docs = [d for d in load_all() if keyword in d.metadata["source"]]
        for d in docs:
            print("=" * 60)
            print(d)
            print("-" * 60)
            print(d.text)
        return

    docs = load_all()
    print_stats(docs)
    print("\n前 5 个 Doc 预览:")
    for d in docs[:5]:
        preview = d.text[:60].replace("\n", " ")
        print(f"  {d} : {preview}...")


if __name__ == "__main__":
    main()
