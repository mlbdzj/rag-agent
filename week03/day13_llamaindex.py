"""Week3 Day13: LlamaIndex 2.0 重构

对比目标:
  手写管线 (week02 day06-09): 解析/分块/embed/存储/检索 全自己写
  LlamaIndex:                VectorStoreIndex 几行搞定

学习目标:
1. LlamaIndex 的抽象: Document -> Node(SentenceSplitter) -> Index -> Retriever
2. 2.0 关键变化: 全局 Settings 取代旧版 ServiceContext
3. 本地 BGE 接入: HuggingFaceEmbedding 指到本地快照, 不联网
4. 混合检索: QueryFusionRetriever(向量+BM25) 内置 RRF 思路

说明: LLM 生成仍用我们的 DeepSeek 客户端 (llama-index-llms-openai-like 与 openai 3.x 冲突)

用法:
  uv run week03/day13_llamaindex.py build     # 建索引
  uv run week03/day13_llamaindex.py "企业版多少钱"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 复用 week02 的语料解析
sys.path.insert(0, str(Path(__file__).parent.parent / "week02"))
from day06_load import load_all  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

# 离线: 只用本地缓存, 不联网下载
os.environ.setdefault("HF_HUB_OFFLINE", "1")

CHROMA_DIR = Path(__file__).parent / "chroma_llama"
COLLECTION = "skylark_llama"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 30


def local_bge_path() -> str:
    """定位本地 BGE 快照, 避免任何网络请求。找不到则回退模型名。"""
    hub = Path.home() / ".cache" / "huggingface" / "hub" / "models--BAAI--bge-small-zh-v1.5" / "snapshots"
    if hub.exists():
        snaps = [p for p in hub.iterdir() if p.is_dir()]
        if snaps:
            return str(snaps[0])
    return "BAAI/bge-small-zh-v1.5"


def setup_settings():
    """2.0 用全局 Settings 统一配置 (取代旧版 ServiceContext)。"""
    from llama_index.core import Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    Settings.embed_model = HuggingFaceEmbedding(model_name=local_bge_path())
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP
    return Settings


def build() -> None:
    import chromadb
    from llama_index.core import Document, StorageContext, VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.vector_stores.chroma import ChromaVectorStore

    setup_settings()

    raw_docs = load_all()
    li_docs = [
        Document(text=d.text, metadata={**d.metadata})
        for d in raw_docs
    ]
    print(f"LlamaIndex Document: {len(li_docs)} 个")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION)
    except Exception:  # noqa: BLE001
        pass
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    index = VectorStoreIndex.from_documents(
        li_docs, storage_context=storage_context, transformations=[splitter]
    )
    index.storage_context.persist(persist_dir=str(CHROMA_DIR / "storage"))
    print(f"索引完成: {collection.count()} 个节点 -> {CHROMA_DIR}")


def get_index():
    import chromadb
    from llama_index.core import StorageContext, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return VectorStoreIndex.from_vector_store(
        vector_store, storage_context=StorageContext.from_defaults(vector_store=vector_store)
    )


def get_llm():
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    base = os.getenv("OPENAI_BASE_URL", "").strip() or None
    model = os.getenv("OPENAI_MODEL", "deepseek-chat").strip()
    return OpenAI(api_key=key, base_url=base), model


def retrieve(query: str, top_k: int = 5) -> list:
    setup_settings()
    index = get_index()
    retriever = index.as_retriever(similarity_top_k=top_k)
    return retriever.retrieve(query)


def generate(client, model: str, query: str, nodes: list) -> str:
    context = "\n\n".join(
        f"[{i}] 来源: {n.metadata.get('source','?')}"
        + (f" p.{n.metadata['page']}" if n.metadata.get("page") else "")
        + f"\n{n.text}"
        for i, n in enumerate(nodes, 1)
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "只依据资料回答, 用 [编号] 标注引用, 找不到就说'资料中未找到相关信息', 中文简洁。"},
            {"role": "user", "content": f"<资料>\n{context}\n</资料>\n\n问题: {query}"},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content or ""


def ask(query: str) -> None:
    nodes = retrieve(query)
    print(f"\n[检索到 {len(nodes)} 个节点]")
    for i, n in enumerate(nodes, 1):
        m = n.metadata
        loc = m.get("source", "?") + (f" p.{m['page']}" if m.get("page") else "")
        print(f"  [{i}] score={n.score:.4f}  {loc}")
    client, model = get_llm()
    print("\nAI>", generate(client, model, query, nodes))


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build()
        return
    if len(sys.argv) > 1:
        ask(" ".join(sys.argv[1:]))
        return
    print("LlamaIndex 问答 (空行退出)")
    while True:
        try:
            q = input("\n问> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        ask(q)


if __name__ == "__main__":
    main()
