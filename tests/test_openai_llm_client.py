import json
from types import SimpleNamespace

import pytest

from app.llm.openai_llm_client import MissingOpenAiApiKeyError, OpenAiLlmClient


class FakeResponses:
    def __init__(self, output_text):
        self.output_text = output_text
        self.received_kwargs = None

    def create(self, **kwargs):
        self.received_kwargs = kwargs
        return SimpleNamespace(output_text=self.output_text)


class FakeOpenAI:
    def __init__(self, output_text):
        self.responses = FakeResponses(output_text)


def test_openai_llm_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(MissingOpenAiApiKeyError):
        OpenAiLlmClient(api_key="")


def test_openai_llm_client_requests_strict_json_schema():
    fake_openai = FakeOpenAI('{"status": "success"}')
    client = OpenAiLlmClient(
        api_key="test-key",
        model="gpt-test",
        openai_client=fake_openai,
    )

    result = client.generate_json(
        system_prompt="Return JSON only.",
        payload={"user_input": "추천해줘"},
        json_schema={
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
            "additionalProperties": False,
        },
        schema_name="intent_result",
    )

    request = fake_openai.responses.received_kwargs
    assert result == {"status": "success"}
    assert request["model"] == "gpt-test"
    assert json.loads(request["input"]) == {"user_input": "추천해줘"}
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["name"] == "intent_result"
    assert request["text"]["format"]["strict"] is True
