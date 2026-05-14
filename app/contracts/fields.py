from enum import StrEnum


class CommonField(StrEnum):
    STATUS = "status"
    USER_ID = "user_id"


class SessionContextField(StrEnum):
    SESSION_ID = "session_id"
    RECENT_GENRES = "recent_genres"
    RECENT_ARTISTS = "recent_artists"
    RECENT_MOODS = "recent_moods"
    SELECTED_TRACKS = "selected_tracks"
    CONVERSATION_SUMMARY = "conversation_summary"


class KagStateField(StrEnum):
    STATUS = "status"
    RECOMMENDATION_GOAL = "recommendation_goal"
    RECOMMENDED_CONTENT_IDS = "recommended_content_ids"
    RECOMMENDATION_CATEGORY = "recommendation_category"
    ROUTE = "route"
    TARGET_SECTION = "target_section"


class RagStateField(StrEnum):
    STATUS = "status"
    RECOMMENDED_CONTENT_EVIDENCE = "recommended_content_evidence"
    RECOMMENDATION_REASON = "recommendation_reason"


class IntentResultField(StrEnum):
    STATUS = "status"
    INTENT_TYPE = "intent_type"
    CONFIDENCE = "confidence"
    TARGET_CONTENT_ID = "target_content_id"
    REQUIRES_RECOMMENDATION = "requires_recommendation"
    REQUIRES_INFORMATION = "requires_information"


class RecommendationField(StrEnum):
    CONTENT_ID = "content_id"
    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    GENRE = "genre"
    MOOD = "mood"
    TEMPO = "tempo"
    RELEASE_TYPE = "release_type"
    RECOMMENDATION_CATEGORY = "recommendation_category"
    EVIDENCE_SUMMARY = "evidence_summary"
    MATCH_REASON = "match_reason"
    DISPLAY_REASON = "display_reason"


class SelectedRecommendationsField(StrEnum):
    STATUS = "status"
    SELECTED_RECOMMENDATIONS = "selected_recommendations"


class ResponseStateField(StrEnum):
    STATUS = "status"
    RESPONSE_TYPE = "response_type"
    CHATBOT_RESPONSE = "chatbot_response"
    DISPLAY_RECOMMENDATIONS = "display_recommendations"
    USED_CONTENT_IDS = "used_content_ids"


class InteractionLogField(StrEnum):
    LOG_ID = "log_id"
    USER_ID = "user_id"
    SESSION_ID = "session_id"
    USER_INPUT = "user_input"
    SESSION_CONTEXT = "session_context"
    KAG_STATE = "kag_state"
    RAG_STATE = "rag_state"
    RESPONSE_STATE = "response_state"
    VALIDATION_STATUS = "validation_status"
    ERROR_TYPE = "error_type"
    LATENCY_MS = "latency_ms"
    CREATED_AT = "created_at"
