# RIMAS Final Implementation Direction

작성 기준:

- 기준 설계서: `docs/rimas_v_4_integrated_design_updated_final_.md`
- 현재 구현 상태: 선택지 C, 단계적 설계 정렬 적용 중
- 목적: 이후 구현이 임의 해석으로 흐르지 않도록 최종 방향과 보류 결정을 고정한다.

---

## 1. Redis / Session Flush Policy

### 최종 선택

- Redis flush와 `interaction_logs` 관리를 분리한다.
- 기본값은 `interaction_logs` 보존이다.

### 정책

- flush API 기본 동작:
  - Redis session history를 PostgreSQL `chat_sessions`, `chat_session_turns`에 저장한다.
  - 저장 성공 후 Redis session history/context를 삭제한다.
  - `interaction_logs`는 삭제하지 않는다.

- 옵션:
  - `flush_logs=true`인 경우에만 `interaction_logs` 삭제를 허용할 수 있다.
  - 단, 삭제 범위는 구현 전에 `session_id`, `user_id`, `request_id` 중 무엇을 기준으로 할지 확정해야 한다.

### 이유

- 운영 로그는 감사, 디버깅, 회귀 분석 가치가 높다.
- 테스트 환경에서는 선택적으로 로그 초기화가 필요할 수 있다.
- 운영 안정성과 개발 편의성을 동시에 유지한다.

### 추가 정책

- flush 수행 시 request_id 기준 trace 로그를 남긴다.
- 현재 flush 구현 범위:
  - Redis conversation history
  - Redis session context
  - PostgreSQL `chat_sessions`
  - PostgreSQL `chat_session_turns`

### 향후 flush 또는 snapshot 대상

- latest `KAG_STATE`
- latest `RAG_STATE`
- latest `RESPONSE_STATE`
- recommendation metadata
- response cache

위 항목은 현재 명확한 Redis key로 분리되어 있지 않으므로, 구현 전에 Redis key structure를 먼저 확정한다.

---

## 2. Redis TTL / Auto Flush Policy

### 최종 선택

- Redis TTL 단독 의존을 금지한다.
- 요청 종료 시 필요한 compact summary/state를 영속 저장할 수 있도록 구성한다.
- 세션 flush는 명시적 flush API 또는 세션 종료 시점에 수행한다.

### 정책

- 추천 응답 완료 후 저장 가능 대상:
  - session summary
  - latest `RAG_STATE`
  - latest `KAG_STATE`
  - recommendation metadata

- Redis TTL:
  - 캐시 만료 용도
  - 영속 저장소 역할 금지

### 비채택

- Celery 또는 Background Scheduler 기반 TTL sweep은 현재 단계에서 제외한다.

---

## 3. Redis 장애 대응 정책

### 최종 선택

- Stateless fallback을 허용한다.

### 정책

- Redis 연결 실패 시:
  - recommendation flow는 계속 진행한다.
  - session 기반 personalization 일부를 비활성화할 수 있다.
  - response에 degraded 상태를 포함할 수 있다.

예시:

```json
{
  "session_degraded": true
}
```

### 구현 전 확인 필요

`session_degraded`를 API wrapper에 둘지, `RESPONSE_STATE` 내부에 둘지 contract를 확정해야 한다.

### 금지

- Redis 장애 때문에 recommendation 전체를 실패시키지 않는다.

---

## 4. Real KAG Adapter Direction

### 최종 선택

- Interface/schema를 먼저 고정한다.
- 이후 최소 Neo4j traversal을 구현한다.

### 우선 구현 범위

```text
user/profile/preferences
-> genre/tag/mood/artist
-> candidate tracks
```

### 현재 Mock 유지 목적

- 다른 모듈 병렬 개발 가능
- ResponseGenerator 계약 안정화
- Real adapter 구현 전 contract 회귀 방지

### KAG_STATE 확장 후보

- `traversal_reason`
- `matched_nodes`
- `excluded_nodes`
- `candidate_tracks`
- `diversity_metadata`

### 구현 전 확인 필요

현재 `KagStateSchema`는 단순 구조다. 위 필드를 추가하려면 schema, validator, compact state 정책을 먼저 확정한다.

