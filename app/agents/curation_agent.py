INTENT_TO_MODE = {
    "personalized_recommendation": "recommend_personalized",
    "new_release_recommendation": "recommend_new_release",
    "new_taste_discovery": "recommend_discovery",
    "similar_taste_recommendation": "recommend_discovery",
    "music_information_question": "explain_music_information",
    "recommendation_reason_question": "explain_recommendation_reason",
    "general_chat": "general_curator_response",
}

INTENT_TO_FOCUS = {
    "personalized_recommendation": "personalized_match",
    "new_release_recommendation": "new_release",
    "new_taste_discovery": "discovery_candidate",
    "similar_taste_recommendation": "similar_taste",
}


class CurationAgent:
    def run(self, intent_result, kag_state, rag_state):
        evidence_items = rag_state.get("recommended_content_evidence", [])
        if not evidence_items:
            return {
                "status": "empty_result",
                "curation_mode": "fallback",
                "response_focus": None,
                "tone": "fallback",
                "allowed_content_ids": [],
                "primary_content_id": None,
                "use_information_evidence": False,
            }

        intent_type = intent_result.get("intent_type", "general_chat")
        response_focus = self._response_focus(intent_type, evidence_items)
        allowed_items = self._allowed_items(response_focus, evidence_items)
        allowed_content_ids = [item["content_id"] for item in allowed_items]
        primary_content_id = self._primary_content_id(intent_result, allowed_items)

        return {
            "status": "success",
            "curation_mode": INTENT_TO_MODE.get(
                intent_type,
                "general_curator_response",
            ),
            "response_focus": response_focus,
            "tone": "friendly_dj",
            "allowed_content_ids": allowed_content_ids,
            "primary_content_id": primary_content_id,
            "use_information_evidence": intent_type
            in {
                "music_information_question",
                "recommendation_reason_question",
            },
        }

    def _response_focus(self, intent_type, evidence_items):
        preferred_focus = INTENT_TO_FOCUS.get(intent_type)
        if self._has_category(preferred_focus, evidence_items):
            return preferred_focus
        for fallback_focus in (
            "discovery_candidate",
            "personalized_match",
            "new_release",
            "similar_taste",
            "information_related",
        ):
            if self._has_category(fallback_focus, evidence_items):
                return fallback_focus
        return None

    def _allowed_items(self, response_focus, evidence_items):
        if response_focus is None:
            return list(evidence_items)
        matched = [
            item
            for item in evidence_items
            if item.get("recommendation_category") == response_focus
        ]
        return matched or list(evidence_items)

    def _primary_content_id(self, intent_result, allowed_items):
        target_content_id = intent_result.get("target_content_id")
        allowed_ids = {item.get("content_id") for item in allowed_items}
        if target_content_id in allowed_ids:
            return target_content_id
        if not allowed_items:
            return None
        return allowed_items[0].get("content_id")

    def _has_category(self, category, evidence_items):
        if category is None:
            return False
        return any(
            item.get("recommendation_category") == category
            for item in evidence_items
        )
