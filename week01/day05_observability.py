"""Day 5: 本地可观测性 + Week 1 复盘 (不依赖外部观测平台)

学习目标:
1. 图可视化: create_agent 编译出的节点/边 (model + tools 两个节点)
2. 回调追踪: 用 BaseCallbackHandler 本地打印 每次 LLM 请求/工具调用的耗时
3. Token 记账: 从消息的 usage_metadata 汇总 input/output tokens 与成本
4. 复盘: 手写循环 vs 框架, 每个抽象对应底层哪一步

命令: /help /graph /usage /clear /exit
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

from day01_chat import price_per_token
from day04_langchain import build_agent

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


# ---------------------------------------------------------------------------
# 1. 本地回调追踪器 (替代 LangSmith: 把关键事件打到本地)
# ---------------------------------------------------------------------------

class LocalTracer(BaseCallbackHandler):
    def __init__(self) -> None:
        self.llm_calls = 0
        self.tool_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self._t0 = 0.0

    # --- LLM 事件 ---
    def on_chat_model_start(self, serialized, messages, **kwargs):  # noqa: ANN001
        self._t0 = time.perf_counter()
        self.llm_calls += 1
        n = len(messages[0]) if messages else 0
        print(f"    [LLM 请求 #{self.llm_calls}] 上下文 {n} 条消息")

    def on_llm_end(self, response, **kwargs):  # noqa: ANN001
        dt = (time.perf_counter() - self._t0) * 1000
        usage = self._extract_usage(response)
        if usage:
            self.input_tokens += usage.get("input_tokens", 0)
            self.output_tokens += usage.get("output_tokens", 0)
        print(f"    [LLM 返回 #{self.llm_calls}] 耗时 {dt:.0f}ms tokens={usage}")

    @staticmethod
    def _extract_usage(response) -> dict:
        try:
            msg = response.generations[0][0].message
            if getattr(msg, "usage_metadata", None):
                return msg.usage_metadata
        except Exception:  # noqa: BLE001
            pass
        llm_output = getattr(response, "llm_output", None) or {}
        return llm_output.get("token_usage", {})

    # --- 工具事件 ---
    def on_tool_start(self, serialized, input_str, **kwargs):  # noqa: ANN001
        self.tool_calls += 1
        print(f"    [工具开始 #{self.tool_calls}] {serialized.get('name')} <- {input_str[:80]}")

    def on_tool_end(self, output, **kwargs):  # noqa: ANN001
        print(f"    [工具结束 #{self.tool_calls}] -> {str(output)[:80]}")

    def report(self, model: str) -> str:
        lines = [
            f"  LLM 请求次数: {self.llm_calls}",
            f"  工具调用次数: {self.tool_calls}",
            f"  累计 tokens: in={self.input_tokens:,} out={self.output_tokens:,}",
        ]
        price = price_per_token(model)
        if price:
            cost = self.input_tokens / 1e6 * price[0] + self.output_tokens / 1e6 * price[1]
            lines.append(f"  估算成本: ${cost:.6f}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2. 图可视化
# ---------------------------------------------------------------------------

def print_graph(agent) -> None:
    g = agent.get_graph()
    print("节点:", " | ".join(g.nodes))
    print("边  :")
    for e in g.edges:
        cond = " (条件)" if getattr(e, "conditional", False) else ""
        print(f"  {e.source} -> {e.target}{cond}")
    print("\nMermaid (可贴到 https://mermaid.live 渲染):")
    print(g.draw_mermaid())


# ---------------------------------------------------------------------------
# 3. 从消息汇总 token (不依赖回调, 双保险)
# ---------------------------------------------------------------------------

def sum_usage(messages: list) -> tuple[int, int]:
    inp = out = 0
    for m in messages:
        if isinstance(m, AIMessage) and getattr(m, "usage_metadata", None):
            inp += m.usage_metadata.get("input_tokens", 0)
            out += m.usage_metadata.get("output_tokens", 0)
    return inp, out


def print_new_messages(msgs: list, start: int) -> None:
    for m in msgs[start:]:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                print(f"  [模型决策] {tc['name']}({tc['args']})")
        elif isinstance(m, ToolMessage):
            print(f"  [工具结果] {str(m.content)[:160]}")
        elif isinstance(m, AIMessage) and m.content:
            print(f"AI> {m.content}")


def print_help() -> None:
    print("命令: /graph 查看图结构 | /usage token记账 | /clear | /exit")


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    model_name = os.getenv("OPENAI_MODEL", "deepseek-chat").strip()
    if not api_key or api_key == "sk-your-key-here":
        print("[错误] 请先在 .env 中配置 OPENAI_API_KEY")
        sys.exit(1)

    agent = build_agent(base_url, model_name)
    history: list = []

    print("=" * 60)
    print(" Day 5 · 本地可观测性 + 复盘")
    print(f" 模型: {model_name} | Agent: {type(agent).__name__}")
    print(" 输入 /graph 看底层图结构")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n你> ").strip().lstrip("﻿")
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        if not user_input:
            continue
        if user_input in ("/exit", "/quit", "exit", "quit"):
            print("再见!")
            break
        if user_input == "/help":
            print_help()
            continue
        if user_input == "/graph":
            print_graph(agent)
            continue
        if user_input == "/usage":
            inp, out = sum_usage(history)
            print(f"  [消息汇总] in={inp:,} out={out:,}")
            price = price_per_token(model_name)
            if price:
                print(f"  [估算成本] ${inp/1e6*price[0] + out/1e6*price[1]:.6f}")
            continue
        if user_input == "/clear":
            history = []
            print("[历史已清空]")
            continue

        history.append(HumanMessage(content=user_input))
        start = len(history) - 1
        tracer = LocalTracer()
        print("  --- trace 开始 ---")
        try:
            for chunk in agent.stream(
                {"messages": history},
                config={"callbacks": [tracer]},
                stream_mode="values",
            ):
                msgs = chunk["messages"]
                print_new_messages(msgs, start)
                start = len(msgs)
            history = msgs
        except Exception as exc:  # noqa: BLE001
            if history and isinstance(history[-1], HumanMessage):
                history.pop()
            print(f"[请求失败] {type(exc).__name__}: {exc}")
        print("  --- trace 结束 ---")
        print(tracer.report(model_name))


if __name__ == "__main__":
    main()
