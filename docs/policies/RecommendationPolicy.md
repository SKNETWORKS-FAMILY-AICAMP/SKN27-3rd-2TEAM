# Recommendation Policy

구현 기준: `app/policies/recommendation_policy.py`

---

## 목적

RecommendationAgent가 RAG evidence에서 최종 추천 목록을 선택할 때 따르는 정책을 정의한다.

---

## 카테고리 섹션 매핑

| recommendation_category | 프론트 섹션 |
|------------------------|------------|
| personalized_match     | personalized |
| discovery_candidate    | discovery    |
| new_release            | new_release  |

---

## 기본 카테고리 우선순위

intent_type별로 우선 노출 카테고리가 다르다.

| intent_type                  | 우선순위 |
|-----------------------------|---------|
| personalized_recommendation  | personalized_match → discovery_candidate → new_release |
| recommendation_reason        | personalized_match → discovery_candidate → new_release |
| music_information            | personalized_match → discovery_candidate → new_release |
| general_chat                 | personalized_match → discovery_candidate → new_release |
| new_release_recommendation   | new_release → personalized_match → discovery_candidate |
| discovery_recommendation     | discovery_candidate → personalized_match → new_release |

---

## 선택 제한

- 최대 선택 수: **5곡** (`MAX_SELECTED_RECOMMENDATIONS`)
- 기본 섹션: `personalized`

---

## 판단 기준

1. intent_type에 따른 카테고리 우선순위를 적용한다.
2. 우선순위가 높은 카테고리의 evidence를 먼저 채운다.
3. 5곡 한도 내에서 다음 카테고리로 넘어간다.
4. RAG evidence가 없는 카테고리는 건너뛴다.

---

## 금지 사항

- LLM이 추천 후보 순서를 변경하거나 content_id를 생성하지 않는다.
- 카테고리 외 임의 섹션을 생성하지 않는다.
- 5곡 초과 선택 금지.

---

## 운영 관점

- 추천 결과가 0곡이면 Orchestrator가 fallback response를 반환한다.
- 카테고리 우선순위 변경은 이 문서와 `recommendation_policy.py`를 동시에 수정한다.
