from app.agents.base_agent import BaseAgent
from app.common.constants import ALLOWED_GENRES, ALLOWED_MOODS, ALLOWED_SITUATIONS
from app.schemas.intent_state_schema import IntentStateSchema
from app.schemas.kag_input_schema import KagInputSchema


class InputPlannerAgent(BaseAgent):
    """사용자 입력을 INTENT_STATE와 KAG_INPUT_JSON으로 정규화한다."""

    def run(
        self,
        user_id: str,
        session_id: str,
        request_id: str,
        user_input: str,
        session_context: dict,
    ) -> dict:
        normalized_query = user_input.strip() if user_input else "사용자 취향 기반 음악 추천"
        intent_type = self._decide_intent_type(normalized_query)
        detected_moods = self._detect_candidates(
            normalized_query, session_context, "recent_moods", ALLOWED_MOODS
        )
        detected_genres = self._detect_candidates(
            normalized_query, session_context, "recent_genres", ALLOWED_GENRES
        )
        detected_situations = self._detect_situations(normalized_query)

        intent_state = IntentStateSchema(
            intent_type=intent_type,
            confidence=0.82,
            normalized_query=normalized_query,
            detected_moods=detected_moods,
            detected_genres=detected_genres,
            detected_situations=detected_situations,
            requires_kag=intent_type != "general_chat",
            requires_rag=intent_type != "general_chat",
        )
        kag_input = KagInputSchema(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            intent_type=intent_type,
            query_context={
                "normalized_query": normalized_query,
                "mood_candidates": detected_moods,
                "genre_candidates": detected_genres,
                "situation_candidates": detected_situations,
            },
            constraints={
                "allow_discovery": True,
                "allow_new_release": True,
                "max_candidates": 10,
            },
        )
        return {
            "intent_state": intent_state.model_dump(),
            "kag_input_json": kag_input.model_dump(),
        }

    @staticmethod
    def _decide_intent_type(text: str) -> str:
        if "최신" in text or "신곡" in text or "새로 나온" in text:
            return "new_release_recommendation"
        if "이유" in text or "왜" in text:
            return "recommendation_reason"
        if "정보" in text or "알려" in text:
            return "music_information"
        if "새로운" in text or "발견" in text:
            return "discovery_recommendation"
        if "추천" in text or text:
            return "personalized_recommendation"
        return "general_chat"

    @staticmethod
    def _detect_candidates(text: str, session_context: dict, context_key: str, allowed: set[str]) -> list[str]:
        candidates = [value for value in session_context.get(context_key, []) if value in allowed]
        keyword_map = {
            "calm": ["차분", "잔잔"],
            "night": ["밤", "새벽"],
            "indie": ["인디"],
            "dream_pop": ["드림팝"],
            "rnb": ["알앤비", "rnb"],
        }
        lowered = text.lower()
        for candidate, keywords in keyword_map.items():
            if candidate in allowed and any(keyword in lowered for keyword in keywords):
                candidates.append(candidate)
        return list(dict.fromkeys(candidates))

    @staticmethod
    def _detect_situations(text: str) -> list[str]:
        if "밤" in text or "새벽" in text:
            return ["late_night"] if "late_night" in ALLOWED_SITUATIONS else []
        return []
