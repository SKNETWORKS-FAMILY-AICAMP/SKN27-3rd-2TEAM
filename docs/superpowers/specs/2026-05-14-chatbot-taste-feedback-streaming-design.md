# 챗봇 취향 피드백 및 스트리밍 응답 설계

## 1. 목적

챗봇 추천 결과를 사용자의 명시적 취향 신호로 반영하고, 대화 응답을 스트리밍으로 표시한다.

이 설계의 목표는 다음과 같다.

- 챗봇 추천 카드에서 상세 모달을 연 뒤 사용자가 `내 취향에 추가`를 선택할 수 있게 한다.
- 선택한 곡은 현재 세션 안에서 즉시 추천 컨텍스트에 반영한다.
- 대화 종료 시 Redis에 누적된 취향 이벤트와 취향 요약을 PostgreSQL에 저장한다.
- 챗봇 응답은 새 스트리밍 API로 점진 표시하되, 기존 비스트리밍 API 계약은 유지한다.

## 2. 범위

포함 범위:

- 음악 상세 모달의 `내 취향에 추가` 액션
- 취향 이벤트 Redis 저장
- `SESSION_CONTEXT` 즉시 갱신
- 홈 이동 시 `저장하고 종료할까요?` 확인 흐름
- 세션 flush 시 대화 기록, 취향 이벤트, 취향 프로필 요약 DB 저장
- `/api/chatbot/respond/stream` SSE 기반 UI 스트리밍 응답 API
- 스트리밍 응답을 점진 표시하는 프론트 챗봇 UI 상태

제외 범위:

- 자동 브라우저 종료 감지 기반 DB 저장 보장
- 싫어요, 차단, 제외 추천 정책
- 장기 취향 기반 추천 랭킹 알고리즘 고도화
- 검증 전 LLM token 직접 스트리밍
- WebSocket 기반 양방향 통신
- 기존 `/api/chatbot/respond` 응답 계약 변경

## 3. 현재 구조

현재 챗봇 응답은 `POST /api/chatbot/respond`에서 완성된 JSON을 한 번에 반환한다.

대화 상태는 Redis에 `session_id` 기준으로 저장된다.

- `rimas:session:{session_id}:history`
- `rimas:session:{session_id}:context`
- `rimas:session:{session_id}:latest:*`

`POST /api/sessions/{session_id}/flush`는 Redis 대화 히스토리를 PostgreSQL의 `chat_sessions`, `chat_session_turns`에 저장하고 Redis 세션 캐시를 삭제한다.

프론트는 앱 마운트 시 `sessionId`를 생성하고 앱 수명 동안 유지한다. 현재 세션 종료는 자동 기준이 없고, flush API 호출 시에만 DB 저장이 일어난다.

## 4. 핵심 사용자 흐름

### 4.1 챗봇 스트리밍 응답

1. 사용자가 챗봇에 메시지를 입력한다.
2. 프론트는 `/api/chatbot/respond/stream`을 호출한다.
3. 백엔드는 기존 챗봇 흐름과 동일하게 KAG, RAG, Intent, Recommendation, ResponseGenerator, Validator 단계를 완료한다.
4. 백엔드는 검증을 통과한 최종 `response_state.chatbot_response`만 chunk로 나눠 SSE `delta` 이벤트로 전송한다.
5. 프론트는 마지막 봇 말풍선을 `delta` 수신마다 갱신한다.
6. 백엔드는 최종 `response_state` 기준으로 Redis history/context/latest state를 1회 저장한다.
7. Redis 저장이 성공하면 SSE `final` 이벤트로 최종 `response_state`, `display_recommendations`, `latency_ms`를 보낸다.
8. 프론트는 `final` 이벤트를 받은 뒤 추천 카드를 확정 렌더링한다.

이 스트리밍은 1차 구현에서 LLM token streaming이 아니라 UI streaming이다. 검증되지 않은 LLM 생성 텍스트를 사용자에게 노출하지 않는다.

### 4.2 내 취향에 추가

