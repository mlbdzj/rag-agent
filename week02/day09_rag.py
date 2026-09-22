"""Week2 Day9: 检索 -> 生成全链路 (项目① MVP)

学习目标:
1. 组装 RAG 链: query -> 检索 top-k -> 拼上下文 -> LLM 生成
2. RAG 的 prompt 三原则: 只依据资料 / 标注引用 / 找不到就说不知道
3. 观察"检索质量决定回答质量": 检索错 -> 回答错(幻觉)

用法:
  uv run week02/day09_rag.py "企业版多少钱"
  uv run week02/day09_rag.py            # 交互模式
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from day08_embed_store import search

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

TOP_K = 5

SYSTEM_PROMPT = """你是"云雀 CRM"知识库助手。严格遵守:
1. 只依据 <资料> 中的内容回答, 不得使用资料外的知识或编造。
2. 在结论后用 [编号] 标注来源, 例如"企业版每月 599 元[1]"。
3. 如果 <资料> 中没有答案, 明确回答"资料中未找到相关信息", 不要猜测。
4. 回答简洁, 用中文。"""

USER_TEMPLATE = """<资料>
{context}
</资料>

问题: {question}

请依据资料回答, 并标注引用编号。"""


def format_context(hits: list[dict]) -> str:
    lines = []
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        loc = m["source"] + (f" p.{m['page']}" if m.get("page") else "")
        if m.get("heading"):
            loc += f" · {m['heading']}"
        lines.append(f"[{i}] 来源: {loc} (相似度 {h['similarity']:.3f})\n{h['text']}")
    return "\n\n".join(lines)


def get_client():
    from openai import OpenAI

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    if not api_key or api_key == "sk-your-key-here":
        print("[错误] 请先在 .env 中配置 OPENAI_API_KEY")
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url=base_url), os.getenv("OPENAI_MODEL", "deepseek-chat").strip()


def answer(client, model: str, question: str, hits: list[dict], verbose: bool = True) -> str:
    context = format_context(hits)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(context=context, question=question)},
        ],
        temperature=0,
    )
    reply = resp.choices[0].message.content or ""
    if verbose:
        usage = resp.usage
        print(f"  [tokens] in={usage.prompt_tokens} out={usage.completion_tokens}")
    return reply


def rag_once(client, model: str, question: str, k: int = TOP_K) -> None:
    hits = search(question, k=k)
    print(f"\n[检索到 {len(hits)} 个片段]")
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        loc = m["source"] + (f" p.{m['page']}" if m.get("page") else "") + (f" · {m['heading']}" if m.get("heading") else "")
        print(f"  [{i}] {loc}  (sim={h['similarity']:.3f})")
    print("\nAI>", answer(client, model, question, hits))


def main() -> None:
    client, model = get_client()
    if len(sys.argv) > 1:
        rag_once(client, model, " ".join(sys.argv[1:]))
        return

    print("云雀 CRM 知识库问答 (空行退出)")
    while True:
        try:
            q = input("\n问> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        rag_once(client, model, q)


if __name__ == "__main__":
    main()
