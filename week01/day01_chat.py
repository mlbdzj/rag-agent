"""Day 1：多轮对话 CLI —— 流式输出 + Token 用量统计

学习目标:
1. 掌握 OpenAI Messages 协议 (system / user / assistant 多轮)
2. 掌握流式输出 (streaming) 的 chunk 处理
3. 理解 token 计费: 每轮打印 input/output token 与累计成本

命令:
  /help   查看帮助
  /clear  清空对话历史
  /system 查看/设置 system prompt
  /usage  查看累计 token 与成本
  /exit   退出 (Ctrl+C 亦可)
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

# Windows 控制台 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_SYSTEM = "你是一个简洁、准确的技术助手。用中文回答。"

# 常见模型的每 1M token 单价 (USD), 仅作估算参考
PRICE_TABLE = {
    # OpenAI
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    # DeepSeek (缓存未命中价)
    "deepseek-chat": (0.27, 1.10),
    "deepseek-reasoner": (0.55, 2.19),
    # Qwen
    "qwen-plus": (0.40, 1.20),
    "qwen-turbo": (0.05, 0.20),
}


def price_per_token(model: str) -> tuple[float, float] | None:
    """返回 (input单价, output单价) 每 token USD; 未知模型返回 None。"""
    for key, price in PRICE_TABLE.items():
        if key in model:
            return price
    return None


def load_config() -> tuple[str, str, str]:
    """从环境/.env 加载 (api_key, base_url, model)。"""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    if not api_key or api_key == "sk-your-key-here":
        print("[错误] 未配置 OPENAI_API_KEY。请:")
        print("  1. 复制 .env.example 为 .env")
        print("  2. 填入你的 API Key")
        sys.exit(1)
    return api_key, base_url, model


class TokenLedger:
    """累计 token 与成本的记账本。"""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.turns = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.turns += 1

    def summary(self, model: str) -> str:
        lines = [
            f"轮次: {self.turns}",
            f"累计 input tokens:  {self.input_tokens:,}",
            f"累计 output tokens: {self.output_tokens:,}",
            f"累计 tokens:        {self.input_tokens + self.output_tokens:,}",
        ]
        price = price_per_token(model)
        if price:
            cost = self.input_tokens / 1e6 * price[0] + self.output_tokens / 1e6 * price[1]
            lines.append(f"估算成本: ${cost:.6f}  ({model})")
        else:
            lines.append(f"估算成本: 未知模型 {model}, 未收录单价")
        return "\n".join(lines)


def stream_once(client, model: str, messages: list[dict]) -> tuple[str, int, int]:
    """发起一次流式请求, 返回 (完整回复, input_tokens, output_tokens)。"""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
        temperature=0.7,
    )

    parts: list[str] = []
    input_tokens = output_tokens = 0

    print("AI> ", end="", flush=True)
    for chunk in response:
        # usage 通常在最后一个 chunk (choices 为空)
        if getattr(chunk, "usage", None) is not None:
            input_tokens = chunk.usage.prompt_tokens or 0
            output_tokens = chunk.usage.completion_tokens or 0
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None)
        if content:
            parts.append(content)
            print(content, end="", flush=True)
    print()

    return "".join(parts), input_tokens, output_tokens


def print_help() -> None:
    print(
        """可用命令:
  /help   显示本帮助
  /clear  清空对话历史 (保留 system)
  /system 查看当前 system prompt; 或 /system 新的指令 来修改
  /usage  查看累计 token 与估算成本
  /exit   退出"""
    )


def main() -> None:
    api_key, base_url, model = load_config()

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    system_prompt = DEFAULT_SYSTEM
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    ledger = TokenLedger()

    print("=" * 60)
    print(" Day 1 · 多轮对话 CLI (流式 + Token 统计)")
    print(f" 模型: {model}" + (f" @ {base_url}" if base_url else " @ OpenAI"))
    print(" 输入 /help 查看命令, /exit 退出")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue

        # ----- 命令处理 -----
        if user_input in ("/exit", "/quit", "exit", "quit"):
            print("再见!")
            break
        if user_input == "/help":
            print_help()
            continue
        if user_input == "/clear":
            messages = [{"role": "system", "content": system_prompt}]
            print("[已清空对话历史]")
            continue
        if user_input == "/usage":
            print(ledger.summary(model))
            continue
        if user_input == "/system":
            print(f"[当前 system] {system_prompt}")
            continue
        if user_input.startswith("/system "):
            system_prompt = user_input[len("/system ") :].strip()
            messages[0]["content"] = system_prompt
            print(f"[system 已更新] {system_prompt}")
            continue

        # ----- 正常对话 -----
        messages.append({"role": "user", "content": user_input})
        try:
            reply, in_tok, out_tok = stream_once(client, model, messages)
        except Exception as exc:  # noqa: BLE001 - 学习脚本, 打印即可
            messages.pop()  # 失败的 user 消息回滚
            print(f"[请求失败] {type(exc).__name__}: {exc}")
            continue

        messages.append({"role": "assistant", "content": reply})
        ledger.add(in_tok, out_tok)
        print(f"[本轮 tokens: in={in_tok} out={out_tok} | 累计: in={ledger.input_tokens} out={ledger.output_tokens}]")


if __name__ == "__main__":
    main()