---

## 5. Real RAG Adapter Direction

### 최종 선택

- 최소 Elasticsearch retrieval을 먼저 구현한다.
- Hybrid retrieval은 후순위로 둔다.

### 초기 retrieval 기준

- title
- artist
- mood
- metadata
- evidence_text

### RAG_STATE 방향

기존 호환을 위해 현재 필드를 유지하면서 metadata를 확장한다.

```json
{
  "status": "success",
  "query": "사용자 원문 또는 검색 쿼리",
  "normalized_query": "정규화된 검색 쿼리",
  "recommended_content_evidence": [],
  "recommendation_reason": {},
  "retrieval_metadata": {}
}
```

### 목표

- recommendation explanation 안정화
- Music Detail fallback 개선
- RAG evidence 기반 provenance validation 강화

---

## 6. LLM Input Planner Policy

### 최종 선택

- LLM planning을 허용한다.
- 단, enum/schema 밖 출력은 금지한다.

### 중요 원칙

- LLM은 해석만 수행한다.
- 시스템 권한은 deterministic validator가 가진다.
- LLM은 `KAG_STATE`, `RAG_STATE`, 추천 후보, content_id, title, artist를 생성하지 않는다.

### 목표 폴더 구조

```text
app/
  prompts/
    input_planner_prompt.py
    response_generator_prompt.py
    critique_prompt.py

  llm/
    provider.py
    parser.py
    schemas.py
    validators.py
    prompt_executor.py
```

### LLM Output 정책

- parser 검증 필수
- enum 외 값 reject
- schema validation 실패 시 fallback planner 사용 가능

---

## 7. Music Detail Extension Direction

### 최종 선택

- 최근 `RAG_STATE`를 Redis/session에서 가져오는 방식을 채택한다.

### 이유

- recommendation 시점의 evidence와 detail 시점의 explanation 일관성을 유지한다.

### Detail 우선순위

1. latest `RAG_STATE` evidence
2. `music_catalog` fallback
3. minimal metadata response

### 현재 제외

- 내 취향과 얼마나 맞는지
- 유사도 점수 explanation
- personality profiling

위 기능은 별도 승인 후 진행한다.

---

## 8. detail_view_logs Policy

### 최종 선택

- 최소 로그 저장을 적용한다.

### 저장 항목

- `user_id`
- `request_id`
- `track_id`
- `viewed_at`
- `source_type`
- `recommendation_context` optional

### 목표

- recommendation feedback loop 준비
- future analytics 기반 확보

### 구현 전 확인 필요

현재 Music Detail API는 `user_id`, `request_id`를 필수로 받지 않는다. 로그 저장을 구현하려면 API request contract 확장이 필요하다.

---

## 9. Policy Documents Direction

### 최종 선택

- Markdown 정책 문서와 Python 정책 구현을 병행한다.

### 필수 문서

```text
docs/policies/
  RecommendationPolicy.md
  RankingPolicy.md
  PromptPolicy.md
```

### 원칙

- Markdown:
  - 정책 의도
  - 판단 기준
  - 금지 사항
  - 운영/테스트 관점 설명

- Python:
  - 실제 실행 로직
  - 테스트 가능한 상수/함수
  - Agent가 직접 사용하는 정책

### 금지

- 정책이 코드에만 존재하는 상태 유지 금지

---

## 10. Runtime Settings / Security Policy

### 최종 선택

- 환경별 fail-fast 정책을 적용한다.

### 환경

- `local`
- `dev`
- `prod`

### 정책

- local:
  - 일부 default 허용 가능

- prod:
  - 필수 env 누락 시 즉시 실행 실패

### 필수 fail-fast 대상

- DB password
- Neo4j password
- OpenAI key
- provider config
- CORS settings
- external API secrets

### 금지

- 운영 환경에서 insecure default 허용 금지

---

## 11. data / seed Role Policy

### 최종 선택

- 역할 분리를 유지한다.

### 구조

```text
data/
  processed/
    실제 가공 데이터
    matched_spotify_enriched.csv 등

seed/
  앱 초기 적재용
  csv/json seed 데이터

db/
  seed.sql
  최소 mock/development seed
```

