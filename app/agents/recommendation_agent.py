from app.agents.base_agent import BaseAgent


class RecommendationAgent(BaseAgent):
    def run(self, curation_plan, rag_state):
        if curation_plan.get("curation_mode") == "fallback":
            return {
                "status": "empty_result",
                "selected_recommendations": [],
            }

        evidence_by_id = {
            item.get("content_id"): item
            for item in rag_state.get("recommended_content_evidence", [])
        }
        allowed_content_ids = curation_plan.get("allowed_content_ids", [])
        primary_content_id = curation_plan.get("primary_content_id")

        selected_items = []
        if primary_content_id in allowed_content_ids:
            selected_items.append(evidence_by_id.get(primary_content_id))

        for content_id in allowed_content_ids:
            item = evidence_by_id.get(content_id)
            if item is None or item in selected_items:
                continue
            selected_items.append(item)

        recommendations = [
            self._to_selected_recommendation(item)
            for item in selected_items
            if item is not None
        ]
        return {
            "status": "success" if recommendations else "empty_result",
            "selected_recommendations": recommendations,
        }

    def _to_selected_recommendation(self, item):
        return {
            "content_id": item["content_id"],
            "title": item["title"],
            "artist": item["artist"],
            "recommendation_category": item["recommendation_category"],
            "display_reason": item.get("evidence_summary", ""),
        }