1. 사용자가 챗봇 추천 카드를 클릭한다.
2. 음악 상세 모달이 열린다.
3. 사용자가 `내 취향에 추가` 버튼을 누른다.
4. 프론트는 취향 이벤트 API를 호출한다.
5. 백엔드는 `content_id` 기준으로 상세 정보 또는 latest RAG evidence를 확인한다.
6. 백엔드는 Redis `SESSION_CONTEXT`에 장르, 무드, 아티스트, 선택 곡을 즉시 반영한다.
7. 백엔드는 Redis 취향 이벤트 목록에 `add_to_taste` 이벤트를 append한다.
8. 이후 같은 세션의 챗봇/메인 추천은 갱신된 `SESSION_CONTEXT`를 사용한다.

### 4.3 홈 이동 시 세션 종료 확인

1. 사용자가 챗봇 화면에서 홈으로 이동하려 한다.
2. 프론트는 `대화를 저장하고 종료할까요?` 확인 모달을 표시한다.
3. `저장하고 종료`를 선택하면 `POST /api/sessions/{session_id}/flush`를 호출한다.
4. 백엔드는 Redis의 대화 기록, 취향 이벤트, 취향 프로필 요약을 DB에 저장한다.
5. 저장 성공 후 Redis 세션 캐시와 latest state를 삭제한다.
6. 프론트는 새 `sessionId`를 생성하고 홈으로 이동한다.
7. `저장하지 않고 이동`을 선택하면 DB 저장 없이 Redis 세션 캐시를 삭제하고 홈으로 이동한다.
8. `취소`를 선택하면 챗봇 화면에 머문다.

## 5. API 계약

### 5.1 스트리밍 챗봇 응답

Endpoint:

```text
POST /api/chatbot/respond/stream
```

Request:

```json
{
  "user_id": "user_001",
  "session_id": "sess_001",
  "user_input": "새로운 취향 음악 추천해줘",
  "request_id": "req_001"
}
```

Response:

```text
Content-Type: text/event-stream
```

SSE events:

```text
event: delta
data: {"text": "오늘은 "}

event: delta
data: {"text": "조금 새로운 분위기의 곡을 골라봤어요."}

event: final
data: {"status":"success","response_state":{...},"latency_ms":1234.5}

event: done
data: {}
```

오류 발생 시:

```text
event: error
data: {"message":"챗봇 응답 생성 중 오류가 발생했습니다."}
```

스트리밍 endpoint는 기존 `/api/chatbot/respond` 계약을 변경하지 않는다.

### 5.2 취향 추가 이벤트

Endpoint:

```text
POST /api/taste/events
```

Request:

```json
{
  "user_id": "user_001",
  "session_id": "sess_001",
  "content_id": "track_001",
  "event_type": "add_to_taste",
  "source": "music_detail_modal",
  "request_id": "req_002"
}
```

Response:

```json
{
  "status": "success",
  "session_context": {
    "session_id": "sess_001",
    "recent_genres": ["indie"],
    "recent_artists": ["Nova Lane"],
    "recent_moods": ["night"],
    "conversation_summary": ""
  }
}
```

`event_type` 1차 허용값은 `add_to_taste`만 사용한다.

## 6. Redis 계약

기존 세션 키는 유지한다.

새 키:

```text
rimas:session:{session_id}:taste_events
```

값은 Redis list이며 각 항목은 JSON 객체다.

```json
{
  "event_id": "evt_001",
  "user_id": "user_001",
  "session_id": "sess_001",
  "content_id": "track_001",
  "event_type": "add_to_taste",
  "source": "music_detail_modal",
  "title": "Midnight Loop",
  "artist": "Nova Lane",
  "genre": ["indie"],
  "mood": ["night"],
  "recommendation_category": "discovery_candidate",
  "created_at": "2026-05-14T12:00:00Z"
}
```

TTL은 기존 `REDIS_SESSION_TTL`을 따른다.

`SESSION_CONTEXT`에는 다음 필드를 유지 또는 확장한다.

```json
{
  "session_id": "sess_001",
  "recent_genres": ["indie"],
  "recent_artists": ["Nova Lane"],
  "recent_moods": ["night"],
  "selected_tracks": ["track_001"],
  "conversation_summary": ""
}
```

`selected_tracks`는 명시적 취향 추가 곡만 저장한다. 중복 `content_id`는 한 번만 유지한다.

`selected_tracks` 추가는 SESSION_CONTEXT 계약 확장으로 간주한다. 구현 시 다음 항목을 함께 수정해야 한다.

- `app/schemas/session_context_schema.py`
- `app/contracts/fields.py`
- `tests/test_v4_runtime_contracts.py` 또는 SESSION_CONTEXT 계약 테스트
- `app/cache/session_history_cache.py`의 empty context 생성 로직

