# 패키지
from enum import Enum
from dataclasses import dataclass

###########################################################
# 실행할 쿼리 타입
###########################################################
class KagQueryType(str, Enum):
    PERSONALIZED_MATCH = "personalized_match"
    SIMILAR_TASTE = "similar_taste"
    SAFE_DISCOVERY = "safe_discovery"
    NEW_RELEASE = "new_release"
    MOOD_BASED = "mood_based"
    INFORMATION_RELATED = "information_related"


###########################################################
# 쿼리 정책 (타입별 고정 값 정의)
###########################################################
@dataclass(frozen=True)
class KagQueryPolicy:
    primary_goal: str
    secondary_goal: str
    intent_type: str
    intent_confidence_base: float
    allowed_modes: tuple[str, ...]
    strategy_code: str
    strategy_level: str
    strategy_description_for_internal: str
    must_include: tuple[str, ...]
    optional_include: tuple[str, ...]
    avoid: tuple[str, ...]
    target_page: str
    primary_section: str
    secondary_sections: tuple[str, ...]
    selected_path: str


###########################################################
# 쿼리 정책 매핑
###########################################################
class KagQueryPolicies:
    """
    쿼리타입 별로 가져야 할 고정 입력 값들을 정의해서 가지고 있는다. 
    해당 쿼리 타입으로 검색이 실행되는 경우 LangGraph의 flow에 타입별로 다음 값들을 채워서 반환하게 된다. 
    """

    ##################### 타입별 정첵 값 정의 ####################
    PERSONALIZED_MATCH = KagQueryPolicy(
        primary_goal="personalized_recommendation",
        secondary_goal="taste_continuity",
        intent_type="personalized_recommendation",
        intent_confidence_base=0.75,
        allowed_modes=(
            "personalized_recommendation",
            "similar_taste_recommendation",
        ),
        strategy_code="PERSONALIZED_MATCH_FROM_USER_PROFILE",
        strategy_level="medium",
        strategy_description_for_internal="사용자의 기존 취향 프로필을 기반으로 안정적인 개인화 추천을 수행",
        must_include=("personalized_match",),
        optional_include=("similar_taste",),
        avoid=("unsupported_generation",),
        target_page="chatbot_page",
        primary_section="personalized_recommendation_section",
        secondary_sections=("similar_taste_section",),
        selected_path="user_profile_to_personalized_match",
    )

    SIMILAR_TASTE = KagQueryPolicy(
        primary_goal="similar_taste_recommendation",
        secondary_goal="personalized_recommendation",
        intent_type="similar_taste_recommendation",
        intent_confidence_base=0.78,
        allowed_modes=(
            "similar_taste_recommendation",
            "personalized_recommendation",
        ),
        strategy_code="SIMILAR_TASTE_FROM_BASE_PREFERENCE",
        strategy_level="medium",
        strategy_description_for_internal="기존 선호 장르/무드/아티스트와 유사한 콘텐츠를 우선 추천",
        must_include=("similar_taste",),
        optional_include=("personalized_match",),
        avoid=("too_aggressive_genre_shift",),
        target_page="chatbot_page",
        primary_section="similar_taste_section",
        secondary_sections=("personalized_recommendation_section",),
        selected_path="base_preference_to_similar_taste",
    )

    SAFE_DISCOVERY = KagQueryPolicy(
        primary_goal="new_taste_discovery",
        secondary_goal="personalized_recommendation",
        intent_type="new_taste_discovery",
        intent_confidence_base=0.8,
        allowed_modes=(
            "personalized_recommendation",
            "new_taste_discovery",
            "similar_taste_recommendation",
        ),
        strategy_code="SAFE_DISCOVERY_FROM_PERSONAL_TASTE",
        strategy_level="medium",
        strategy_description_for_internal="기존 취향과 연결되는 안전한 새 취향 탐색",
        must_include=("personalized_match", "discovery_candidate"),
        optional_include=("new_release",),
        avoid=("too_aggressive_genre_shift",),
        target_page="chatbot_page",
        primary_section="discovery_section",
        secondary_sections=(
            "personalized_recommendation_section",
            "new_release_section",
        ),
        selected_path="personalized_to_safe_discovery",
    )

    NEW_RELEASE = KagQueryPolicy(
        primary_goal="new_release_recommendation",
        secondary_goal="personalized_recommendation",
        intent_type="new_release_recommendation",
        intent_confidence_base=0.82,
        allowed_modes=(
            "new_release_recommendation",
            "personalized_recommendation",
        ),
        strategy_code="NEW_RELEASE_WITH_USER_AFFINITY",
        strategy_level="medium",
        strategy_description_for_internal="사용자의 신곡 수용도와 기존 취향을 함께 반영한 최신 콘텐츠 추천",
        must_include=("new_release",),
        optional_include=("personalized_match",),
        avoid=("unsupported_generation",),
        target_page="chatbot_page",
        primary_section="new_release_section",
        secondary_sections=("personalized_recommendation_section",),
        selected_path="new_release_affinity_to_recent_content",
    )

    MOOD_BASED = KagQueryPolicy(
        primary_goal="mood_based_recommendation",
        secondary_goal="personalized_recommendation",
        intent_type="mood_based_recommendation",
        intent_confidence_base=0.72,
        allowed_modes=(
            "mood_based_recommendation",
            "personalized_recommendation",
        ),
        strategy_code="MOOD_MATCH_FROM_CONTEXT",
        strategy_level="medium",
        strategy_description_for_internal="사용자 선호 무드와 세션 문맥의 분위기를 기준으로 콘텐츠 추천",
        must_include=("personalized_match",),
        optional_include=("similar_taste",),
        avoid=("mood_mismatch",),
        target_page="chatbot_page",
        primary_section="mood_recommendation_section",
        secondary_sections=("personalized_recommendation_section",),
        selected_path="context_mood_to_recommendation",
    )

    INFORMATION_RELATED = KagQueryPolicy(
        primary_goal="recommendation_explanation",
        secondary_goal="personalized_recommendation",
        intent_type="information_related",
        intent_confidence_base=0.85,
        allowed_modes=(
            "information_related",
            "personalized_recommendation",
        ),
        strategy_code="EXPLAIN_RECOMMENDATION_CONTEXT",
        strategy_level="low",
        strategy_description_for_internal="추천 이유 또는 사용자 취향 맥락 설명을 우선 제공",
        must_include=("information_related",),
        optional_include=("personalized_match",),
        avoid=("unsupported_generation",),
        target_page="chatbot_page",
        primary_section="explanation_section",
        secondary_sections=("personalized_recommendation_section",),
        selected_path="user_question_to_explanation",
    )

    ##################### 타입별 정책 값 매핑 ####################
    MAP = {
        KagQueryType.PERSONALIZED_MATCH: PERSONALIZED_MATCH,
        KagQueryType.SIMILAR_TASTE: SIMILAR_TASTE,
        KagQueryType.SAFE_DISCOVERY: SAFE_DISCOVERY,
        KagQueryType.NEW_RELEASE: NEW_RELEASE,
        KagQueryType.MOOD_BASED: MOOD_BASED,
        KagQueryType.INFORMATION_RELATED: INFORMATION_RELATED,
    }

    ##################### 타입별 정첵 값 매핑 조회 ####################
    @classmethod
    def get(cls, query_type: KagQueryType) -> KagQueryPolicy:
        """
        쿼리 타입을 입력받아 해당 쿼리 타입에 맞는 쿼리 정책을 반환한다.
        """
        try:
            return cls.MAP[query_type]
        except KeyError as exc:
            raise ValueError(f"지원하지 않는 KagQueryType 입니다: {query_type}") from exc