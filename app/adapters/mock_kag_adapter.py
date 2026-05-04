from app.adapters.kag_adapter import KagAdapter


class MockKagAdapter(KagAdapter):
    def build_state(self, user_id, user_input, ml_output):
        if not user_id:
            raise ValueError("user_id is required")
        if not ml_output:
            raise ValueError("ml_output is required")

        taste_profile = ml_output.get("taste_profile", {})
        behavior_profile = ml_output.get("behavior_profile", {})

        return {
            "status": "success",
            "user": {"user_id": user_id},
            "recommendation_goal": {
                "primary_goal": self._decide_primary_goal(user_input),
                "secondary_goal": "personalized_recommendation",
                "goal_reason": "기존 취향을 유지하면서 안전한 취향 확장을 제공한다.",
            },
            "user_context": {
                "base_preference": {
                    "genres": taste_profile.get("preferred_genres", []),
                    "moods": taste_profile.get("preferred_moods", []),
                    "tempo": taste_profile.get("preferred_tempo", "unknown"),
                },
                "behavior_context": {
                    "recent_listening_level": behavior_profile.get(
                        "recent_listening_level", "medium"
                    ),
                    "recent_discovery_level": behavior_profile.get(
                        "recent_discovery_level", "medium"
                    ),
                    "repeat_listening_ratio": behavior_profile.get(
                        "repeat_listening_ratio", 0
                    ),
                    "new_artist_acceptance": behavior_profile.get(
                        "new_artist_acceptance", 0
                    ),
                },
            },
            "curation_intent": {
                "intent_type": self._decide_primary_goal(user_input),
                "intent_confidence": 0.86,
                "allowed_modes": [
                    "personalized_recommendation",
                    "new_taste_discovery",
                    "similar_taste_recommendation",
                ],
            },
            "curation_strategy": {
                "strategy_code": "SAFE_DISCOVERY_FROM_PERSONAL_TASTE",
                "strategy_level": "medium",
                "strategy_description_for_internal": "기존 취향과 연결되는 안전한 취향 탐색",
            },
            "content_requirements": {
                "must_include": ["personalized_match", "discovery_candidate"],
                "optional_include": ["new_release"],
                "avoid": ["too_aggressive_genre_shift"],
            },
            "routing": {
                "target_page": "main_recommendation_page",
                "primary_section": "discovery_section",
                "secondary_sections": [
                    "personalized_recommendation_section",
                    "new_release_section",
                ],
            },
            "selected_path": "personalized_to_safe_discovery",
        }

    def _decide_primary_goal(self, user_input):
        text = user_input or ""
        if "왜" in text or "이유" in text:
            return "recommendation_reason_question"
        if "취향" in text:
            return "new_taste_discovery"
        if "최신" in text or "새로 나온" in text or "새 곡" in text:
            return "new_release_recommendation"
        return "new_taste_discovery"
