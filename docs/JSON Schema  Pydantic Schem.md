# RIMAS JSON Schema / Pydantic Schema 상세 설계 v1

---

# 1. 문서 목적

본 문서는 RIMAS v2 구현을 위한 JSON 계약과 Pydantic Schema 기준을 정의한다.

이 문서는 다음 구현의 기준이 된다.

- ML Output Schema
- KAG_STATE Schema
- RAG_STATE Schema
- Intent Result Schema
- Curation Plan Schema
- Selected Recommendations Schema
- Response State Schema
- Interaction Log Schema

---

# 2. 공통 상태값

## Status Literal

허용값:
- success
- partial_match
- empty_result
- timeout
- error

Pydantic 기준:

Status = Literal[
    "success",
    "partial_match",
    "empty_result",
    "timeout",
    "error"
]

---

# 3. ML Output Schema

## 목적

사용자 기반 추천에 필요한 취향/행동/추천 준비 상태를 제공한다.

## JSON 예시

{
  "status": "success",
  "user_id": "user_001",
  "taste_profile": {
    "preferred_genres": ["rnb", "indie"],
    "preferred_artists": ["artist_a", "artist_b"],
    "preferred_moods": ["calm", "night"],
    "preferred_tempo": "medium"
  },
  "behavior_profile": {
    "recent_listening_level": "medium",
    "recent_discovery_level": "low",
    "repeat_listening_ratio": 0.72,
    "new_artist_acceptance": 0.34
  },
  "recommendation_profile": {
    "personalization_strength": "high",
    "discovery_readiness": "medium",
    "new_release_affinity": "medium"
  }
}

## Pydantic Schema

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

Status = Literal["success", "partial_match", "empty_result", "timeout", "error"]

Level = Literal["low", "medium", "high"]
Tempo = Literal["slow", "medium", "fast", "unknown"]

class TasteProfile(BaseModel):
    preferred_genres: List[str] = Field(default_factory=list)
    preferred_artists: List[str] = Field(default_factory=list)
    preferred_moods: List[str] = Field(default_factory=list)
    preferred_tempo: Tempo = "unknown"

class BehaviorProfile(BaseModel):
    recent_listening_level: Level
    recent_discovery_level: Level
    repeat_listening_ratio: float = Field(ge=0.0, le=1.0)
    new_artist_acceptance: float = Field(ge=0.0, le=1.0)

class RecommendationProfile(BaseModel):
    personalization_strength: Level
    discovery_readiness: Level
    new_release_affinity: Level

class MlOutput(BaseModel):
    status: Status
    user_id: str
    taste_profile: TasteProfile
    behavior_profile: BehaviorProfile
    recommendation_profile: RecommendationProfile

---

# 4. KAG_STATE Schema

## 목적

KAG_STATE는 사용자 상태와 입력을 기반으로 추천 방향, 큐레이션 전략, UI 라우팅을 결정한다.

KAG_STATE는 실제 추천 곡을 생성하지 않는다.

## JSON 예시

{
  "status": "success",
  "user": {
    "user_id": "user_001"
  },
  "recommendation_goal": {
    "primary_goal": "new_taste_discovery",
    "secondary_goal": "personalized_recommendation",
    "goal_reason": "사용자의 기존 취향을 유지하면서 새로운 취향 탐색 가능성이 있음"
  },
  "user_context": {
    "base_preference": {
      "genres": ["rnb", "indie"],
      "moods": ["calm", "night"],
      "tempo": "medium"
    },
    "behavior_context": {
      "recent_listening_level": "medium",
      "recent_discovery_level": "low",
      "repeat_listening_ratio": 0.72,
      "new_artist_acceptance": 0.34
    }
  },
  "curation_intent": {
    "intent_type": "new_taste_discovery",
    "intent_confidence": 0.86,
    "allowed_modes": [
      "personalized_recommendation",
      "new_taste_discovery",
      "similar_taste_recommendation"
    ]
  },
  "curation_strategy": {
    "strategy_code": "SAFE_DISCOVERY_FROM_PERSONAL_TASTE",
    "strategy_level": "medium",
    "strategy_description_for_internal": "기존 취향과 연결되는 안전한 새 취향 탐색"
  },
  "content_requirements": {
    "must_include": ["personalized_match", "discovery_candidate"],
    "optional_include": ["new_release"],
    "avoid": ["too_aggressive_genre_shift"]
  },
  "routing": {
    "target_page": "main_recommendation_page",
    "primary_section": "discovery_section",
    "secondary_sections": [
      "personalized_recommendation_section",
      "new_release_section"
    ]
  },
  "selected_path": "personalized_to_safe_discovery"
}

