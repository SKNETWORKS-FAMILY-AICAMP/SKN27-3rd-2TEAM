from app.common.default_state import FALLBACK_RESPONSE_STATE
from app.common.labels import CATEGORY_LABELS
from app.llm.openai_llm_client import OpenAiLlmClient
from app.llm.response_state_schema import RESPONSE_STATE_JSON_SCHEMA


RESPONSE_GENERATOR_SYSTEM_PROMPT = """
너는 RIMAS의 Response Generator다.
제공된 ML_OUTPUT, KAG_STATE, RAG_STATE, CURATION_PLAN, SELECTED_RECOMMENDATIONS만 사용한다.
RAG_STATE에 없는 곡, 아티스트, 장르, 추천 이유를 새로 만들지 않는다.
고객 응답에는 selected_path, strategy_code, raw JSON 같은 내부 코드를 노출하지 않는다.
반드시 ResponseState JSON 형식으로만 응답한다.
validation 값은 검증기가 나중에 결정하므로 둘 다 false로 둔다.
"""


class ResponseGenerator:
    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def run(
        self,
        user_input,
        ml_output,
        kag_state,
        rag_state,
        curation_plan,
        selected_recommendations,
    ):
        if not selected_recommendations.get("selected_recommendations"):
            return dict(FALLBACK_RESPONSE_STATE)

        payload = {
            "user_input": user_input,
            "ml_output": ml_output,
            "kag_state": kag_state,
            "rag_state": rag_state,
            "curation_plan": curation_plan,
            "selected_recommendations": self._with_display_labels(
                selected_recommendations
            ),
        }
        return self._client().generate_json(
            system_prompt=RESPONSE_GENERATOR_SYSTEM_PROMPT,
            payload=payload,
            json_schema=RESPONSE_STATE_JSON_SCHEMA,
            schema_name="response_state",
        )

    def _client(self):
        if self._llm_client is None:
            self._llm_client = OpenAiLlmClient()
        return self._llm_client

    def _with_display_labels(self, selected_recommendations):
        enriched = []
        for item in selected_recommendations.get("selected_recommendations", []):
            copied = dict(item)
            copied["label"] = CATEGORY_LABELS.get(
                copied.get("recommendation_category"),
                "추천",
            )
            enriched.append(copied)
        return {
            "status": selected_recommendations.get("status", "success"),
            "selected_recommendations": enriched,
        }
