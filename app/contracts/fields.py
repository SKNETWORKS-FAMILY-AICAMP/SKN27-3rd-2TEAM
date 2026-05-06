from enum import StrEnum


class CommonField(StrEnum):
    STATUS = "status"
    USER_ID = "user_id"


class MlOutputField(StrEnum):
    STATUS = "status"
    USER_ID = "user_id"
    TASTE_PROFILE = "taste_profile"
    BEHAVIOR_PROFILE = "behavior_profile"
    RECOMMENDATION_PROFILE = "recommendation_profile"


class KagStateField(StrEnum):
    STATUS = "status"
    USER = "user"
    RECOMMENDATION_GOAL = "recommendation_goal"
    USER_CONTEXT = "user_context"
    CURATION_INTENT = "curation_intent"
    CURATION_STRATEGY = "curation_strategy"
    CONTENT_REQUIREMENTS = "content_requirements"
    ROUTING = "routing"
    SELECTED_PATH = "selected_path"


class RagStateField(StrEnum):
    STATUS = "status"
    RECOMMENDATION_CONTEXT = "recommendation_context"
    RECOMMENDED_CONTENT_EVIDENCE = "recommended_content_evidence"
    RECOMMENDATION_REASON = "recommendation_reason"
    INFORMATION_EVIDENCE = "information_evidence"
    RECOMMENDATION_SCRIPTS = "recommendation_scripts"


class IntentResultField(StrEnum):
    STATUS = "status"
    INTENT_TYPE = "intent_type"
    CONFIDENCE = "confidence"
    TARGET_CONTENT_ID = "target_content_id"
    REQUIRES_RECOMMENDATION = "requires_recommendation"
    REQUIRES_INFORMATION = "requires_information"


class CurationPlanField(StrEnum):
    STATUS = "status"
    CURATION_MODE = "curation_mode"
    RESPONSE_FOCUS = "response_focus"
    TONE = "tone"
    ALLOWED_CONTENT_IDS = "allowed_content_ids"
    PRIMARY_CONTENT_ID = "primary_content_id"
    USE_INFORMATION_EVIDENCE = "use_information_evidence"


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
    PROVENANCE = "provenance"
    VALIDATION = "validation"


class InteractionLogField(StrEnum):
    LOG_ID = "log_id"
    USER_ID = "user_id"
    USER_INPUT = "user_input"
    ML_OUTPUT = "ml_output"
    KAG_STATE = "kag_state"
    RAG_STATE = "rag_state"
    RESPONSE_STATE = "response_state"
    VALIDATION_STATUS = "validation_status"
    ERROR_TYPE = "error_type"
    LATENCY_MS = "latency_ms"
    CREATED_AT = "created_at"