## Pydantic Schema

RecommendationGoalType = Literal[
    "personalized_recommendation",
    "new_release_recommendation",
    "new_taste_discovery",
    "similar_taste_recommendation",
    "music_information",
    "recommendation_reason"
]

RecommendationCategory = Literal[
    "personalized_match",
    "similar_taste",
    "new_release",
    "discovery_candidate",
    "information_related"
]

TargetPage = Literal[
    "main_recommendation_page",
    "chatbot_page"
]

UiSection = Literal[
    "personalized_recommendation_section",
    "new_release_section",
    "discovery_section",
    "information_answer_section"
]

class KagUser(BaseModel):
    user_id: str

class RecommendationGoal(BaseModel):
    primary_goal: RecommendationGoalType
    secondary_goal: Optional[RecommendationGoalType] = None
    goal_reason: str

class KagBasePreference(BaseModel):
    genres: List[str] = Field(default_factory=list)
    moods: List[str] = Field(default_factory=list)
    tempo: Tempo = "unknown"

class KagBehaviorContext(BaseModel):
    recent_listening_level: Level
    recent_discovery_level: Level
    repeat_listening_ratio: float = Field(ge=0.0, le=1.0)
    new_artist_acceptance: float = Field(ge=0.0, le=1.0)

class KagUserContext(BaseModel):
    base_preference: KagBasePreference
    behavior_context: KagBehaviorContext

class CurationIntent(BaseModel):
    intent_type: RecommendationGoalType
    intent_confidence: float = Field(ge=0.0, le=1.0)
    allowed_modes: List[RecommendationGoalType]

class CurationStrategy(BaseModel):
    strategy_code: str
    strategy_level: Level
    strategy_description_for_internal: str

class ContentRequirements(BaseModel):
    must_include: List[RecommendationCategory] = Field(default_factory=list)
    optional_include: List[RecommendationCategory] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)

class Routing(BaseModel):
    target_page: TargetPage
    primary_section: UiSection
    secondary_sections: List[UiSection] = Field(default_factory=list)

class KagState(BaseModel):
    status: Status
    user: KagUser
    recommendation_goal: RecommendationGoal
    user_context: KagUserContext
    curation_intent: CurationIntent
    curation_strategy: CurationStrategy
    content_requirements: ContentRequirements
    routing: Routing
    selected_path: str

---

# 5. RAG_STATE Schema

## 목적

RAG_STATE는 추천 후보와 설명 근거를 제공한다.

RAG_STATE는 KAG_STATE가 결정한 추천 방향을 기반으로 콘텐츠 후보를 반환한다.

## JSON 예시

