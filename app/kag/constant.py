"""KAG용 primary_goal·카테고리·라우팅. `primary_goal`은 스키마 IntentType 문자열과 1:1 동일하다."""

from __future__ import annotations

from typing import ClassVar, get_args

from app.schemas.intent_state_schema import IntentType

####################################################################
# IntentType ↔ primary_goal (동일 집합, 1:1)
####################################################################
_INTENT_VALUES = frozenset(get_args(IntentType))
_INTENT_TYPE_TO_PRIMARY_GOAL: dict[str, str] = {t: t for t in _INTENT_VALUES}

if frozenset(_INTENT_TYPE_TO_PRIMARY_GOAL.keys()) != _INTENT_VALUES:
    raise RuntimeError("IntentType 정의와 1:1 매핑 생성 불일치")
if not all(k == v for k, v in _INTENT_TYPE_TO_PRIMARY_GOAL.items()):
    raise RuntimeError("primary_goal은 intent_type과 동일 문자열이어야 합니다.")

DEFAULT_PRIMARY_GOAL = "personalized_recommendation"


def _assert_primary_goal_maps_intent_types(cat: dict[str, str], routes: dict[str, str]) -> None:
    if frozenset(cat.keys()) != _INTENT_VALUES or frozenset(routes.keys()) != _INTENT_VALUES:
        raise RuntimeError(
            "PRIMARY_GOAL_TO_*는 IntentType 전원과 키가 일치해야 합니다. "
            f"intent={sorted(_INTENT_VALUES)} category_keys={sorted(cat)} route_keys={sorted(routes)}"
        )


class KagGraphConstants:
    """그래프/계약 문자열·intent(primary_goal)별 카테고리·라우트 매핑."""

    RECOMMENDATION_CATEGORY_NEW_RELEASE = "new_release"
    RECOMMENDATION_CATEGORY_DISCOVERY_CANDIDATE = "discovery_candidate"
    RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH = "personalized_match"
    RECOMMENDATION_CATEGORY_INFORMATION_RELATED = "information_related"

    ROUTE_NEW_RELEASE = "new_release"
    ROUTE_SAFE_DISCOVERY = "safe_discovery"
    ROUTE_PERSONALIZED = "personalized"

    TARGET_SECTION_NEW_RELEASE = "new_release_section"
    TARGET_SECTION_DISCOVERY = "discovery_section"
    TARGET_SECTION_PERSONALIZED = "personalized_section"

    # intent_type == primary_goal 이므로 키는 IntentType 멤버와 동일
    INTENT_TYPE_TO_PRIMARY_GOAL: ClassVar[dict[str, str]] = dict(_INTENT_TYPE_TO_PRIMARY_GOAL)

    PRIMARY_GOAL_TO_RECOMMENDATION_CATEGORY: ClassVar[dict[str, str]] = {
        "personalized_recommendation": RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH,
        "new_release_recommendation": RECOMMENDATION_CATEGORY_NEW_RELEASE,
        "discovery_recommendation": RECOMMENDATION_CATEGORY_DISCOVERY_CANDIDATE,
        "music_information": RECOMMENDATION_CATEGORY_INFORMATION_RELATED,
        "recommendation_reason": RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH,
        "general_chat": RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH,
    }

    PRIMARY_GOAL_TO_ROUTE: ClassVar[dict[str, str]] = {
        "personalized_recommendation": ROUTE_PERSONALIZED,
        "new_release_recommendation": ROUTE_NEW_RELEASE,
        "discovery_recommendation": ROUTE_SAFE_DISCOVERY,
        "music_information": ROUTE_SAFE_DISCOVERY,
        "recommendation_reason": ROUTE_PERSONALIZED,
        "general_chat": ROUTE_PERSONALIZED,
    }

    CATEGORY_TO_TARGET_SECTION: ClassVar[dict[str, str]] = {
        RECOMMENDATION_CATEGORY_NEW_RELEASE: TARGET_SECTION_NEW_RELEASE,
        RECOMMENDATION_CATEGORY_DISCOVERY_CANDIDATE: TARGET_SECTION_DISCOVERY,
        RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH: TARGET_SECTION_PERSONALIZED,
        RECOMMENDATION_CATEGORY_INFORMATION_RELATED: TARGET_SECTION_PERSONALIZED,
    }

    @classmethod
    def primary_goal_from_intent_type(cls, intent_type: str | None) -> str:
        if not intent_type:
            return DEFAULT_PRIMARY_GOAL
        if intent_type in _INTENT_VALUES:
            return intent_type
        return DEFAULT_PRIMARY_GOAL

    @classmethod
    def recommendation_category_for_primary_goal(cls, primary_goal: str) -> str:
        return cls.PRIMARY_GOAL_TO_RECOMMENDATION_CATEGORY.get(
            primary_goal,
            cls.RECOMMENDATION_CATEGORY_PERSONALIZED_MATCH,
        )

    @classmethod
    def route_for_primary_goal(cls, primary_goal: str) -> str:
        return cls.PRIMARY_GOAL_TO_ROUTE.get(primary_goal, cls.ROUTE_PERSONALIZED)

    @classmethod
    def target_section_for_category(cls, category: str) -> str:
        return cls.CATEGORY_TO_TARGET_SECTION.get(category, cls.TARGET_SECTION_PERSONALIZED)


_assert_primary_goal_maps_intent_types(
    KagGraphConstants.PRIMARY_GOAL_TO_RECOMMENDATION_CATEGORY,
    KagGraphConstants.PRIMARY_GOAL_TO_ROUTE,
)


class KagSessionInput:
    """`session_context`에 실린 외부 입력만 사용한다. 기대 형식은 `kag_input.json`의 `kag_input_json` 과 동일."""

    KAG_INPUT_JSON_KEY = "kag_input_json"

    def __init__(self, session_context: dict | None) -> None:
        raw = (session_context or {}).get(self.KAG_INPUT_JSON_KEY)
        self._kag_input: dict = raw if isinstance(raw, dict) else {}
        self._primary_goal_cached: str | None = None

    def kag_input_json(self) -> dict:
        """외부에서 받은 KagInputSchema.model_dump()와 동등한 내용(dict 얕은 복사)."""
        return dict(self._kag_input)

    def intent_type(self) -> str | None:
        raw = self._kag_input.get("intent_type")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return None

    def primary_goal(self) -> str:
        if self._primary_goal_cached is None:
            self._primary_goal_cached = KagGraphConstants.primary_goal_from_intent_type(
                self.intent_type(),
            )
        return self._primary_goal_cached

    def recommendation_category(self) -> str:
        return KagGraphConstants.recommendation_category_for_primary_goal(self.primary_goal())

    def route(self) -> str:
        return KagGraphConstants.route_for_primary_goal(self.primary_goal())

    def target_section(self) -> str:
        return KagGraphConstants.target_section_for_category(self.recommendation_category())
