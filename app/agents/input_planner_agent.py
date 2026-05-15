import logging
import re

from app.agents.base_agent import BaseAgent
from app.common.constants import (
    ALLOWED_GENRES,
    ALLOWED_INTENT_TYPES,
    ALLOWED_MOODS,
    ALLOWED_SITUATIONS,
    ARTIST_ALIAS_MAP,
    DISCOVERY_KEYWORDS,
    GENRE_KEYWORD_MAP,
    MOOD_KEYWORD_MAP,
)
from app.policies.recommendation_policy import MAX_SELECTED_RECOMMENDATIONS
from app.schemas.intent_state_schema import IntentStateSchema
from app.schemas.kag_input_schema import KagInputSchema

logger = logging.getLogger("rimas.agent.input_planner")


class InputPlannerAgent(BaseAgent):
    """Normalize user input into INTENT_STATE and KAG_INPUT_JSON."""

    def __init__(self, llm_client=None, negative_preference_matcher=None):
        self._llm = llm_client
        self._negative_preference_matcher = negative_preference_matcher

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
        new_dislikes = self._resolve_negative_preferences(parsed)
        disliked_genres = parsed.get("disliked_genres", [])
        detected_genres = self._remove_disliked_genres(
            parsed["detected_genres"],
            disliked_genres,
        )
        detected_artists = self._clean_text_list(parsed.get("detected_artists", []))
        intent_state = IntentStateSchema(
            intent_type=intent_type,
            confidence=parsed["confidence"],
            normalized_query=parsed["normalized_query"],
            detected_moods=parsed["detected_moods"],
            detected_genres=detected_genres,
            detected_artists=detected_artists,
            detected_situations=parsed["detected_situations"],
            requested_count=parsed.get("requested_count"),
            disliked_artists=new_dislikes["disliked_artists"],
            disliked_tracks=new_dislikes["disliked_tracks"],
            disliked_genres=disliked_genres,
            requires_kag=intent_type != "general_chat",
            requires_rag=intent_type != "general_chat",
        )
        excluded_artists = self._merge_unique(
            new_dislikes["disliked_artists"],
            session_context.get("disliked_artists", []),
        )
        context_excluded_tracks = session_context.get("disliked_tracks", [])
        if intent_type == "discovery_recommendation":
            context_excluded_tracks = self._merge_unique(
                session_context.get("selected_tracks", []),
                context_excluded_tracks,
            )
        excluded_tracks = self._merge_unique(new_dislikes["disliked_tracks"], context_excluded_tracks)
        excluded_genres = self._merge_unique(
            parsed.get("disliked_genres", []),
            session_context.get("disliked_genres", []),
        )
        kag_input = KagInputSchema(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            intent_type=intent_type,
            query_context={
                "normalized_query": parsed["normalized_query"],
                "mood_candidates": parsed["detected_moods"],
                "genre_candidates": detected_genres,
                "artist_candidates": detected_artists,
                "situation_candidates": parsed["detected_situations"],
            },
            constraints={
                "allow_discovery": True,
                "allow_new_release": True,
                "max_candidates": parsed.get("requested_count") or 10,
                "excluded_artists": excluded_artists,
                "excluded_tracks": excluded_tracks,
                "excluded_genres": excluded_genres,
            },
        )
        return {
            "intent_state": intent_state.model_dump(),
            "kag_input_json": kag_input.model_dump(),
        }

    @staticmethod
    def _remove_disliked_genres(detected_genres: list[str], disliked_genres: list[str]) -> list[str]:
        disliked = set(disliked_genres or [])
        return [genre for genre in detected_genres if genre not in disliked]

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
        result["detected_artists"] = InputPlannerAgent._clean_text_list(result.get("detected_artists", []))
        result["detected_situations"] = [s for s in result.get("detected_situations", []) if s in ALLOWED_SITUATIONS]
        result["requested_count"] = InputPlannerAgent._normalize_requested_count(result.get("requested_count"))
        result["disliked_artists"] = InputPlannerAgent._clean_text_list(result.get("disliked_artists", []))
        result["disliked_tracks"] = InputPlannerAgent._clean_text_list(result.get("disliked_tracks", []))
        result["disliked_genres"] = [g for g in result.get("disliked_genres", []) if g in ALLOWED_GENRES]
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
            "detected_artists": self._detect_artist_candidates(normalized_query, session_context),
            "detected_situations": self._detect_situations(normalized_query),
            "requested_count": self._detect_requested_count(normalized_query),
            "disliked_artists": negative_preferences["disliked_artists"],
            "disliked_tracks": negative_preferences["disliked_tracks"],
            "disliked_genres": negative_preferences["disliked_genres"],
            "negative_terms": negative_preferences["negative_terms"],
        }

    @staticmethod
    def _decide_intent_type(text: str) -> str:
        lowered = (text or "").lower()
        if any(keyword in lowered for keyword in DISCOVERY_KEYWORDS):
            return "discovery_recommendation"
        if InputPlannerAgent._is_taste_contrast_request(text):
            return "discovery_recommendation"
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
    def _is_taste_contrast_request(text: str) -> bool:
        compact = (text or "").replace(" ", "")
        if "다른" not in compact:
            return False
        return "취향" in compact or "노래" in compact or "곡" in compact

    @staticmethod
    def _detect_candidates(text: str, session_context: dict, context_key: str, allowed: set[str]) -> list[str]:
        candidates = [value for value in session_context.get(context_key, []) if value in allowed]
        keyword_map = {**MOOD_KEYWORD_MAP, **GENRE_KEYWORD_MAP}
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
    def _detect_artist_candidates(text: str, session_context: dict) -> list[str]:
        lowered = (text or "").casefold()
        compact = lowered.replace(" ", "")
        candidates = []
        for alias, canonical in ARTIST_ALIAS_MAP.items():
            normalized_alias = alias.casefold()
            if normalized_alias in lowered or normalized_alias.replace(" ", "") in compact:
                candidates.append(canonical)
        for artist in session_context.get("recent_artists", []) or []:
            artist_text = str(artist).strip()
            if artist_text and artist_text.casefold() in lowered:
                candidates.append(artist_text)
        return InputPlannerAgent._merge_unique(candidates, [])

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
        markers = ("추천하지 마", "듣기 싫어", "싫어", "싫다", "별로", "빼줘", "빼고", "말고", "제외하고", "제외")
        if not any(marker in text for marker in markers):
            return {"disliked_artists": [], "disliked_tracks": [], "disliked_genres": [], "negative_terms": []}

        candidate = text
        for marker in markers:
            if marker in candidate:
                candidate = candidate.split(marker, maxsplit=1)[0]
        negative_scope = InputPlannerAgent._negative_scope(candidate)
        disliked_genres = InputPlannerAgent._detect_negative_genres(negative_scope)
        candidate = InputPlannerAgent._clean_negative_candidate(candidate)
        return {
            "disliked_artists": [],
            "disliked_tracks": [],
            "disliked_genres": disliked_genres,
            "negative_terms": [candidate] if candidate else [],
        }

    @staticmethod
    def _negative_scope(value: str) -> str:
        scope = value or ""
        for marker in ("근데", "그런데", "하지만", "다만", "but"):
            if marker in scope:
                scope = scope.rsplit(marker, maxsplit=1)[-1]
        return scope

    @staticmethod
    def _detect_negative_genres(text: str) -> list[str]:
        compact = (text or "").casefold().replace(" ", "")
        detected = []
        for genre, keywords in GENRE_KEYWORD_MAP.items():
            if genre not in ALLOWED_GENRES:
                continue
            for keyword in keywords + [genre]:
                if keyword.casefold().replace(" ", "") in compact:
                    detected.append(genre)
                    break
        return list(dict.fromkeys(detected))

    @staticmethod
    def _clean_negative_candidate(value: str) -> str:
        candidate = InputPlannerAgent._negative_scope(value).strip(" ,.!?를은이가")
        suffixes = ("음악은", "음악", "장르는", "장르", "노래는", "노래", "곡은", "곡")
        for suffix in suffixes:
            if candidate.endswith(suffix):
                candidate = candidate[: -len(suffix)].strip(" ,.!?를은이가")
        return candidate

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

    def _resolve_negative_preferences(self, parsed: dict) -> dict:
        terms = self._merge_unique(
            parsed.get("negative_terms", []),
            parsed.get("disliked_artists", []) + parsed.get("disliked_tracks", []),
        )
        if not terms or self._negative_preference_matcher is None:
            return {"disliked_artists": [], "disliked_tracks": []}

        artists: list[str] = []
        tracks: list[str] = []
        for term in terms:
            try:
                resolved = self._negative_preference_matcher.resolve(term)
            except Exception as exc:
                logger.warning("negative_preference_match_failed", extra={"term": term, "error": str(exc)})
                continue
            artists.extend(resolved.get("disliked_artists", []))
            tracks.extend(resolved.get("disliked_tracks", []))
        return {
            "disliked_artists": self._merge_unique(artists, []),
            "disliked_tracks": self._merge_unique(tracks, []),
        }
