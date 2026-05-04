class ViewModelService:
    def build_main_view_model(self, user_id, ml_output, kag_state, rag_state, validation_result):
        evidence_items = rag_state.get("recommended_content_evidence", [])
        recommendation_groups = self._group_recommendations(evidence_items)
        taste_profile = ml_output.get("taste_profile", {})

        return {
            "page_type": "main_recommendation_page",
            "status": rag_state.get("status", "error"),
            "user_id": user_id,
            "taste_badges": self._build_taste_badges(taste_profile),
            "today_theme": rag_state.get("recommendation_reason", {}).get("summary", ""),
            "character_message": rag_state.get("recommendation_scripts", {}).get(
                "dj_intro", ""
            ),
            "recommendation_groups": recommendation_groups,
            "personalized_guide": rag_state.get("recommendation_scripts", {}).get(
                "discovery_message", ""
            ),
            "debug": {
                "ml_output": ml_output,
                "kag_state": kag_state,
                "rag_state": rag_state,
                "selected_path": kag_state.get("selected_path"),
                "validation_result": validation_result,
                "latency_ms": 0,
                "error_type": None if validation_result.get("passed") else "CONTRACT_VALIDATION_FAILED",
            },
        }

    def build_chatbot_view_model(
        self,
        user_id,
        user_input,
        response_state,
        ml_output,
        kag_state,
        rag_state,
        validation_result,
    ):
        return {
            "page_type": "chatbot_page",
            "status": response_state.get("status", "error"),
            "user_id": user_id,
            "user_input": user_input,
            "chatbot_response": response_state.get("chatbot_response", ""),
            "related_recommendations": response_state.get("display_recommendations", []),
            "debug": {
                "ml_output": ml_output,
                "kag_state": kag_state,
                "rag_state": rag_state,
                "response_state": response_state,
                "selected_path": kag_state.get("selected_path"),
                "validation_result": validation_result,
                "latency_ms": 0,
                "error_type": None if validation_result.get("passed") else "PROVENANCE_VALIDATION_FAILED",
            },
        }

    def _group_recommendations(self, evidence_items):
        groups = {
            "personalized_match": [],
            "similar_taste": [],
            "new_release": [],
            "discovery_candidate": [],
        }
        for item in evidence_items:
            category = item.get("recommendation_category")
            if category not in groups:
                continue
            groups[category].append(self._to_card(item))
        return groups

    def _to_card(self, item):
        return {
            "content_id": item.get("content_id"),
            "title": item.get("title"),
            "artist": item.get("artist"),
            "album": item.get("album"),
            "genre": item.get("genre", []),
            "mood": item.get("mood", []),
            "release_type": item.get("release_type"),
            "display_reason": item.get("evidence_summary", ""),
        }

    def _build_taste_badges(self, taste_profile):
        return (
            taste_profile.get("preferred_genres", [])
            + taste_profile.get("preferred_moods", [])
            + [taste_profile.get("preferred_tempo", "unknown")]
        )
