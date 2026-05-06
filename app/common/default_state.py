from app.common.constants import DEFAULT_USER_ID


SESSION_DEFAULTS = {
    "selected_user_id": DEFAULT_USER_ID,
    "current_page": "main_recommendation_page",
    "current_ml_output": None,
    "current_kag_state": None,
    "current_rag_state": None,
    "current_response_state": None,
    "chat_history": [],
    "last_status": None,
    "last_error": None,
}

DEFAULT_ML_OUTPUT = {
    "status": "success",
    "user_id": DEFAULT_USER_ID,
    "taste_profile": {
        "preferred_genres": ["rnb", "indie"],
        "preferred_artists": ["Nova Lane", "Luna Field"],
        "preferred_moods": ["calm", "night"],
        "preferred_tempo": "medium",
    },
    "behavior_profile": {
        "recent_listening_level": "medium",
        "recent_discovery_level": "low",
        "repeat_listening_ratio": 0.72,
        "new_artist_acceptance": 0.34,
    },
    "recommendation_profile": {
        "personalization_strength": "high",
        "discovery_readiness": "medium",
        "new_release_affinity": "medium",
    },
}

FALLBACK_RESPONSE_STATE = {
    "status": "error",
    "response_type": "fallback",
    "chatbot_response": "지금은 충분한 추천 근거를 확인하지 못해 기본 안내만 제공할게요.",
    "display_recommendations": [],
    "used_content_ids": [],
    "provenance": {
        "used_ml_fields": [],
        "used_kag_fields": [],
        "used_rag_content_ids": [],
        "used_rag_fields": [],
    },
    "validation": {
        "response_validation_passed": False,
        "provenance_validation_passed": False,
    },
}