### 원칙

- processed data와 development seed 역할을 분리한다.
- `db/seed.sql`은 최소 개발/테스트 seed로 유지한다.
- 실제 가공 데이터 적재 경로는 별도 로더 또는 adapter 구현 단계에서 확정한다.

---

## 12. Frontend request_id Policy

### 최종 선택

- `request_id`는 optional로 유지한다.
- Frontend 생성은 권장한다.

### 정책

- Frontend:
  - UUID 생성 가능
  - React Query retry 또는 refetch와 결합 가능

- Backend:
  - request_id가 없으면 기존 호출을 허용한다.
  - request_id가 있으면 lifecycle cache로 중복 요청을 차단한다.

### 목표

- React Query retry 대응
- 중복 요청 차단
- recommendation lifecycle cache 연결

---

## 13. Frontend + Backend Cache Policy

### 최종 선택

- React Query cache와 Backend lifecycle cache를 공존시킨다.

### Frontend 책임

- UI fetch dedupe
- stale 관리
- retry 정책 관리

### Backend 책임

- request_id 기반 idempotency
- recommendation cache
- duplicate prevention

### 금지

- UI만으로 중복 요청 방지 책임 전가 금지

---

## 14. README / Design Document Sync Policy

### 필수 반영 대상

- `app/core`
- `app/policies`
- Redis key structure
- request_id lifecycle
- Music Detail fallback
- session degraded mode
- KAG/RAG state usage
- flush API usage

### 원칙

- README와 실제 구조 불일치 상태를 방치하지 않는다.
- 설계 문서와 실제 구현이 다를 경우, 구현 승인 문서에 근거를 남긴다.

---

## 15. Final Implementation Order

### PHASE 1

- `KAG_STATE` / `RAG_STATE` schema 확정
- Redis key structure 확정
- `session_degraded` contract 확정
- `flush_logs=true` 범위 확정

### PHASE 2

- Redis/session flush 보강
- latest KAG/RAG/response metadata 저장 구조 추가

### PHASE 3

- 정책 문서 작성
  - `RecommendationPolicy.md`
  - `RankingPolicy.md`
  - `PromptPolicy.md`

### PHASE 4

- Real RAG Adapter 최소 구현
- Elasticsearch retrieval 연결

### PHASE 5

- Real KAG Adapter 최소 구현
- Neo4j traversal 연결

### PHASE 6

- Music Detail recent `RAG_STATE` 연결
- `detail_view_logs` 저장

### PHASE 7

- `settings.py` fail-fast 적용
- README / 설계 문서 동기화

### PHASE 8

- Frontend request_id / React Query 연동

---

## 16. Core Architecture Principles

- LLM은 해석만 수행한다.
- 최종 시스템 권한은 deterministic validator가 가진다.
- UI는 판단하지 않는다.
- recommendation 결정은 backend가 수행한다.
- Redis는 cache/session layer이다.
- Redis는 영속 저장소 역할을 하지 않는다.
- recommendation explanation은 실제 retrieval/traversal 결과 기반이어야 한다.
- Mock 구조와 Real 구조의 schema는 동일해야 한다.
- request_id 기반 idempotency를 유지한다.
- 운영 환경은 fail-fast 원칙을 따른다.

---

## 17. Current Decision Status

### 확정

- 단계적 정렬 방식, 선택지 C
- request_id optional + backend duplicate prevention
- Recommendation/Ranking Python policy module 분리
- Music Detail: RAG evidence 우선, music_catalog fallback
- SQL query constants 사용

### 구현 전 계약 확정 필요

- Redis key structure
- latest KAG/RAG/response metadata 저장 위치
- `session_degraded` 응답 위치
- `flush_logs=true` 삭제 범위
- `KAG_STATE` 확장 필드
- `RAG_STATE` 확장 필드
- detail_view_logs API request contract

---

## 18. Enforcement Rule

이 문서의 확정 정책과 충돌하는 구현은 진행하지 않는다.

충돌, 누락, 모호함이 있으면 구현 전에 사용자 확인을 받는다.
