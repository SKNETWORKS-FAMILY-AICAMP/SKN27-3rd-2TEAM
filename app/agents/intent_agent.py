from app.agents.base_agent import BaseAgent
from app.common.constants import ALLOWED_INTENT_TYPES


class IntentAgent(BaseAgent):
    def run(self, user_input, kag_state=None, rag_state=None, intent_state=None):
        text = user_input or ""
        intent_type = self._confirmed_intent_type(text, intent_state)
        return {
            "status": "success",
            "intent_type": intent_type,
            "confidence": 0.86,
            "target_content_id": self._find_target_content_id(text, rag_state or {}),
            "requires_recommendation": intent_type
            in {
                "personalized_recommendation",
                "new_release_recommendation",
                "discovery_recommendation",
            },
            "requires_information": intent_type
            in {
                "music_information",
                "recommendation_reason",
            },
        }

    def _confirmed_intent_type(self, text, intent_state):
        planned_intent = (intent_state or {}).get("intent_type")
        if planned_intent in ALLOWED_INTENT_TYPES:
            return planned_intent
        return self._classify(text)

    def _classify(self, text):
        if "왜" in text or "이유" in text:
            return "recommendation_reason"
        if "최신" in text or "새로 나온" in text or "신곡" in text:
            return "new_release_recommendation"
        if "뭐야" in text or "정보" in text or "알려" in text or "어떤" in text:
            return "music_information"
        if "다른" in text or "새로운" in text or "발견" in text:
            return "discovery_recommendation"
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
