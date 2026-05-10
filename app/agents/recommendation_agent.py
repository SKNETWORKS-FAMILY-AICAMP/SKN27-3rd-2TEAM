from app.agents.base_agent import BaseAgent


class RecommendationAgent(BaseAgent):
    """RAG evidence에서 최종 표시 추천만 선택한다."""

    _CATEGORY_SECTION_MAP = {
        "personalized_match": "personalized",
        "discovery_candidate": "discovery",
        "new_release": "new_release",
    }

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
        if intent_type == "new_release_recommendation":
            priority = ["new_release", "personalized_match", "discovery_candidate"]
        elif intent_type in {"new_taste_discovery", "discovery_recommendation"}:
            priority = ["discovery_candidate", "personalized_match", "new_release"]
        else:
            priority = ["personalized_match", "discovery_candidate", "new_release"]

        ordered: list[dict] = []
        used_ids: set[str] = set()
        for category in priority:
            for item in evidence:
                content_id = item.get("content_id")
                if item.get("recommendation_category") == category and content_id not in used_ids:
                    ordered.append(self._to_selected(item, rank=len(ordered) + 1))
                    used_ids.add(content_id)

        return ordered[:5]

    @staticmethod
    def _to_selected(item: dict, rank: int) -> dict:
        category = item.get("recommendation_category", "")
        return {
            "content_id": item["content_id"],
            "title": item["title"],
            "artist": item["artist"],
            "section": RecommendationAgent._CATEGORY_SECTION_MAP.get(category, "personalized"),
            "recommendation_category": category,
            "display_reason": item.get("evidence_summary", ""),
            "rank": rank,
            "score": round(max(0.1, 1.0 - ((rank - 1) * 0.05)), 2),
            "source": {"kag": False, "rag": True},
        }
