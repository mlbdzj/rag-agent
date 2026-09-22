"""Day 4: 用 LangChain 重构 Day 2 的手写 Agent

对比目标 (学完要能回答):
  手写循环 (day02_tools.py)  ~100 行  vs  LangChain create_agent  ~10 行
  抽象帮你省了什么? 又隐藏了什么?

学习目标:
1. @tool 装饰器: 函数签名+docstring 自动变成工具的 JSON Schema
2. 模型抽象: ChatOpenAI 同一份代码可换 OpenAI/DeepSeek/Qwen (只改 base_url)
3. create_agent: v1 的预置 Agent, 底层其实编译成了一个 LangGraph 图
4. agent.stream: 逐步观察 模型决策 / 工具执行 的状态流转

命令: /help /clear /exit /history
"""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

# 复用 Day 2 的纯函数实现 (演示: 已有函数可包装成工具)
from day02_tools import calculator as _calculator
from day02_tools import get_weather as _get_weather
from day02_tools import read_file as _read_file

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

DEFAULT_SYSTEM = (
    "你是一个会使用工具的助手。需要外部信息或精确计算时, "
    "必须调用工具, 不要凭空编造。工具结果返回后再回答用户。"
)


# ---------------------------------------------------------------------------
# 1. @tool 装饰器: 类型注解 + docstring → 自动生成 JSON Schema
#    对比 Day 2: 那里要手写 {"type":"object","properties":...,"required":...}
# ---------------------------------------------------------------------------

@tool
def get_weather(city: str) -> dict:
    """查询指定城市的当前天气 (mock 数据, 支持 beijing/shanghai/shenzhen)。"""
    return _get_weather(city)


@tool
def calculator(expression: str) -> dict:
    """精确计算数学表达式, 涉及数字运算时必须使用。支持 + - * / ** % 与 sqrt 等。"""
    return _calculator(expression)


@tool
def read_file(path: str, max_chars: int = 2000) -> dict:
    """读取工作区内文本文件的内容。"""
    return _read_file(path, max_chars)


TOOLS = [get_weather, calculator, read_file]


# ---------------------------------------------------------------------------
# 2. 模型抽象: 同一个 ChatOpenAI 类, 换 base_url 即可换服务商
# ---------------------------------------------------------------------------

def build_model(base_url: str | None, model_name: str):
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=base_url,
        temperature=0.2,
    )


# ---------------------------------------------------------------------------
# 3. create_agent: 一行替代手写 while 循环
# ---------------------------------------------------------------------------

def build_agent(base_url: str | None, model_name: str):
    from langchain.agents import create_agent

    graph = create_agent(
        build_model(base_url, model_name),
        tools=TOOLS,
        system_prompt=DEFAULT_SYSTEM,
    )
    return graph


# ---------------------------------------------------------------------------
# 消息打印 (把 LangChain 消息对象翻译成人可读的步骤日志)
# ---------------------------------------------------------------------------

def print_new_messages(msgs: list, start: int) -> None:
    """打印 msgs[start:] 中的新消息, 对应 Day 2 的 [tool #N] 日志。"""
    for m in msgs[start:]:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                print(f"  [模型决策] 调用 {tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})")
        elif isinstance(m, ToolMessage):
            content = str(m.content)
            print(f"  [工具结果] {content[:200]}")
        elif isinstance(m, AIMessage) and m.content:
            print(f"AI> {m.content}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_help() -> None:
    print(
        """可用命令: /help /clear /history /exit
体验建议 (和 Day 2 完全相同的输入, 对比日志):
  - 北京天气怎么样? 深圳呢? 哪个更热?
  - 北京多少度? 换算成华氏度 (观察串行)
  - 2的20次方是多少? 再读一下 pyproject.toml"""
    )


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
    print(" Day 4 · LangChain create_agent (对比 Day 2 手写循环)")
    print(f" 模型: {model_name} | 工具: {', '.join(t.name for t in TOOLS)}")
    print(f" Agent 类型: {type(agent).__name__}  <- 底层就是一张 LangGraph 图")
    print(" 输入 /help 查看示例, /exit 退出")
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
        if user_input == "/clear":
            history = []
            print("[历史已清空]")
            continue
        if user_input == "/history":
            print(f"[当前历史 {len(history)} 条消息]")
            for m in history:
                print(f"  {type(m).__name__}: {str(m.content)[:60]}")
            continue

        history.append(HumanMessage(content=user_input))
        start = len(history) - 1
        try:
            for chunk in agent.stream({"messages": history}, stream_mode="values"):
                msgs = chunk["messages"]
                print_new_messages(msgs, start)
                start = len(msgs)
            history = msgs
        except Exception as exc:  # noqa: BLE001
            if history and isinstance(history[-1], HumanMessage):
                history.pop()
            print(f"[请求失败] {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
