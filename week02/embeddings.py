"""Week2: 本地 BGE Embedding 封装

BGE (BAAI General Embedding) 中文检索要点:
1. 段落(passage)直接编码; 查询(query)需加固定指令前缀, 效果更好
2. 归一化后用余弦相似度检索 (Chroma 需显式设 hnsw:space=cosine)
3. 首次运行会下载模型; 国内可设 HF_ENDPOINT=https://hf-mirror.com
"""

from __future__ import annotations

import os

# 若未设置 HF 镜像, 默认走国内镜像 (避免下载失败)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from functools import lru_cache

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


class BGEEmbedder:
    """封装 BGE: 段落与查询分别编码 (查询带指令前缀)。"""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self.model_name = model_name

    @property
    def dim(self) -> int:
        model = get_model()
        # transformers 5.x 将 get_sentence_embedding_dimension 重命名为 get_embedding_dimension
        if hasattr(model, "get_embedding_dimension"):
            return model.get_embedding_dimension()
        return model.get_sentence_embedding_dimension()

    def encode_passages(self, texts: list[str]) -> list[list[float]]:
        vecs = get_model().encode(texts, normalize_embeddings=True, show_progress_bar=len(texts) > 16)
        return [v.tolist() for v in vecs]

    def encode_query(self, text: str) -> list[float]:
        vec = get_model().encode(QUERY_INSTRUCTION + text, normalize_embeddings=True)
        return vec.tolist()


if __name__ == "__main__":
    e = BGEEmbedder()
    print(f"模型: {e.model_name}  dim={e.dim}")
    # 关键: 段落书写要一致(都带产品名), 否则长度/格式差异会干扰相似度
    passages = [
        "云雀 CRM 定价：企业版基础价格 599 元/用户/月",
        "云雀 CRM 定价：标准版基础价格 299 元/用户/月",
        "今天天气不错",
    ]
    vs = e.encode_passages(passages)
    q = e.encode_query("企业版多少钱？")

    def cos(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))  # 已归一化, 点积即余弦

    print("查询: 企业版多少钱？")
    for text, v in zip(passages, vs):
        print(f"  相似度 {cos(q, v):.4f}  <- {text}")
