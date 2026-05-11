# RIMAS Pending Decisions

작성 기준:

- 기준 문서: `docs/implementation_direction.md`
- 목적: 구현 전에 사용자 확인이 필요한 계약과 선택지를 분리한다.
- 원칙: 이 문서의 항목은 확정 전까지 임의 구현하지 않는다.

---

## 1. Redis Key Structure 확장 사용 범위

### 현재 확정된 key

```text
rimas:session:{session_id}:history
rimas:session:{session_id}:context
rimas:session:{session_id}:latest:kag_state
rimas:session:{session_id}:latest:rag_state
rimas:session:{session_id}:latest:response_state
rimas:session:{session_id}:recommendation:metadata
```

### 미확정 사항

- latest KAG/RAG/response state를 실제로 언제 저장할지
- recommendation metadata에 어떤 필드를 저장할지
- flush 시 latest state와 metadata를 삭제할지

### 선택지

#### A. history/context만 flush 대상으로 유지

- 장점: 현재 구현과 가장 가깝다.
- 단점: Music Detail에서 latest RAG_STATE를 재사용하기 어렵다.

#### B. history/context/latest state/metadata 모두 flush 대상으로 포함

- 장점: session 종료 시 Redis 관련 상태를 깔끔하게 정리할 수 있다.
- 단점: latest state 저장 구조를 먼저 구현해야 한다.

### 추천

**B 추천.**

이유:

- `docs/implementation_direction.md`에서 Redis key structure를 확장하기로 이미 정리했다.
- Music Detail recent RAG_STATE 연결과도 맞다.

---

## 2. session_degraded Contract 위치

### 미확정 사항

Redis 장애 또는 session cache 장애 시 `session_degraded`를 어디에 포함할지 결정해야 한다.

### 선택지

#### A. API wrapper 최상위에 둔다

예시:

```json
{
  "status": "success",
  "session_degraded": true,
  "response_state": {}
}
```

장점:

- `RESPONSE_STATE` 계약을 건드리지 않는다.
- session/cache 장애와 추천 응답 내용을 분리할 수 있다.

단점:

- API마다 wrapper 필드 처리를 맞춰야 한다.

#### B. RESPONSE_STATE 내부에 둔다

예시:

```json
{
  "status": "success",
  "response_type": "curator_recommendation",
  "chatbot_response": "추천 응답",
  "display_recommendations": [],
  "used_content_ids": [],
  "session_degraded": true
}
```

장점:

- 챗봇 응답 객체 안에서 한 번에 확인 가능하다.

단점:

- `ResponseStateSchema`와 LLM response schema를 확장해야 한다.
- LLM 출력과 시스템 metadata가 섞일 수 있다.

### 추천

**A 추천.**

이유:

- `session_degraded`는 LLM 응답 내용이 아니라 시스템 실행 상태다.
- RESPONSE_STATE는 추천 응답 계약으로 유지하는 것이 안전하다.

---

## 3. flush_logs=true 삭제 범위

### 미확정 사항

`flush_logs=true`가 들어왔을 때 `interaction_logs`를 어떤 기준으로 삭제할지 결정해야 한다.

### 선택지

#### A. `session_id` 기준 삭제

```text
DELETE FROM interaction_logs WHERE session_id = ?
```

장점:

- 세션 flush와 의미가 가장 잘 맞는다.
- 특정 세션 테스트 로그만 정리 가능하다.

단점:

- 동일 유저의 다른 세션 로그는 남는다.

#### B. `user_id` 기준 삭제

```text
DELETE FROM interaction_logs WHERE user_id = ?
```

장점:

- 테스트 사용자 전체 로그 초기화가 쉽다.

단점:

- 운영에서 위험하다.
- 다른 세션의 감사 로그까지 지울 수 있다.

#### C. `request_id` 기준 삭제

```text
DELETE FROM interaction_logs WHERE request_id = ?
```

장점:

- 가장 좁은 범위다.

단점:

- flush API가 session 단위라 의미가 잘 맞지 않는다.

### 추천

**A 추천.**

이유:

- flush API가 `POST /api/sessions/{session_id}/flush` 구조이기 때문이다.
- 운영 안정성 측면에서도 `user_id` 기준 삭제보다 안전하다.

추가 권장:

- `flush_logs=true`는 `local/dev` 환경에서만 허용하는 옵션으로 제한한다.

---

## 4. KAG_STATE 확장 필드

### 현재 상태

현재 `KagStateSchema`는 단순 구조다.

```json
{
  "status": "success",
  "recommendation_goal": {},
  "recommended_content_ids": [],
  "recommendation_category": "",
  "route": "",
  "target_section": ""
}
```

### 확장 후보

- `traversal_reason`
- `matched_nodes`
- `excluded_nodes`
- `candidate_tracks`
- `diversity_metadata`

### 선택지

#### A. 기존 schema 유지

장점:

- 변경 범위가 작다.
- Mock/Real adapter 전환 전에 안정적이다.

단점:

- Real Neo4j traversal trace를 담기 부족하다.

#### B. optional 필드로 확장

예시:

```json
{
  "status": "success",
  "recommendation_goal": {},
  "recommended_content_ids": [],
  "recommendation_category": "",
  "route": "",
  "target_section": "",
  "traversal_reason": "",
  "matched_nodes": [],
  "excluded_nodes": [],
  "candidate_tracks": [],
  "diversity_metadata": {}
}
```

장점:

- 기존 Mock 흐름과 호환된다.
- Real KAG 구현 준비가 가능하다.

단점:

- Validator와 compact state 정책을 같이 정해야 한다.

### 추천

**B 추천.**

