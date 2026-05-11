from app.agents.base_agent import BaseAgent
from app.policies.ranking_policy import score_for_rank
from app.policies.recommendation_policy import (
    CATEGORY_SECTION_MAP,
    DEFAULT_CATEGORY_PRIORITY,
    DEFAULT_SECTION,
    INTENT_CATEGORY_PRIORITY,
    MAX_SELECTED_RECOMMENDATIONS,
)


class RecommendationAgent(BaseAgent):
    """RAG evidence에서 최종 표시 추천만 선택한다."""

    def run(self, intent_result: dict, rag_state: dict) -> dict:
        intent_type = intent_result.get("intent_type", "personalized_recommendation")
        evidence = rag_state.get("recommended_content_evidence", [])

        if not evidence:
            return {"status": "empty_result", "selected_recommendations": []}

        selected = self._select(intent_type, evidence)
        return {
            "status": "success" if selected else "empty_result",
            "selected_recommendations": selected,
        }

    def _select(self, intent_type: str, evidence: list[dict]) -> list[dict]:
        priority = INTENT_CATEGORY_PRIORITY.get(intent_type, DEFAULT_CATEGORY_PRIORITY)

        ordered: list[dict] = []
        used_ids: set[str] = set()
        for category in priority:
            for item in evidence:
                content_id = item.get("content_id")
                if item.get("recommendation_category") == category and content_id not in used_ids:
                    ordered.append(self._to_selected(item, rank=len(ordered) + 1))
                    used_ids.add(content_id)

        return ordered[:MAX_SELECTED_RECOMMENDATIONS]

    @staticmethod
    def _to_selected(item: dict, rank: int) -> dict:
        category = item.get("recommendation_category", "")
        return {
            "content_id": item["content_id"],
            "title": item["title"],
            "artist": item["artist"],
            "section": CATEGORY_SECTION_MAP.get(category, DEFAULT_SECTION),
            "recommendation_category": category,
            "display_reason": item.get("evidence_summary", ""),
            "rank": rank,
            "score": score_for_rank(rank),
            "source": {"kag": False, "rag": True},
        }
