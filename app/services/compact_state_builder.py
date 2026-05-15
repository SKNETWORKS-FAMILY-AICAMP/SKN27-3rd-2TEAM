from app.agents.recommendation_agent import build_display_reason
from app.validators.display_reason_validator import DisplayReasonValidator


class CompactStateBuilder:
    """내부 Full State를 API 전송용 Compact State로 변환한다."""

    def build(self, kag_state: dict, rag_state: dict, response_state: dict | None = None) -> dict:
        compact = {
            "kag_state": self.compact_kag_state(kag_state),
            "rag_state": self.compact_rag_state(rag_state),
        }
        if response_state is not None:
            compact["response_state"] = self.compact_response_state(response_state)
        return compact

    @staticmethod
    def compact_kag_state(kag_state: dict) -> dict:
        return {
            "status": kag_state.get("status"),
            "recommendation_goal": kag_state.get("recommendation_goal", {}),
            "target_section": kag_state.get("target_section")
            or kag_state.get("routing", {}).get("target_section"),
        }

    @staticmethod
    def compact_rag_state(rag_state: dict) -> dict:
        display_recommendations = []
        for item in rag_state.get("recommended_content_evidence", []):
            display_recommendations.append(
                {
                    "content_id": item.get("content_id"),
                    "title": item.get("title"),
                    "artist": item.get("artist"),
                    "display_reason": _safe_display_reason(item),
                }
            )
        return {
            "status": rag_state.get("status"),
            "display_recommendations": display_recommendations,
        }

    @staticmethod
    def compact_response_state(response_state: dict) -> dict:
        allowed = {
            "status",
            "response_type",
            "chatbot_response",
            "display_recommendations",
            "used_content_ids",
        }
        return {key: value for key, value in response_state.items() if key in allowed}


def _safe_display_reason(item: dict) -> str:
    reason = item.get("display_reason", "")
    if DisplayReasonValidator().validate(reason, item).get("passed"):
        return reason
    return build_display_reason(item)
