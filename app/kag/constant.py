"""KAG 어댑터용 primary_goal·추천 카테고리·라우팅 상수 및 매핑."""

# --- recommendation_goal.primary_goal ---
PRIMARY_GOAL_RECOMMENDATION_REASON_QUESTION = "recommendation_reason_question"
PRIMARY_GOAL_NEW_RELEASE_RECOMMENDATION = "new_release_recommendation"
PRIMARY_GOAL_SIMILAR_TASTE_RECOMMENDATION = "similar_taste_recommendation"
PRIMARY_GOAL_NEW_TASTE_DISCOVERY = "new_taste_discovery"
PRIMARY_GOAL_PERSONALIZED_RECOMMENDATION = "personalized_recommendation"

# --- kag_state.recommendation_category (계약·RAG 카테고리와 정합) ---
RECOMMENDATION_CATEGORY_NEW_RELEASE = "new_release"
RECOMMENDATION_CATEGORY_DISCOVERY_CANDIDATE = "discovery_candidate"
RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH = "personalized_match"

# --- kag_state.route ---
ROUTE_NEW_RELEASE = "new_release"
ROUTE_SAFE_DISCOVERY = "safe_discovery"
ROUTE_PERSONALIZED = "personalized"

# --- kag_state.target_section ---
TARGET_SECTION_NEW_RELEASE = "new_release_section"
TARGET_SECTION_DISCOVERY = "discovery_section"
TARGET_SECTION_PERSONALIZED = "personalized_section"

PRIMARY_GOAL_TO_RECOMMENDATION_CATEGORY: dict[str, str] = {
    PRIMARY_GOAL_NEW_RELEASE_RECOMMENDATION: RECOMMENDATION_CATEGORY_NEW_RELEASE,
    PRIMARY_GOAL_NEW_TASTE_DISCOVERY: RECOMMENDATION_CATEGORY_DISCOVERY_CANDIDATE,
}

PRIMARY_GOAL_TO_ROUTE: dict[str, str] = {
    PRIMARY_GOAL_NEW_RELEASE_RECOMMENDATION: ROUTE_NEW_RELEASE,
    PRIMARY_GOAL_NEW_TASTE_DISCOVERY: ROUTE_SAFE_DISCOVERY,
}

CATEGORY_TO_TARGET_SECTION: dict[str, str] = {
    RECOMMENDATION_CATEGORY_NEW_RELEASE: TARGET_SECTION_NEW_RELEASE,
    RECOMMENDATION_CATEGORY_DISCOVERY_CANDIDATE: TARGET_SECTION_DISCOVERY,
}


def primary_goal_from_user_input(user_input: str) -> str:
    """사용자 문장에서 primary_goal 문자열을 결정한다."""
    text = user_input or ""
    if "왜" in text or "이유" in text:
        return PRIMARY_GOAL_RECOMMENDATION_REASON_QUESTION
    if "최신" in text or "새로 나온" in text or "신곡" in text:
        return PRIMARY_GOAL_NEW_RELEASE_RECOMMENDATION
    if "비슷" in text:
        return PRIMARY_GOAL_SIMILAR_TASTE_RECOMMENDATION
    if "취향" in text or "새로운" in text:
        return PRIMARY_GOAL_NEW_TASTE_DISCOVERY
    return PRIMARY_GOAL_PERSONALIZED_RECOMMENDATION


def recommendation_category_for_primary_goal(primary_goal: str) -> str:
    return PRIMARY_GOAL_TO_RECOMMENDATION_CATEGORY.get(
        primary_goal,
        RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH,
    )


def route_for_primary_goal(primary_goal: str) -> str:
    return PRIMARY_GOAL_TO_ROUTE.get(primary_goal, ROUTE_PERSONALIZED)


def target_section_for_category(category: str) -> str:
    return CATEGORY_TO_TARGET_SECTION.get(category, TARGET_SECTION_PERSONALIZED)