이유:

- Real KAG Adapter 구현 전 schema를 먼저 고정한다는 방향과 맞다.
- optional 필드로 두면 기존 테스트와 흐름을 크게 깨지 않는다.

---

## 5. RAG_STATE 확장 필드

### 현재 상태

현재 흐름은 `recommended_content_evidence`와 `recommendation_reason` 중심이다.

### 확장 후보

- `query`
- `normalized_query`
- `retrieval_metadata`
- `retrieval_trace`

### 선택지

#### A. 새 구조로 완전히 변경

예시:

```json
{
  "query": "",
  "normalized_query": "",
  "evidences": [],
  "retrieval_metadata": {}
}
```

장점:

- Elasticsearch retrieval 중심 구조가 명확하다.

단점:

- 기존 `RecommendationAgent`, `CompactStateBuilder`, validator, tests를 많이 바꿔야 한다.

#### B. 기존 구조 유지 + optional metadata 추가

예시:

```json
{
  "status": "success",
  "query": "",
  "normalized_query": "",
  "recommended_content_evidence": [],
  "recommendation_reason": {},
  "retrieval_metadata": {},
  "retrieval_trace": {}
}
```

장점:

- 기존 코드와 호환된다.
- Real RAG 구현 준비가 가능하다.

단점:

- 필드가 다소 많아진다.

### 추천

**B 추천.**

이유:

- 현재 구현은 이미 `recommended_content_evidence`를 기준으로 움직인다.
- Real RAG Adapter를 붙이기 전에 호환성을 유지하는 것이 안전하다.

---

## 6. detail_view_logs API Contract

### 현재 상태

Music Detail API:

```text
GET /api/music/detail/{content_id}
```

현재는 `user_id`, `session_id`, `request_id`를 받지 않는다.

### 저장 목표

- `user_id`
- `request_id`
- `track_id`
- `viewed_at`
- `source_type`
- `recommendation_context` optional

### 선택지

#### A. query parameter로 추가

예시:

```text
GET /api/music/detail/{content_id}?user_id=user_001&session_id=session_001&request_id=req_001
```

장점:

- 현재 GET API와 잘 맞는다.
- 프론트 수정이 단순하다.

단점:

- query가 길어진다.

#### B. 별도 POST 로그 API 추가

예시:

```text
POST /api/music/detail/{content_id}/view-log
```

장점:

- 조회와 로그 저장 책임이 분리된다.

단점:

- API 호출이 하나 더 필요하다.
- 프론트 흐름이 복잡해진다.

### 추천

**A 추천.**

이유:

- 현재 상세 조회와 view log 저장은 같은 사용자 행동에서 발생한다.
- MVP 단계에서는 단일 GET 요청에서 최소 로그 저장을 처리하는 편이 단순하다.

---

## 7. Redis latest RAG_STATE 저장 시점

### 미확정 사항

Music Detail이 latest RAG_STATE를 사용하려면 언제 Redis에 저장할지 정해야 한다.

### 선택지

#### A. Chatbot/Main Recommendation 응답 생성 직후 저장

장점:

- recommendation 시점 evidence와 detail 시점 evidence가 일치한다.
- 구현 위치가 명확하다.

단점:

- Redis 쓰기 횟수가 늘어난다.

#### B. Music Detail 요청 시 최근 interaction log에서 복원

장점:

- Redis에 latest state를 따로 저장하지 않아도 된다.

단점:

- DB 조회가 필요하다.
- compact log만 저장되어 있으면 detail evidence가 부족할 수 있다.

### 추천

**A 추천.**

이유:

- `docs/implementation_direction.md`에서 Redis/session 기반 recent RAG_STATE 사용을 선택했다.
- detail explanation 일관성을 가장 잘 보장한다.

---

## 8. Prompt / LLM Planner Contract

### 미확정 사항

LLM Input Planner를 언제, 어떤 방식으로 도입할지 정해야 한다.

### 선택지

#### A. 현재 rule-based planner 유지

장점:

- 안정적이고 테스트하기 쉽다.
- 외부 LLM 의존이 없다.

단점:

- 다양한 자연어 입력 해석력이 낮다.

#### B. LLM planner를 optional로 추가하고 실패 시 rule-based fallback

장점:

- 자연어 해석력이 좋아진다.
- 실패해도 deterministic fallback이 있다.

단점:

- prompt, parser, schema validation, provider 설정이 필요하다.

### 추천

**B 추천.**

이유:

- 최종 방향은 LLM planning 허용이다.
- 단, enum/schema validation과 fallback planner가 반드시 같이 있어야 한다.

---

## 9. 다음 구현 순서 추천

위 결정 중 먼저 확정할 순서는 다음이 안전하다.

1. `KAG_STATE` optional 확장 필드
2. `RAG_STATE` optional 확장 필드
3. Redis latest state 저장 시점
4. `session_degraded` 위치
5. `flush_logs=true` 삭제 범위
6. detail_view_logs API contract
7. LLM Planner contract

---

## 10. User Decision Checklist

아래 항목에 대해 승인/수정/보류를 표시하면 이후 구현 기준으로 사용한다.

```text
[ 승인 ] Redis flush 대상: B안 승인
[ 승인 ] session_degraded 위치: A안 승인
[ 승인 ] flush_logs=true 삭제 범위: A안 승인
[ 승인 ] KAG_STATE 확장: B안 승인
[ 승인 ] RAG_STATE 확장: B안 승인
[ 승인 ] detail_view_logs API: A안 승인
[ 승인 ] latest RAG_STATE 저장 시점: A안 승인
[ 승인 ] LLM Planner: B안 승인
```