`selected_tracks`는 선택 사항이지만, 존재할 경우 `list[str]`이어야 한다.

## 7. PostgreSQL 계약

### 7.1 user_taste_events

사용자의 명시적 취향 선택 이벤트를 원본 그대로 저장한다.

필드:

- `event_id`
- `user_id`
- `session_id`
- `content_id`
- `event_type`
- `source`
- `title`
- `artist`
- `genre_json`
- `mood_json`
- `recommendation_category`
- `created_at`

### 7.2 user_taste_profiles

사용자별 취향 요약을 저장한다.

필드:

- `user_id`
- `preferred_genres_json`
- `preferred_moods_json`
- `preferred_artists_json`
- `selected_content_ids_json`
- `updated_at`

flush 시 같은 `user_id`가 이미 있으면 upsert한다. 새 이벤트가 기존 프로필과 중복될 경우 중복을 제거하고 최신 선택을 우선한다.

### 7.3 세션 시작 시 취향 프로필 hydrate

장기 취향이 다음 세션 추천에 반영되려면 Redis `SESSION_CONTEXT` 생성 시 PostgreSQL `user_taste_profiles`를 읽어와야 한다.

규칙:

1. `SESSION_CONTEXT`가 Redis에 있으면 Redis 값을 우선한다.
2. Redis miss이고 `user_id`가 있으면 `user_taste_profiles`를 조회한다.
3. 프로필이 있으면 `preferred_genres_json`, `preferred_moods_json`, `preferred_artists_json`, `selected_content_ids_json`을 기반으로 초기 `SESSION_CONTEXT`를 만든다.
4. 프로필이 없으면 기존 empty context를 사용한다.
5. hydrate된 context도 Redis에 저장하고 기존 TTL을 적용한다.

이 흐름을 위해 세션 컨텍스트 로드 경로는 `session_id`만 받는 현재 형태에서 `user_id`를 함께 받을 수 있도록 확장해야 한다. 기존 호출부는 새 시그니처에 맞춰 수정한다.

## 8. 백엔드 구성

### 8.1 TasteEventService

역할:

- 취향 이벤트 요청 검증
- `content_id` 기반 곡 정보 조회
- Redis `SESSION_CONTEXT` 갱신
- Redis `taste_events` append

곡 정보는 우선순위에 따라 조회한다.

1. latest RAG state evidence
2. MusicDetailService
3. 조회 실패 시 404 또는 명시적 실패 응답

없는 곡을 취향에 추가하지 않는다.

### 8.1.1 TasteProfileRepository

역할:

- `user_taste_events` insert
- `user_taste_profiles` upsert
- `user_taste_profiles` by `user_id` 조회

이 repository는 세션 시작 hydrate와 flush에서만 사용한다. 추천 생성 중에는 PostgreSQL을 직접 조회하지 않는다.

### 8.2 SessionFlushService 확장

기존 flush는 대화 히스토리만 DB에 저장한다.

확장 후 flush는 다음을 한 트랜잭션으로 처리한다.

1. `chat_sessions` upsert
2. `chat_session_turns` insert
3. `user_taste_events` insert
4. `user_taste_profiles` upsert
5. Redis 세션 캐시 삭제
6. latest state 삭제
7. taste_events 삭제

DB 저장 중 실패하면 Redis 캐시는 삭제하지 않는다.

### 8.3 ChatbotStreamService

기존 `ChatbotService`의 전체 흐름을 재사용하되 스트리밍 출력을 위한 orchestration을 제공한다.

스트리밍 중간에는 DB나 Redis에 완료 상태를 저장하지 않는다. 최종 `response_state`가 만들어지고 검증을 통과한 뒤 `chatbot_response`를 chunk로 나눠 `delta` 이벤트로 전송한다. 이후 Redis 저장을 완료하고 `final` 이벤트를 전송한다.

LLM token streaming은 1차 구현 범위가 아니다. OpenAI 응답이든 로컬 fallback 응답이든 최종 검증된 `response_state.chatbot_response` 문자열만 UI streaming 대상으로 사용한다.

### 8.4 SessionContextHydrationService

역할:

- Redis miss 시 `user_taste_profiles` 조회
- 조회된 장기 취향 프로필을 SESSION_CONTEXT 초기값으로 변환
- 변환된 context를 Redis에 저장

