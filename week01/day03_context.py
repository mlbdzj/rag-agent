"""Day 3: 提示词 / 上下文工程 + 结构化输出

学习目标:
1. 提示词模板化: 变量注入 vs 字符串拼接, few-shot 的利弊
2. 上下文工程四要素: 预算分配 / 摘要压缩 / 结构化注入 / 缓存意识
3. 结构化输出: JSON schema 约束 + 校验 + 失败重试

命令:
  /help /clear /exit
  /mode chat      切换到自由聊天模式 (体验 prompt 变量)
  /mode extract   切换到信息抽取模式 (结构化输出)
  /mode review    切换到代码评审模式 (few-shot + 结构化)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# 1. 提示词模板 (变量注入, 不用 f-string 裸拼)
# ---------------------------------------------------------------------------

# 设计原则: system 定角色与硬约束, user 模板放可变数据
PROMPTS = {
    "chat": {
        "system": (
            "你是{persona}。回答遵守:\n"
            "- {style}\n"
            "- 不确定就说不知道, 不编造\n"
            "- 总长不超过 {max_words} 字"
        ),
        "user": "{question}",
        "vars": {"persona": "资深 Python 工程师", "style": "先给结论, 再给理由", "max_words": "200"},
    },
    "extract": {
        "system": (
            "你是信息抽取器。从用户文本中抽取实体, "
            "只输出 JSON, 不要任何解释文字。\n"
            "JSON 必须严格符合 schema:\n"
            '{"people": string[], "orgs": string[], "dates": string[], "amounts": string[]}'
        ),
        "user": "抽取以下文本:\n<<<\n{text}\n>>>",
        "vars": {},
    },
    "review": {
        "system": (
            "你是资深 code reviewer。按 JSON 输出评审结果。\n"
            "Schema: {\"score\": 1-5整数, \"issues\": [{\"line\": 整数, \"severity\": \"high|med|low\", \"msg\": string}], \"summary\": string}\n"
            "评分标准示例:\n"
            "输入: \"def add(a,b): return a+b\"  -> 输出 {{\"score\": 3, \"issues\": [{{\"line\": 1, \"severity\": \"low\", \"msg\": \"缺类型注解与 docstring\"}}], \"summary\": \"能用但缺规范\"}}\n"
            "只输出 JSON。"
        ),
        "user": "评审这段代码:\n<<<\n{code}\n>>>",
        "vars": {},
    },
}


def render(template: str, variables: dict) -> str:
    """安全渲染: 缺变量时报错而不是静默留下 {var}。"""
    try:
        return template.format(**variables)
    except KeyError as exc:
        raise ValueError(f"模板缺少变量: {exc} (可用: {list(variables)})") from exc


# ---------------------------------------------------------------------------
# 2. 结构化输出: 校验 + 修复重试
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {"people", "orgs", "dates", "amounts"}


def extract_json(text: str) -> dict:
    """从模型输出中抠出 JSON (容忍 ```json 代码块包裹)。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("输出中没有 JSON 对象")
    return json.loads(text[start : end + 1])


def validate_extract(data: dict) -> list[str]:
    """返回错误列表, 空 = 通过。"""
    errors = []
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        errors.append(f"缺少字段: {missing}")
    for key in REQUIRED_KEYS & data.keys():
        if not isinstance(data[key], list):
            errors.append(f"字段 {key} 应为数组, 实际 {type(data[key]).__name__}")
        elif not all(isinstance(x, str) for x in data[key]):
            errors.append(f"字段 {key} 数组元素应全为 string")
    return errors


def validate_review(data: dict) -> list[str]:
    errors = []
    if not isinstance(data.get("score"), int) or not 1 <= data["score"] <= 5:
        errors.append("score 应为 1-5 整数")
    issues = data.get("issues")
    if not isinstance(issues, list):
        errors.append("issues 应为数组")
    else:
        for i, item in enumerate(issues):
            if not isinstance(item, dict) or {"line", "severity", "msg"} - item.keys():
                errors.append(f"issues[{i}] 缺字段")
                break
            if item.get("severity") not in ("high", "med", "low"):
                errors.append(f"issues[{i}].severity 非法")
                break
    if not isinstance(data.get("summary"), str):
        errors.append("summary 应为 string")
    return errors


VALIDATORS = {"extract": (extract_json, validate_extract), "review": (extract_json, validate_review)}


def chat_with_schema(client, model: str, messages: list[dict], mode: str, max_retries: int = 2) -> str:
    """请求 → 抽 JSON → 校验; 失败则把错误回喂给模型重试。"""
    parse, validate = VALIDATORS[mode]
    history = list(messages)
    last_err = ""
    for attempt in range(max_retries + 1):
        resp = client.chat.completions.create(model=model, messages=history, temperature=0)
        raw = resp.choices[0].message.content or ""
        try:
            data = parse(raw)
            errors = validate(data)
        except (ValueError, json.JSONDecodeError) as exc:
            errors = [f"JSON 解析失败: {exc}"]
            data = None
        if not errors:
            if attempt:
                print(f"  [结构化输出] 第 {attempt + 1} 次尝试通过校验")
            return json.dumps(data, ensure_ascii=False, indent=2)
        last_err = "; ".join(errors)
        print(f"  [校验失败 第 {attempt + 1}/{max_retries + 1}] {last_err} -> 回喂重试")
        history = history + [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": f"你的输出校验未通过: {last_err}。请修正后只输出合法 JSON。",
            },
        ]
    return json.dumps({"error": "重试耗尽", "last_error": last_err}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 3. 上下文窗口管理 (演示: 历史截断 + 预算意识)
# ---------------------------------------------------------------------------

def trim_history(messages: list[dict], keep_last: int = 6) -> list[dict]:
    """保 system + 最近 keep_last 条; 演示最朴素的上下文压缩。"""
    if len(messages) <= keep_last + 1:
        return messages
    return [messages[0], *messages[-keep_last:]]


def approx_tokens(text: str) -> int:
    """粗估: 中文 ~1.6 字/token, 英文 ~4 字符/token (仅演示, 生产用 tiktoken)。"""
    cn = sum(1 for c in text if "一" <= c <= "鿿")
    return int(cn / 1.6 + (len(text) - cn) / 4)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_help() -> None:
    print(
        """可用命令:
  /mode chat|extract|review   切换模式
  /clear /exit /help
体验建议:
  chat 模式:   "什么是描述符协议?"
  extract:     "腾讯2024年营收6602亿元, 张志东是联合创始人, 公司1998年成立。"
  review:      "def add(a,b): return a+b\""""
    )


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

    mode = "chat"
    messages: list[dict] = []

    def rebuild_messages() -> None:
        """模式切换后按模板重建 messages (变量在此注入)。"""
        nonlocal messages
        prompt = PROMPTS[mode]
        system = render(prompt["system"], prompt["vars"])
        messages = [{"role": "system", "content": system}]

    rebuild_messages()

    print("=" * 60)
    print(" Day 3 · 提示词/上下文工程 + 结构化输出")
    print(f" 模型: {model} | 模式: {mode}")
    print(" /help 查看命令, /mode 切换模式, /exit 退出")
    print("=" * 60)

    while True:
        try:
            user_input = input(f"\n[{mode}] 你> ").strip()
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
            rebuild_messages()
            print("[历史已清空]")
            continue
        if user_input.startswith("/mode "):
            new_mode = user_input[6:].strip()
            if new_mode not in PROMPTS:
                print(f"[无效模式] 可选: {list(PROMPTS)}")
                continue
            mode = new_mode
            rebuild_messages()
            print(f"[已切换到 {mode} 模式]")
            continue

        # 上下文预算: 超过阈值截断历史 (演示)
        trimmed = trim_history(messages)
        if len(trimmed) < len(messages):
            print(f"  [上下文] 历史 {len(messages)} 条 -> 截断保留 {len(trimmed)} 条")
            messages = trimmed

        user_msg = render(PROMPTS[mode]["user"], {**PROMPTS[mode]["vars"], "question": user_input, "text": user_input, "code": user_input})
        messages.append({"role": "user", "content": user_msg})

        est = approx_tokens("\n".join(m["content"] for m in messages))
        try:
            if mode in VALIDATORS:
                reply = chat_with_schema(client, model, messages, mode)
            else:
                resp = client.chat.completions.create(model=model, messages=messages, temperature=0.7)
                reply = resp.choices[0].message.content or ""
                print(f"AI> {reply}")
            if mode in VALIDATORS:
                print(f"AI> {reply}")
            messages.append({"role": "assistant", "content": reply})
            print(f"  [本次上下文粗估 ~{est} tokens]")
        except Exception as exc:  # noqa: BLE001
            if messages[-1]["role"] == "user":
                messages.pop()
            print(f"[请求失败] {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
