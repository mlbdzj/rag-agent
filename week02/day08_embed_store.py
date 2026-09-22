"""Week2 Day8: Embedding + Chroma 入库与检索

学习目标:
1. 完整管线: load(day06) -> chunk(day07) -> embed(BGE) -> store(Chroma)
2. 理解向量库三要素: 向量 + 原始文本(document) + 元数据(metadata)
3. 余弦距离与相似度: similarity = 1 - distance
4. 观察 top-k 检索结果与分数, 建立"召回"直觉

用法:
  uv run week02/day08_embed_store.py build          # 重建索引
  uv run week02/day08_embed_store.py query "企业版多少钱"  # 检索
  uv run week02/day08_embed_store.py                 # 交互检索
"""

from __future__ import annotations

import sys
from pathlib import Path

from day06_load import load_all
from day07_chunk import apply_strategy
from embeddings import BGEEmbedder

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION = "skylark"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


def get_client():
    import chromadb

    return chromadb.PersistentClient(path=str(DB_DIR))


def build(chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP, strategy: str = "recursive") -> None:
    docs = load_all()
    chunks = apply_strategy(docs, strategy, size=chunk_size, overlap=overlap, max_size=800)
    print(f"解析 {len(docs)} 个 Doc -> 分块 {len(chunks)} 个 (strategy={strategy}, size={chunk_size})")

    embedder = BGEEmbedder()
    print(f"Embedding 模型: {embedder.model_name} dim={embedder.dim}, 开始编码...")
    texts = [c.text for c in chunks]
    vectors = embedder.encode_passages(texts)

    client = get_client()
    # 重建: 删除同名集合
    try:
        client.delete_collection(COLLECTION)
    except Exception:  # noqa: BLE001
        pass
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    ids = [
        f"{c.metadata['source']}#p{c.metadata.get('page', 0)}#{c.metadata['chunk']}"
        for c in chunks
    ]
    metadatas = [
        {"source": c.metadata["source"], "format": c.metadata.get("format", ""),
         "page": c.metadata.get("page", 0), "heading": c.metadata.get("heading", "")}
        for c in chunks
    ]
    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)
    print(f"已写入 Chroma: {DB_DIR} (collection={COLLECTION}, {collection.count()} 条)")


def get_collection():
    client = get_client()
    return client.get_collection(COLLECTION)


def search(query: str, k: int = 5) -> list[dict]:
    embedder = BGEEmbedder()
    qvec = embedder.encode_query(query)
    col = get_collection()
    res = col.query(query_embeddings=[qvec], n_results=k)
    hits = []
    for i in range(len(res["ids"][0])):
        hits.append(
            {
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
                "similarity": 1 - res["distances"][0][i],
            }
        )
    return hits


def print_hits(query: str, hits: list[dict]) -> None:
    print(f"\n查询: {query}")
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        loc = f"{m['source']}" + (f" p.{m['page']}" if m.get("page") else "") + (f" [{m['heading']}]" if m.get("heading") else "")
        print(f"\n  #{i} sim={h['similarity']:.4f} dist={h['distance']:.4f}  {loc}")
        print(f"     {h['text'][:120].replace(chr(10), ' ')}...")


def interactive() -> None:
    print("输入问题检索 (空行退出):")
    while True:
        try:
            q = input("\n问> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        print_hits(q, search(q))


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build()
        return
    if not DB_DIR.exists():
        print("索引不存在, 先运行: uv run week02/day08_embed_store.py build")
        sys.exit(1)
    if len(sys.argv) > 1 and sys.argv[1] == "query":
        print_hits(" ".join(sys.argv[2:]), search(" ".join(sys.argv[2:])))
    else:
        interactive()


if __name__ == "__main__":
    main()