{
  "status": "success",
  "recommendation_context": {
    "context_type": "new_taste_discovery",
    "base_context": "사용자의 기존 rnb/indie 취향과 calm/night 분위기를 기준으로 안전한 취향 확장 후보를 제공",
    "source_type": "mock_music_catalog"
  },
  "recommended_content_evidence": [
    {
      "content_id": "track_001",
      "title": "Midnight Loop",
      "artist": "Nova Lane",
      "album": "Night Sketch",
      "genre": ["rnb", "indie"],
      "mood": ["calm", "night"],
      "tempo": "medium",
      "release_type": "existing_catalog",
      "recommendation_category": "personalized_match",
      "evidence_summary": "사용자의 기존 rnb/indie 취향과 calm/night 분위기에 직접적으로 연결되는 곡",
      "match_reason": {
        "genre_match": true,
        "mood_match": true,
        "tempo_match": true,
        "new_taste_expansion": false
      }
    }
  ],
  "recommendation_reason": {
    "summary": "기존 개인화 추천을 기본으로 유지하면서, 부담 없는 새 취향 후보와 최신 업데이트 곡을 함께 구성함",
    "reason_items": [
      "기존 rnb/indie 취향과 연결되는 곡을 포함함"
    ]
  },
  "information_evidence": [
    {
      "info_id": "genre_dream_pop_001",
      "info_type": "genre",
      "title": "dream_pop",
      "summary": "부드러운 사운드와 몽환적인 분위기가 특징인 장르"
    }
  ],
  "recommendation_scripts": {
    "dj_intro": "기존에 좋아하던 분위기는 유지하면서, 살짝 새로운 결의 음악도 함께 골라봤어요.",
    "personalized_message": "먼저 익숙하게 들을 수 있는 곡을 추천드릴게요.",
    "new_release_message": "최근 업데이트된 곡 중에서도 취향과 연결되는 곡을 함께 넣었어요.",
    "discovery_message": "새로운 취향을 시도하고 싶다면 이 곡부터 시작해볼 수 있어요.",
    "fallback_message": "지금은 충분한 추천 근거가 부족해서 기본 안내만 제공할게요."
  }
}

## Pydantic Schema

ReleaseType = Literal[
    "existing_catalog",
    "new_release",
    "updated_playlist",
    "unknown"
]

InfoType = Literal[
    "track",
    "artist",
    "genre",
    "playlist",
    "mood",
    "general"
]

class RecommendationContext(BaseModel):
    context_type: RecommendationGoalType
    base_context: str
    source_type: str

class MatchReason(BaseModel):
    genre_match: bool
    mood_match: bool
    tempo_match: bool
    new_taste_expansion: bool

class RecommendedContentEvidence(BaseModel):
    content_id: str
    title: str
    artist: str
    album: Optional[str] = None
    genre: List[str] = Field(default_factory=list)
    mood: List[str] = Field(default_factory=list)
    tempo: Tempo = "unknown"
    release_type: ReleaseType = "unknown"
    recommendation_category: RecommendationCategory
    evidence_summary: str
    match_reason: MatchReason

class RecommendationReason(BaseModel):
    summary: str
    reason_items: List[str] = Field(default_factory=list)

class InformationEvidence(BaseModel):
    info_id: str
    info_type: InfoType
    title: str
    summary: str

class RecommendationScripts(BaseModel):
    dj_intro: str
    personalized_message: str
    new_release_message: str
    discovery_message: str
    fallback_message: str

class RagState(BaseModel):
    status: Status
    recommendation_context: RecommendationContext
    recommended_content_evidence: List[RecommendedContentEvidence]
    recommendation_reason: RecommendationReason
    information_evidence: List[InformationEvidence] = Field(default_factory=list)
    recommendation_scripts: RecommendationScripts

---

# 6. Intent Result Schema

## 목적

Intent Agent의 출력 계약이다.

## JSON 예시

{
  "status": "success",
  "intent_type": "recommendation_reason_question",
  "confidence": 0.91,
  "target_content_id": "track_002",
  "requires_recommendation": false,
  "requires_information": true
}

## Pydantic Schema

IntentType = Literal[
    "personalized_recommendation",
    "new_release_recommendation",
    "new_taste_discovery",
    "similar_taste_recommendation",
    "music_information_question",
    "recommendation_reason_question",
    "general_chat"
]

class IntentResult(BaseModel):
    status: Status
    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    target_content_id: Optional[str] = None
    requires_recommendation: bool
    requires_information: bool

---

# 7. Curation Plan Schema

## 목적

Curation Agent의 출력 계약이다.

## JSON 예시

{
  "status": "success",
  "curation_mode": "explain_recommendation_reason",
  "response_focus": "discovery_candidate",
  "tone": "friendly_dj",
  "allowed_content_ids": ["track_001", "track_002", "track_003"],
  "primary_content_id": "track_002",
  "use_information_evidence": true
}