이 서비스는 추천 후보를 직접 만들지 않는다. KAG/RAG가 사용할 입력 컨텍스트만 구성한다.

## 9. 프론트 구성

### 9.1 챗봇 스트리밍 상태

챗봇 store는 임시 봇 응답을 지원한다.

- 사용자 메시지를 먼저 history에 추가한다.
- 빈 봇 말풍선을 추가한다.
- `delta` 수신 시 마지막 봇 말풍선 텍스트를 append한다.
- `final` 수신 시 `display_recommendations`를 확정한다.
- 오류 시 마지막 봇 말풍선을 오류 메시지로 교체하거나 제거한다.

### 9.2 상세 모달 취향 버튼

`MusicDetailModal`에 `내 취향에 추가` 버튼을 추가한다.

상태:

- 기본: 클릭 가능
- 저장 중: 비활성화
- 저장 완료: `취향에 추가됨`
- 실패: 오류 메시지 표시 후 재시도 가능

동일 모달에서 같은 곡을 반복 추가하지 않는다.

### 9.3 홈 이동 확인

챗봇 화면에서 홈으로 이동할 때 확인 모달을 띄운다.

버튼:

- `저장하고 종료`
- `저장하지 않고 이동`
- `취소`

`저장하고 종료` 성공 후:

- chat store 초기화
- session store `resetSession()`
- 홈 이동

`저장하지 않고 이동` 성공 후:

- Redis 세션 삭제 API 호출
- chat store 초기화
- session store `resetSession()`
- 홈 이동

## 10. 오류 처리

- 취향 이벤트 저장 실패는 챗봇 대화를 중단하지 않는다.
- 취향 이벤트 저장 실패 시 모달 안에 명확한 실패 상태를 표시한다.
- flush 실패 시 홈 이동을 막고 사용자가 재시도할 수 있게 한다.
- 스트리밍 중 오류가 발생하면 SSE `error` 이벤트를 보내고 request lifecycle을 종료한다.
- request_id 중복 요청은 기존 중복 요청 정책을 따른다.
- DB flush 성공 전에는 Redis 세션을 삭제하지 않는다.

## 11. 테스트 기준

백엔드:

- 취향 이벤트 API가 Redis context와 taste_events를 갱신한다.
- SESSION_CONTEXT schema가 `selected_tracks`를 선택 필드로 허용한다.
- Redis context miss 시 user_taste_profiles 기반 hydrate가 수행된다.
- 없는 `content_id`는 취향 이벤트로 저장하지 않는다.
- flush가 대화 기록, 취향 이벤트, 취향 프로필을 같은 트랜잭션으로 저장한다.
- flush 실패 시 Redis 세션이 유지된다.
- 스트리밍 endpoint가 `delta`, `final`, `done` 이벤트 순서를 보장한다.
- 스트리밍 endpoint는 검증 완료 전 LLM token을 전송하지 않는다.
- 기존 `/api/chatbot/respond` 테스트가 깨지지 않는다.

프론트:

- 스트리밍 delta가 마지막 봇 메시지에 누적된다.
- final 이벤트 이후 추천 카드가 렌더링된다.
- `내 취향에 추가` 성공/실패 상태가 표시된다.
- 홈 이동 시 확인 모달이 뜬다.
- `저장하고 종료` 성공 후 새 sessionId가 생성된다.
- `취소`는 현재 대화 상태를 유지한다.

## 12. 구현 순서

1. SESSION_CONTEXT 계약 확장
2. DB schema와 query constant 추가
3. Redis taste_events key/helper 추가
4. TasteProfileRepository와 SessionContextHydrationService 추가
5. TasteEventService와 API 추가
6. SessionFlushService에 취향 이벤트/profile flush 추가
7. MusicDetailModal에 `내 취향에 추가` 액션 연결
8. 홈 이동 확인 모달과 flush/clear 흐름 연결
9. 검증 완료 response_state 기반 UI 스트리밍 챗봇 endpoint 추가
10. 프론트 스트리밍 수신 및 chat store 확장
11. 백엔드/프론트 테스트 추가

스트리밍은 취향 저장과 독립적으로 동작해야 한다. 취향 저장 기능이 실패해도 챗봇 스트리밍 응답은 정상 동작해야 한다.
