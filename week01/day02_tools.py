"""Day 2: 手写 Tool Calling Agent 循环 (无框架)

学习目标:
1. 掌握 Tool Calling 协议四步:
   定义 tools(JSON Schema) -> 模型返回 tool_calls -> 本地执行 -> 回传 tool_results
2. 理解 Agent 本质: 一个 while 循环, 直到模型不再请求调用工具
3. 实现 3 个工具: get_weather(mock) / calculator / read_file

命令 (对话中可用):
  /help /clear /exit
"""

from __future__ import annotations

import ast
import json
import math
import operator
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_SYSTEM = (
    "你是一个会使用工具的助手。需要外部信息或精确计算时, "
    "必须调用工具, 不要凭空编造。工具结果返回后再回答用户。"
)

# ---------------------------------------------------------------------------
# 工具实现
# ---------------------------------------------------------------------------

WEATHER_DB = {
    "beijing": {"condition": "晴", "temp_c": 26, "humidity": 35},
    "shanghai": {"condition": "多云", "temp_c": 28, "humidity": 70},
    "shenzhen": {"condition": "雷阵雨", "temp_c": 30, "humidity": 85},
}


def get_weather(city: str) -> dict:
    """查询城市天气 (mock 数据)。"""
    key = city.strip().lower()
    if key not in WEATHER_DB:
        return {"error": f"未知城市: {city}", "available": list(WEATHER_DB)}
    data = dict(WEATHER_DB[key])
    data["city"] = city
    return data


def calculator(expression: str) -> dict:
    """安全计算数学表达式, 仅支持 + - * / ** % 与常用数学函数。"""
    allowed_names = {
        "abs": abs, "round": round,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "pi": math.pi, "e": math.e,
    }
    binary_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }
    unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def _eval(node: ast.AST):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id in allowed_names:
            return allowed_names[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
            return binary_ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
            return unary_ops[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = allowed_names.get(node.func.id)
            if callable(fn) and not node.keywords:
                return fn(*[_eval(a) for a in node.args])
        raise ValueError(f"不支持的表达式元素: {ast.dump(node)}")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval(tree)
        return {"expression": expression, "result": result}
    except Exception as exc:  # noqa: BLE001
        return {"expression": expression, "error": str(exc)}


def read_file(path: str, max_chars: int = 2000) -> dict:
    """读取工作区内文本文件 (安全限制在当前目录)。"""
    root = Path.cwd().resolve()
    target = (root / path).resolve()
    if not str(target).startswith(str(root)):
        return {"error": "禁止访问工作区外的文件"}
    if not target.is_file():
        return {"error": f"文件不存在: {path}"}
    text = target.read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > max_chars
    return {
        "path": path,
        "size": len(text),
        "content": text[:max_chars],
        "truncated": truncated,
    }


# ---------------------------------------------------------------------------
# 工具注册表: name -> (实现函数, JSON Schema, 描述)
# ---------------------------------------------------------------------------

TOOLS: dict[str, tuple] = {
    "get_weather": (
        get_weather,
        {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名, 如 beijing"}
            },
            "required": ["city"],
        },
        "查询指定城市的当前天气 (mock 数据, 支持 beijing/shanghai/shenzhen)",
    ),
    "calculator": (
        calculator,
        {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式, 如 2**10 + sqrt(16)"}
            },
            "required": ["expression"],
        },
        "精确计算数学表达式, 涉及数字运算时必须使用",
    ),
    "read_file": (
        read_file,
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "相对当前工作区的文件路径"},
                "max_chars": {"type": "integer", "description": "最多返回字符数, 默认 2000"},
            },
            "required": ["path"],
        },
        "读取工作区内文本文件的内容",
    ),
}


def openai_tools_payload() -> list[dict]:
    """转换为 OpenAI chat.completions 的 tools 参数格式。"""
    return [
        {"type": "function", "function": {"name": name, "description": desc, "parameters": schema}}
        for name, (_, schema, desc) in TOOLS.items()
    ]


def dispatch_tool(name: str, arguments: dict) -> str:
    """执行工具并返回 JSON 字符串 (失败也返回 JSON, 交给模型处理)。"""
    if name not in TOOLS:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
    fn = TOOLS[name][0]
    try:
        result = fn(**arguments)
    except TypeError as exc:
        result = {"error": f"参数错误: {exc}"}
    except Exception as exc:  # noqa: BLE001
        result = {"error": f"{type(exc).__name__}: {exc}"}
    return json.dumps(result, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Agent 循环 (核心: 就是一个 while)
# ---------------------------------------------------------------------------

def run_agent(client, model: str, messages: list[dict], max_steps: int = 8) -> None:
    """手写 Agent 循环: 只要模型还要求调工具, 就执行并回传, 直到它给出最终回答。"""
    tools = openai_tools_payload()
    step = 0

    while step < max_steps:
        step += 1
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=0.2,
        )
        choice = response.choices[0]
        msg = choice.message

        # 1) 模型没有请求工具 -> 最终回答, 循环结束
        if not msg.tool_calls:
            print(f"AI> {msg.content}")
            messages.append({"role": "assistant", "content": msg.content or ""})
            return

        # 2) 模型请求了工具 -> 先把 assistant 消息(含 tool_calls)存入历史
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        # 3) 逐个执行工具, 每个 tool_call 必须对应一条 tool 消息回传
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"  [tool #{step}] {name}({json.dumps(args, ensure_ascii=False)})")
            result_str = dispatch_tool(name, args)
            print(f"             -> {result_str[:200]}")
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result_str}
            )

        # 4) 回到 while 顶部, 把工具结果喂回模型, 继续决策
    print("[警告] 达到 max_steps, 强制停止 (防死循环)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_help() -> None:
    print("可用命令: /help /clear /exit")
    print("试试这些问题:")
    print('  - 北京天气怎么样? 深圳呢? 哪个更热?')
    print('  - 2的20次方是多少? 再除以 999 要保留几位小数?')
    print("  - 读一下 pyproject.toml 告诉我项目名")


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    model = os.getenv("OPENAI_MODEL", "deepseek-chat").strip()
    if not api_key or api_key == "sk-your-key-here":
        print("[错误] 请先在 .env 中配置 OPENAI_API_KEY")
        sys.exit(1)

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    messages: list[dict] = [{"role": "system", "content": DEFAULT_SYSTEM}]

    print("=" * 60)
    print(" Day 2 · 手写 Tool Calling Agent 循环 (无框架)")
    print(f" 模型: {model} | 工具: {', '.join(TOOLS)}")
    print(" 输入 /help 查看示例, /exit 退出")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n你> ").strip()
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
            messages = [{"role": "system", "content": DEFAULT_SYSTEM}]
            print("[已清空对话历史]")
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            run_agent(client, model, messages)
        except Exception as exc:  # noqa: BLE001
            if messages[-1]["role"] == "user":
                messages.pop()
            print(f"[请求失败] {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
