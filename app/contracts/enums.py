from enum import StrEnum


class IntentType(StrEnum):
    PERSONALIZED_RECOMMENDATION = "personalized_recommendation"
    NEW_RELEASE_RECOMMENDATION = "new_release_recommendation"
    NEW_TASTE_DISCOVERY = "new_taste_discovery"
    SIMILAR_TASTE_RECOMMENDATION = "similar_taste_recommendation"
    MUSIC_INFORMATION_QUESTION = "music_information_question"
    RECOMMENDATION_REASON_QUESTION = "recommendation_reason_question"
    GENERAL_CHAT = "general_chat"


class CurationMode(StrEnum):
    RECOMMEND_PERSONALIZED = "recommend_personalized"
    RECOMMEND_NEW_RELEASE = "recommend_new_release"
    RECOMMEND_DISCOVERY = "recommend_discovery"
    EXPLAIN_MUSIC_INFORMATION = "explain_music_information"
    EXPLAIN_RECOMMENDATION_REASON = "explain_recommendation_reason"
    GENERAL_CURATOR_RESPONSE = "general_curator_response"
    FALLBACK = "fallback"


class RecommendationCategory(StrEnum):
    PERSONALIZED_MATCH = "personalized_match"
    SIMILAR_TASTE = "similar_taste"
    NEW_RELEASE = "new_release"
    DISCOVERY_CANDIDATE = "discovery_candidate"
    INFORMATION_RELATED = "information_related"


class ResponseTone(StrEnum):
    FRIENDLY_DJ = "friendly_dj"
    FALLBACK = "fallback"
