import logging
import re

from app.agents.base_agent import BaseAgent
from app.common.constants import ALLOWED_GENRES, ALLOWED_INTENT_TYPES, ALLOWED_MOODS, ALLOWED_SITUATIONS
from app.policies.recommendation_policy import MAX_SELECTED_RECOMMENDATIONS
from app.schemas.intent_state_schema import IntentStateSchema
from app.schemas.kag_input_schema import KagInputSchema

logger = logging.getLogger("rimas.agent.input_planner")


class InputPlannerAgent(BaseAgent):
    """Normalize user input into INTENT_STATE and KAG_INPUT_JSON."""

    def __init__(self, llm_client=None):
        self._llm = llm_client

    def run(
        self,
        user_id: str,
        session_id: str,
        request_id: str,
        user_input: str,
        session_context: dict,
    ) -> dict:
        parsed = self._parse_with_llm(user_input, session_context) if self._llm else None
        if parsed is None:
            parsed = self._parse_with_rules(user_input, session_context)

        intent_type = parsed["intent_type"]
        intent_state = IntentStateSchema(
            intent_type=intent_type,
            confidence=parsed["confidence"],
            normalized_query=parsed["normalized_query"],
            detected_moods=parsed["detected_moods"],
            detected_genres=parsed["detected_genres"],
            detected_situations=parsed["detected_situations"],
            requested_count=parsed.get("requested_count"),
            disliked_artists=parsed.get("disliked_artists", []),
            disliked_tracks=parsed.get("disliked_tracks", []),
            requires_kag=intent_type != "general_chat",
            requires_rag=intent_type != "general_chat",
        )
        excluded_artists = self._merge_unique(
            parsed.get("disliked_artists", []),
            session_context.get("disliked_artists", []),
        )
        excluded_tracks = self._merge_unique(
            parsed.get("disliked_tracks", []),
            session_context.get("disliked_tracks", []),
        )
        kag_input = KagInputSchema(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            intent_type=intent_type,
            query_context={
                "normalized_query": parsed["normalized_query"],
                "mood_candidates": parsed["detected_moods"],
                "genre_candidates": parsed["detected_genres"],
                "situation_candidates": parsed["detected_situations"],
            },
            constraints={
                "allow_discovery": True,
                "allow_new_release": True,
                "max_candidates": parsed.get("requested_count") or 10,
                "excluded_artists": excluded_artists,
                "excluded_tracks": excluded_tracks,
            },
        )
        return {
            "intent_state": intent_state.model_dump(),
            "kag_input_json": kag_input.model_dump(),
        }

    def _parse_with_llm(self, user_input: str, session_context: dict) -> dict | None:
        from app.prompts.input_planner_prompt import OUTPUT_JSON_SCHEMA, SYSTEM_PROMPT
        try:
            payload = {
                "user_input": user_input or "",
                "recent_genres": session_context.get("recent_genres", []),
                "recent_moods": session_context.get("recent_moods", []),
                "disliked_artists": session_context.get("disliked_artists", []),
                "disliked_tracks": session_context.get("disliked_tracks", []),
            }
            result = self._llm.generate_json(
                system_prompt=SYSTEM_PROMPT,
                payload=payload,
                json_schema=OUTPUT_JSON_SCHEMA,
                schema_name="input_planner_output",
            )
            return self._validate_llm_output(result)
        except Exception as exc:
            logger.warning("llm_planner_fallback", extra={"error": str(exc)})
            return None

    @staticmethod
    def _validate_llm_output(result: dict) -> dict | None:
        if result.get("intent_type") not in ALLOWED_INTENT_TYPES:
            logger.warning("llm_planner_invalid_intent", extra={"intent_type": result.get("intent_type")})
            return None
        result["detected_moods"] = [m for m in result.get("detected_moods", []) if m in ALLOWED_MOODS]
        result["detected_genres"] = [g for g in result.get("detected_genres", []) if g in ALLOWED_GENRES]
        result["detected_situations"] = [s for s in result.get("detected_situations", []) if s in ALLOWED_SITUATIONS]
        result["requested_count"] = InputPlannerAgent._normalize_requested_count(result.get("requested_count"))
        result["disliked_artists"] = InputPlannerAgent._clean_text_list(result.get("disliked_artists", []))
        result["disliked_tracks"] = InputPlannerAgent._clean_text_list(result.get("disliked_tracks", []))
        confidence = result.get("confidence", 0.0)
        result["confidence"] = max(0.0, min(1.0, float(confidence)))
        return result

    def _parse_with_rules(self, user_input: str, session_context: dict) -> dict:
        normalized_query = user_input.strip() if user_input else "music recommendation"
        negative_preferences = self._detect_negative_preferences(normalized_query)
        return {
            "intent_type": self._decide_intent_type(normalized_query),
            "confidence": 0.82,
            "normalized_query": normalized_query,
            "detected_moods": self._detect_candidates(normalized_query, session_context, "recent_moods", ALLOWED_MOODS),
            "detected_genres": self._detect_candidates(normalized_query, session_context, "recent_genres", ALLOWED_GENRES),
            "detected_situations": self._detect_situations(normalized_query),
            "requested_count": self._detect_requested_count(normalized_query),
            "disliked_artists": negative_preferences["disliked_artists"],
            "disliked_tracks": negative_preferences["disliked_tracks"],
        }

    @staticmethod
    def _decide_intent_type(text: str) -> str:
        lowered = (text or "").lower()
        if any(keyword in lowered for keyword in ("latest", "new release", "신곡", "최신", "새로 나온")):
            return "new_release_recommendation"
        if any(keyword in lowered for keyword in ("why", "reason", "이유", "왜")):
            return "recommendation_reason"
        if any(keyword in lowered for keyword in ("info", "information", "정보", "알려")):
            return "music_information"
        if any(keyword in lowered for keyword in ("discover", "new taste", "새로운", "발견")):
            return "discovery_recommendation"
        if any(keyword in lowered for keyword in ("recommend", "추천")) or text:
            return "personalized_recommendation"
        return "general_chat"

    @staticmethod
    def _detect_candidates(text: str, session_context: dict, context_key: str, allowed: set[str]) -> list[str]:
        candidates = [value for value in session_context.get(context_key, []) if value in allowed]
        keyword_map = {
            "calm": ["calm", "잔잔", "차분"],
            "night": ["night", "밤", "야간"],
            "bright": ["bright", "밝은"],
            "clean": ["clean", "깔끔"],
            "indie": ["indie", "인디"],
            "dream_pop": ["dream pop", "드림팝"],
            "ambient": ["ambient", "앰비언트"],
            "rnb": ["rnb", "알앤비"],
            "electro_pop": ["electro pop", "일렉트로"],
        }
        lowered = (text or "").lower()
        for candidate, keywords in keyword_map.items():
            if candidate in allowed and any(keyword in lowered for keyword in keywords):
                candidates.append(candidate)
        return list(dict.fromkeys(candidates))

    @staticmethod
    def _detect_situations(text: str) -> list[str]:
        lowered = (text or "").lower()
        if any(keyword in lowered for keyword in ("late night", "밤", "야간")):
            return ["late_night"] if "late_night" in ALLOWED_SITUATIONS else []
        return []

    @staticmethod
    def _detect_requested_count(text: str) -> int | None:
        digit_match = re.search(r"([1-9]\d*)\s*(?:곡|개)", text or "")
        if digit_match:
            return InputPlannerAgent._normalize_requested_count(int(digit_match.group(1)))

        compact = (text or "").replace(" ", "")
        patterns = {
            3: ("세곡", "셋", "세개", "3곡", "3개"),
            2: ("두곡", "둘", "두개", "2곡", "2개"),
            1: ("한곡", "하나", "한개", "1곡", "1개"),
        }
        for count, tokens in patterns.items():
            if any(token in compact for token in tokens):
                return count
        return None

    @staticmethod
    def _normalize_requested_count(value) -> int | None:
        if value is None:
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return max(1, min(parsed, MAX_SELECTED_RECOMMENDATIONS))

    @staticmethod
    def _detect_negative_preferences(text: str) -> dict:
        markers = ("추천하지 마", "듣기 싫어", "싫어", "싫다", "별로", "빼줘", "제외")
        if not any(marker in text for marker in markers):
            return {"disliked_artists": [], "disliked_tracks": []}

        candidate = text
        for marker in markers:
            if marker in candidate:
                candidate = candidate.split(marker, maxsplit=1)[0]
        candidate = candidate.strip(" ,.!?를은이가")
        return {
            "disliked_artists": [candidate] if candidate else [],
            "disliked_tracks": [],
        }

    @staticmethod
    def _clean_text_list(values: list) -> list[str]:
        return [text for text in (str(value).strip() for value in values) if text]

    @staticmethod
    def _merge_unique(new_items: list[str], existing_items: list[str]) -> list[str]:
        merged = []
        seen = set()
        for value in list(new_items) + list(existing_items):
            text = str(value).strip()
            if text and text not in seen:
                seen.add(text)
                merged.append(text)
        return merged