## Pydantic Schema

CurationMode = Literal[
    "recommend_personalized",
    "recommend_new_release",
    "recommend_discovery",
    "explain_recommendation_reason",
    "explain_music_information",
    "general_curator_response",
    "fallback"
]

ResponseTone = Literal[
    "friendly_dj",
    "calm_curator",
    "concise",
    "fallback"
]

class CurationPlan(BaseModel):
    status: Status
    curation_mode: CurationMode
    response_focus: Optional[RecommendationCategory] = None
    tone: ResponseTone
    allowed_content_ids: List[str] = Field(default_factory=list)
    primary_content_id: Optional[str] = None
    use_information_evidence: bool = False

---

# 8. Selected Recommendations Schema

## 목적

Recommendation Agent가 최종 응답과 UI 표시 대상으로 선택한 추천 목록 계약이다.

## JSON 예시

{
  "status": "success",
  "selected_recommendations": [
    {
      "content_id": "track_002",
      "title": "Soft Orbit",
      "artist": "Luna Field",
      "recommendation_category": "discovery_candidate",
      "display_reason": "기존 calm/night 분위기와 연결되면서 dream_pop 계열로 취향을 넓혀볼 수 있는 곡"
    }
  ]
}

## Pydantic Schema

class SelectedRecommendation(BaseModel):
    content_id: str
    title: str
    artist: str
    recommendation_category: RecommendationCategory
    display_reason: str

class SelectedRecommendationsResult(BaseModel):
    status: Status
    selected_recommendations: List[SelectedRecommendation] = Field(default_factory=list)

검증 규칙:
- content_id는 RAG_STATE.recommended_content_evidence에 존재해야 한다.
- title은 RAG_STATE의 title과 동일해야 한다.
- artist는 RAG_STATE의 artist와 동일해야 한다.
- display_reason은 RAG evidence_summary 또는 recommendation_reason 기반이어야 한다.

---

# 9. Response State Schema

## 목적

LLM Response Generator의 최종 출력 계약이다.

## JSON 예시

{
  "status": "success",
  "response_type": "curator_recommendation",
  "chatbot_response": "기존에 좋아하던 차분한 밤 분위기는 유지하면서, 조금 새로운 결로 넘어갈 수 있는 곡으로 Luna Field의 Soft Orbit을 추천드릴게요.",
  "display_recommendations": [
    {
      "content_id": "track_002",
      "title": "Soft Orbit",
      "artist": "Luna Field",
      "label": "새로운 취향 시도",
      "display_reason": "기존 calm/night 분위기와 연결되면서 dream_pop 계열로 취향을 넓혀볼 수 있는 곡"
    }
  ],
  "used_content_ids": ["track_002"],
  "provenance": {
    "used_ml_fields": [
      "taste_profile.preferred_genres",
      "taste_profile.preferred_moods"
    ],
    "used_kag_fields": [
      "recommendation_goal.primary_goal",
      "curation_intent.intent_type"
    ],
    "used_rag_content_ids": ["track_002"],
    "used_rag_fields": [
      "recommended_content_evidence.evidence_summary",
      "recommendation_reason.summary"
    ]
  },
  "validation": {
    "response_validation_passed": true,
    "provenance_validation_passed": true
  }
}

## Pydantic Schema

ResponseType = Literal[
    "curator_recommendation",
    "curator_information",
    "recommendation_reason",
    "fallback"
]

class DisplayRecommendation(BaseModel):
    content_id: str
    title: str
    artist: str
    label: str
    display_reason: str

class Provenance(BaseModel):
    used_ml_fields: List[str] = Field(default_factory=list)
    used_kag_fields: List[str] = Field(default_factory=list)
    used_rag_content_ids: List[str] = Field(default_factory=list)
    used_rag_fields: List[str] = Field(default_factory=list)

class ValidationResult(BaseModel):
    response_validation_passed: bool
    provenance_validation_passed: bool

