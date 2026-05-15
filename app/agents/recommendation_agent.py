from app.agents.base_agent import BaseAgent
from app.common.genre_utils import normalize_genre_tokens
from app.policies.ranking_policy import score_for_rank
from app.policies.recommendation_policy import (
    CATEGORY_SECTION_MAP,
    DEFAULT_CATEGORY_PRIORITY,
    DEFAULT_SECTION,
    INTENT_CATEGORY_PRIORITY,
    MAX_SELECTED_RECOMMENDATIONS,
)


class RecommendationAgent(BaseAgent):
    """Select final display recommendations from RAG evidence."""

    def run(self, intent_result: dict, rag_state: dict) -> dict:
        intent_type = intent_result.get("intent_type", "personalized_recommendation")
        evidence = rag_state.get("recommended_content_evidence", [])

        if not evidence:
            return {"status": "empty_result", "selected_recommendations": []}

        selected = self._select(
            intent_type,
            evidence,
            requested_count=intent_result.get("requested_count"),
            disliked_artists=intent_result.get("disliked_artists", []),
            disliked_tracks=intent_result.get("disliked_tracks", []),
            disliked_genres=intent_result.get("disliked_genres", []),
        )
        return {
            "status": "success" if selected else "empty_result",
            "selected_recommendations": selected,
        }

    def _select(
        self,
        intent_type: str,
        evidence: list[dict],
        requested_count: int | None = None,
        disliked_artists: list[str] | None = None,
        disliked_tracks: list[str] | None = None,
        disliked_genres: list[str] | None = None,
    ) -> list[dict]:
        priority = INTENT_CATEGORY_PRIORITY.get(intent_type, DEFAULT_CATEGORY_PRIORITY)
        target_count = self._target_count(requested_count)
        excluded_artists = set(disliked_artists or [])
        excluded_tracks = set(disliked_tracks or [])
        excluded_genres = normalize_genre_tokens(disliked_genres or [])

        ordered: list[dict] = []
        used_ids: set[str] = set()
        for category in priority:
            for item in evidence:
                content_id = item.get("content_id")
                if item.get("recommendation_category") != category:
                    continue
                if not content_id or content_id in used_ids:
                    continue
                if content_id in excluded_tracks or item.get("artist") in excluded_artists:
                    continue
                if self._has_excluded_genre(item, excluded_genres):
                    continue
                ordered.append(self._to_selected(item, rank=len(ordered) + 1))
                used_ids.add(content_id)
                if len(ordered) >= target_count:
                    return ordered

        return ordered[:target_count]

    @staticmethod
    def _target_count(requested_count: int | None) -> int:
        if requested_count is None:
            return MAX_SELECTED_RECOMMENDATIONS
        try:
            parsed = int(requested_count)
        except (TypeError, ValueError):
            return MAX_SELECTED_RECOMMENDATIONS
        return max(1, min(parsed, MAX_SELECTED_RECOMMENDATIONS))

    @staticmethod
    def _has_excluded_genre(item: dict, excluded_genres: set[str]) -> bool:
        if not excluded_genres:
            return False
        return bool(normalize_genre_tokens(item.get("genre")) & excluded_genres)

    @staticmethod
    def _to_selected(item: dict, rank: int) -> dict:
        category = item.get("recommendation_category", "")
        return {
            "content_id": item["content_id"],
            "title": item["title"],
            "artist": item["artist"],
            "section": CATEGORY_SECTION_MAP.get(category, DEFAULT_SECTION),
            "recommendation_category": category,
            "display_reason": build_display_reason(item),
            "rank": rank,
            "score": score_for_rank(rank),
            "source": {"kag": False, "rag": True},
        }


def build_display_reason(item: dict) -> str:
    genres = item.get("genre") or []
    moods = item.get("mood") or []
    genre_text = ", ".join(genres[:2]) if genres else "현재 취향"
    mood_text = ", ".join(moods[:2]) if moods else "듣기 좋은 분위기"
    category = item.get("recommendation_category")
    if category == "new_release":
        return f"최근 업데이트된 곡 중 {genre_text} 성향과 {mood_text} 분위기를 함께 볼 수 있는 곡입니다."
    if category == "discovery_candidate":
        return f"{mood_text} 흐름을 유지하면서 {genre_text} 쪽으로 취향을 넓혀볼 수 있는 곡입니다."
    return f"{genre_text} 취향과 {mood_text} 분위기에 맞춰 고른 곡입니다."
