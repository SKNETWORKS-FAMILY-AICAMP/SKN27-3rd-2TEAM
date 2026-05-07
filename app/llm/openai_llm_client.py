import json

from app.config import settings


class MissingOpenAiApiKeyError(RuntimeError):
    pass


class OpenAiLlmClient:
    def __init__(
        self,
        api_key=None,
        model=None,
        timeout_seconds=None,
        openai_client=None,
    ):
        self._api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        if not self._api_key:
            raise MissingOpenAiApiKeyError("OPENAI_API_KEY is required")

        self._model = model or settings.RIMAS_LLM_MODEL
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.RIMAS_LLM_TIMEOUT_SECONDS
        )
        self._client = openai_client or self._build_client()

    def generate_json(self, system_prompt, payload, json_schema, schema_name):
        response = self._client.responses.create(
            model=self._model,
            instructions=system_prompt,
            input=json.dumps(payload, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": json_schema,
                    "strict": True,
                }
            },
            temperature=0.2,
        )
        return json.loads(response.output_text)

    def _build_client(self):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is required for OpenAI LLM calls") from exc

        return OpenAI(api_key=self._api_key, timeout=self._timeout_seconds)
