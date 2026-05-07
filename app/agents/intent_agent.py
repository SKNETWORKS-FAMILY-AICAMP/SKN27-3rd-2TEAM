from app.agents.base_agent import BaseAgent


class IntentAgent(BaseAgent):
    def run(self, user_input, kag_state=None, rag_state=None):
        text = user_input or ""
        intent_type = self._classify(text)
        return {
            "status": "success",
            "intent_type": intent_type,
            "confidence": 0.86,
            "target_content_id": self._find_target_content_id(text, rag_state or {}),
            "requires_recommendation": intent_type
            in {
                "personalized_recommendation",
                "new_release_recommendation",
                "new_taste_discovery",
                "similar_taste_recommendation",
            },
            "requires_information": intent_type
            in {
                "music_information_question",
                "recommendation_reason_question",
            },
        }

    def _classify(self, text):
        if "왜" in text or "이유" in text:
            return "recommendation_reason_question"
        if "최신" in text or "새로 나온" in text or "신곡" in text:
            return "new_release_recommendation"
        if "비슷" in text:
            return "similar_taste_recommendation"
        if "뭐야" in text or "정보" in text or "어떤" in text:
            return "music_information_question"
        if "취향" in text or "다른" in text or "새로운" in text:
            return "new_taste_discovery"
        if "추천" in text:
            return "personalized_recommendation"
        return "general_chat"

    def _find_target_content_id(self, text, rag_state):
        for item in rag_state.get("recommended_content_evidence", []):
            content_id = item.get("content_id")
            title = item.get("title")
            if content_id and content_id in text:
                return content_id
            if title and title in text:
                return content_id
        return None
