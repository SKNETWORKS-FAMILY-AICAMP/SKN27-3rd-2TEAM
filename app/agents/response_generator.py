import logging

from app.agents.base_agent import BaseAgent
from app.agents.recommendation_agent import build_display_reason
from app.common.default_state import FALLBACK_RESPONSE_STATE
from app.common.labels import CATEGORY_LABELS
from app.config import settings
from app.llm.openai_llm_client import OpenAiLlmClient
from app.llm.response_state_schema import RESPONSE_STATE_JSON_SCHEMA
from app.validators.display_reason_validator import DisplayReasonValidator

logger = logging.getLogger("rimas.agent.response_generator")

_SYSTEM_PROMPT = """
너는 RIMAS의 DJ 큐레이터 Response Generator다.
제공된 SESSION_CONTEXT, KAG_STATE, RAG_STATE, SELECTED_RECOMMENDATIONS만 사용한다.
RAG_STATE에 없는 곡, 아티스트, 장르, 추천 이유를 절대 새로 만들지 않는다.
고객 응답에는 selected_path, strategy_code, raw JSON 같은 내부 코드를 노출하지 않는다.
반드시 ResponseState JSON 형식으로만 응답한다.
검증 결과나 provenance 같은 내부 검증 필드는 응답 JSON에 포함하지 않는다.
""".strip()


class ResponseGenerator(BaseAgent):
    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def run(
        self,
        user_input: str,
        session_context: dict,
        kag_state: dict,
        rag_state: dict,
        intent_result: dict,
        selected_recommendations: dict,
    ) -> dict:
        if not selected_recommendations.get("selected_recommendations"):
            return dict(FALLBACK_RESPONSE_STATE)

        payload = {
            "user_input": user_input,
            "session_context": session_context,
            "intent_type": intent_result.get("intent_type"),
            "kag_state": kag_state,
            "rag_state": rag_state,
            "selected_recommendations": self._with_labels(selected_recommendations),
        }
        if self._llm_client is None and not settings.OPENAI_API_KEY:
            return self._build_local_response(payload["selected_recommendations"])

        try:
            return self._client().generate_json(
                system_prompt=_SYSTEM_PROMPT,
                payload=payload,
                json_schema=RESPONSE_STATE_JSON_SCHEMA,
                schema_name="response_state",
            )
        except Exception as exc:
            logger.error("llm_call_failed", extra={"error": str(exc)}, exc_info=True)
            raise

    def _client(self) -> OpenAiLlmClient:
        if self._llm_client is None:
            self._llm_client = OpenAiLlmClient()
        return self._llm_client

    @staticmethod
    def _with_labels(selected: dict) -> dict:
        enriched = []
        for item in selected.get("selected_recommendations", []):
            enriched.append({
                **item,
                "label": CATEGORY_LABELS.get(item.get("recommendation_category"), "추천"),
            })
        return {**selected, "selected_recommendations": enriched}

    @staticmethod
    def _build_local_response(selected: dict) -> dict:
        recommendations = selected.get("selected_recommendations", [])
        reason_validator = DisplayReasonValidator()
        display_recommendations = [
            {
                "content_id": item.get("content_id", ""),
                "title": item.get("title", ""),
                "artist": item.get("artist", ""),
                "label": item.get("label", ""),
                "display_reason": (
                    item.get("display_reason", "")
                    if reason_validator.validate(item.get("display_reason", ""), item).get("passed")
                    else build_display_reason(item)
                ),
            }
            for item in recommendations
        ]
        title = display_recommendations[0]["title"] if display_recommendations else "추천 곡"
        return {
            "status": "success",
            "response_type": "curator_recommendation",
            "chatbot_response": f"임시 응답입니다. 현재 근거 기준으로 {title}을 추천합니다.",
            "display_recommendations": display_recommendations,
            "used_content_ids": [
                item["content_id"]
                for item in display_recommendations
                if item.get("content_id")
            ],
        }
