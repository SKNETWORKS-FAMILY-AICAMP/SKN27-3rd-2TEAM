"""Recommendation Agent 선택 정책."""

CATEGORY_SECTION_MAP = {
    "personalized_match": "personalized",
    "discovery_candidate": "discovery",
    "new_release": "new_release",
}

DEFAULT_CATEGORY_PRIORITY = [
    "personalized_match",
    "discovery_candidate",
    "new_release",
]

INTENT_CATEGORY_PRIORITY = {
    "personalized_recommendation": DEFAULT_CATEGORY_PRIORITY,
    "recommendation_reason": DEFAULT_CATEGORY_PRIORITY,
    "music_information": DEFAULT_CATEGORY_PRIORITY,
    "general_chat": DEFAULT_CATEGORY_PRIORITY,
    "new_release_recommendation": [
        "new_release",
        "personalized_match",
        "discovery_candidate",
    ],
    "discovery_recommendation": [
        "discovery_candidate",
        "personalized_match",
        "new_release",
    ],
}

MAX_SELECTED_RECOMMENDATIONS = 5
DEFAULT_SECTION = "personalized"