class ResponseState(BaseModel):
    status: Status
    response_type: ResponseType
    chatbot_response: str
    display_recommendations: List[DisplayRecommendation] = Field(default_factory=list)
    used_content_ids: List[str] = Field(default_factory=list)
    provenance: Provenance
    validation: ValidationResult

---

# 10. Interaction Log Schema

## 목적

DB 저장을 위한 로그 계약이다.

## JSON 예시

{
  "log_id": "log_20260504_0001",
  "user_id": "user_001",
  "user_input": "새로운 취향으로 들을만한 노래 추천해줘",
  "ml_output": {},
  "kag_state": {},
  "rag_state": {},
  "response_state": {},
  "validation_status": "success",
  "error_type": null,
  "latency_ms": 1420,
  "created_at": "2026-05-04T19:30:00+09:00"
}

## Pydantic Schema

ValidationStatus = Literal[
    "success",
    "failed",
    "fallback"
]

ErrorType = Literal[
    "ML_OUTPUT_NOT_FOUND",
    "KAG_STATE_ERROR",
    "RAG_STATE_ERROR",
    "CONTRACT_VALIDATION_FAILED",
    "LLM_CALL_FAILED",
    "RESPONSE_VALIDATION_FAILED",
    "PROVENANCE_VALIDATION_FAILED",
    "UNKNOWN_ERROR"
]

from datetime import datetime
from typing import Any, Dict

class InteractionLog(BaseModel):
    log_id: str
    user_id: str
    user_input: Optional[str] = None
    ml_output: Optional[Dict[str, Any]] = None
    kag_state: Optional[Dict[str, Any]] = None
    rag_state: Optional[Dict[str, Any]] = None
    response_state: Optional[Dict[str, Any]] = None
    validation_status: ValidationStatus
    error_type: Optional[ErrorType] = None
    latency_ms: Optional[int] = None
    created_at: datetime

---

# 11. Validator 구현 규칙

## 11.1 Contract Validator

검증 대상:
- MlOutput
- KagState
- RagState

검증 실패 시:
- LLM 실행 금지
- fallback 응답 생성
- interaction_logs 저장

## 11.2 Response Validator

검증 대상:
- ResponseState

검증 실패 조건:
- chatbot_response 없음
- status 허용값 위반
- display_recommendations 구조 오류
- used_content_ids 타입 오류

## 11.3 Provenance Validator

검증 대상:
- ResponseState
- RagState
- KagState
- MlOutput

검증 규칙:
- ResponseState.used_content_ids는 RagState.recommended_content_evidence.content_id 안에 있어야 한다.
- display_recommendations.title은 RAG title과 일치해야 한다.
- display_recommendations.artist는 RAG artist와 일치해야 한다.
- RAG_STATE에 없는 content_id가 있으면 실패한다.
- 내부 전략 코드가 chatbot_response에 직접 노출되면 실패한다.
- ML Output은 LLM 전후 동일해야 한다.

---

# 12. 구현 파일 매핑

schemas/
  common_schema.py
  ml_output_schema.py
  kag_state_schema.py
  rag_state_schema.py
  intent_result_schema.py
  curation_plan_schema.py
  selected_recommendation_schema.py
  response_state_schema.py
  interaction_log_schema.py

validators/
  contract_validator.py
  response_validator.py
  provenance_validator.py

contracts/
  ml_output_example.json
  kag_state_example.json
  rag_state_example.json
  intent_result_example.json
  curation_plan_example.json
  selected_recommendations_example.json
  response_state_example.json
  interaction_log_example.json

---

# 13. 최종 완료 기준

- 모든 Schema가 Pydantic으로 정의된다.
- 모든 Mock JSON이 Schema 검증을 통과한다.
- Contract Validator가 ML/KAG/RAG 구조 오류를 잡는다.
- Response Validator가 LLM 응답 구조 오류를 잡는다.
- Provenance Validator가 RAG에 없는 추천 생성을 막는다.
- Interaction Log Schema가 DB 저장 구조와 일치한다.