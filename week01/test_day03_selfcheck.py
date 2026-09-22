"""Day 3 自检: 重试耗尽路径 (mock 模型, 不调 API)。"""
import json
import sys

sys.path.insert(0, "week01")
from day03_context import chat_with_schema, extract_json, validate_extract


class FakeMsg:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMsg(content)


class FakeResp:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, outputs):
        self._outputs = list(outputs)
        self.calls = 0

    def create(self, **kwargs):
        out = self._outputs[min(self.calls, len(self._outputs) - 1)]
        self.calls += 1
        return FakeResp(out)


class FakeClient:
    def __init__(self, outputs):
        self.chat = type("C", (), {})()
        self.chat.completions = FakeCompletions(outputs)


def test_retry_exhausted():
    client = FakeClient(["完全不是JSON", '{"people": 123}', '{"wrong": true}'])
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    result = json.loads(chat_with_schema(client, "m", msgs, "extract", max_retries=2))
    assert result.get("error") == "重试耗尽", result
    assert "last_error" in result
    assert client.chat.completions.calls == 3
    print("PASS 重试耗尽兜底, 调用3次(1+2重试):", result)


def test_retry_then_success():
    client = FakeClient(["bad json", '{"people": [], "orgs": [], "dates": [], "amounts": []}'])
    msgs = [{"role": "system", "content": "s"}]
    result = json.loads(chat_with_schema(client, "m", msgs, "extract", max_retries=2))
    assert "error" not in result and set(result) == {"people", "orgs", "dates", "amounts"}
    assert client.chat.completions.calls == 2
    print("PASS 第2次修复成功:", result)


def test_validate_rejects():
    data = extract_json('{"people": 123}')
    errs = validate_extract(data)
    assert any("缺少字段" in e or "应为数组" in e for e in errs)
    print("PASS 校验拒绝错误类型:", errs)


if __name__ == "__main__":
    test_validate_rejects()
    test_retry_then_success()
    test_retry_exhausted()
    print("ALL PASS")
