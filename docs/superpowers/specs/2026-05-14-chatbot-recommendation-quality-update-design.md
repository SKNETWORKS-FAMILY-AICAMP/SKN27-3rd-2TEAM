# 챗봇 추천 품질 업데이트 설계

## 1. 목적

챗봇과 메인 추천 화면에서 사용자가 명시한 부정 취향, 요청 곡 수, 중복 추천, 빈 추천 섹션, 추천 이유 노출 방식을 일관되게 처리한다.

이번 설계는 다음 5개 문제를 수정 대상으로 삼는다.

1. 사용자가 싫다고 말한 아티스트나 곡이 이후 추천에 다시 등장하는 문제
2. 추천 결과에 같은 노래가 여러 번 등장하는 문제
3. 사용자가 1곡 또는 2곡을 요청해도 고정 개수로 추천되는 문제
4. 신규 발매 또는 다양한 장르 추천 섹션이 비어 있는 문제
5. 추천 이유에 가사 또는 원문 evidence가 그대로 노출되는 문제

## 2. 기존 문서와의 관계

`docs/superpowers/specs/2026-05-14-chatbot-taste-feedback-streaming-design.md`는 기존 범위에서 "싫어요, 차단, 제외 추천 정책"을 제외했다.

이번 설계서는 해당 제외 범위를 변경한다. 명시적 부정 취향은 추천 품질에 직접 영향을 주는 필수 정책으로 승격한다.

기존 `add_to_taste`는 긍정 취향만 저장한다. 이번 설계의 `disliked_artists`, `disliked_tracks`는 긍정 취향과 분리된 부정 취향 계약으로 관리한다.

## 3. 범위

포함 범위:

- 사용자 입력에서 부정 취향 추출
- 세션 컨텍스트에 부정 취향 저장
- KAG/RAG 추천 후보에서 부정 취향 필터링
- 추천 결과에서 `content_id` 기준 중복 제거
- 요청 곡 수를 파이프라인에 전달하고 최종 추천 수에 반영
- 메인 추천 화면의 `new_release`, `discovery` 섹션 fallback 채우기
- 추천 이유에서 가사 원문 또는 긴 evidence 원문 직접 노출 금지

제외 범위:

- "다시는 추천하지 않기" 같은 별도 UI 버튼
- 부정 취향 삭제 또는 관리 화면
- Elasticsearch 재색인 또는 인덱스 구조 변경
- LLM이 새로운 곡, 아티스트, content_id를 생성하는 기능

## 4. 핵심 정책

### 4.1 부정 취향 우선 정책

사용자가 "싫어", "별로", "추천하지 마", "빼줘", "빼고", "말고", "제외해줘", "제외하고", "듣기 싫어"처럼 명시적으로 부정 표현을 하면 부정 표현 앞의 대상을 부정 취향 후보로 본다.

부정 취향 후보는 장르 부정 표현 또는 `music_catalog` 정확 매칭으로 확인되는 경우에만 저장한다.

매칭 규칙:

- 부정 표현 앞의 마지막 대화 구간에 허용 장르가 포함되면 `disliked_genres`에 저장한다.
- `artist`와 정확히 일치하면 `disliked_artists`에 저장한다.
- `title`과 정확히 일치하면 일치하는 모든 `content_id`를 `disliked_tracks`에 저장한다.
- `artist`와 `title`이 모두 일치하면 아티스트 제외를 우선한다.
- 장르, 아티스트, 곡 중 어디에도 정확 매칭이 없으면 영구 저장하지 않는다.

부정 취향은 긍정 취향보다 우선한다.

같은 세션에서 사용자가 어떤 아티스트를 좋아한다고 말했더라도, 이후에 "그 아티스트는 싫어"라고 말하면 이후 추천에서는 제외한다.

부정 취향은 세션이 바뀌어도 유지되어야 하므로 PostgreSQL에 영구 저장한다.

부정 취향 해제는 이번 범위에 포함하지 않는다. 따라서 사용자가 "전에 싫다고 했던 아티스트 다시 추천해줘"처럼 명시적으로 요청하더라도, 이번 구현에서는 자동 해제를 하지 않는다. 이 동작은 별도 승인된 해제 정책이 생기기 전까지 지원하지 않는다.

### 4.2 중복 추천 정책

추천 결과의 중복 기준은 제목이 아니라 `content_id`다.

같은 `content_id`가 여러 evidence에서 반복되더라도 최종 추천과 메인 화면 섹션에는 한 번만 표시한다.

다른 `content_id`가 같은 제목을 갖는 경우는 별도 곡으로 취급한다.

### 4.3 요청 곡 수 정책

사용자가 "1곡", "한 곡", "2곡", "두 곡", "3곡"처럼 추천 개수를 명시하면 `requested_count`로 기록한다.

`requested_count`가 있으면 최종 추천 수는 해당 값으로 제한한다.

후보가 요청 수보다 적으면 있는 후보만 반환한다.

후보가 없으면 기존 fallback 응답 정책을 따른다.

요청 수가 없으면 기존 기본값인 `MAX_SELECTED_RECOMMENDATIONS`를 유지한다.

### 4.4 메인 추천 섹션 보장 정책

메인 추천 화면의 `personalized`, `new_release`, `discovery` 섹션은 빈 배열로 방치하지 않는다.

RAG 결과가 특정 섹션을 채우지 못하면 DB fallback으로 채운다.

사용자 취향 데이터가 있으면 세션 컨텍스트의 `recent_genres`, `recent_moods`, `recent_artists`, `selected_tracks`를 fallback 정렬과 필터링에 반영한다.

사용자 취향 데이터가 없으면 DB의 결정론적 정렬을 사용한다.

현재 `music_catalog`에는 `release_date`와 `popularity` 컬럼이 없으므로 fallback 정렬은 다음 필드만 사용한다.

- 신규 발매: `release_type = 'new_release'`, `created_at DESC`
- 다양한 장르: `recommendation_category = 'discovery_candidate'`, `created_at DESC`
- 보조 정렬: `content_id ASC`

### 4.5 추천 이유 안전 설명 정책

`evidence_summary` 또는 Elasticsearch `content`가 가사 원문, 긴 본문, raw document 내용일 수 있으므로 그대로 `display_reason`에 복사하지 않는다.

추천 이유는 다음 정보만 사용해서 짧은 한국어 설명으로 만든다.

- title
- artist
- genre
- mood
- recommendation_category
- release_type
- match_reason
- 짧게 정제된 evidence hint

LLM은 추천 결과의 곡, 아티스트, content_id를 생성하거나 바꾸지 않는다.

LLM은 이미 선택된 추천 결과에 대해 설명 문장만 자연스럽게 작성한다.

LLM을 사용할 수 없을 때도 로컬 fallback이 raw evidence를 그대로 노출하지 않고 장르, 분위기, 추천 카테고리 기반 문장을 생성한다.

## 5. 데이터 계약

### 5.1 SESSION_CONTEXT 확장

기존:

```json
{
  "session_id": "session_001",
  "recent_genres": ["indie"],
  "recent_artists": ["Nova Lane"],
  "recent_moods": ["night"],
  "selected_tracks": ["track_001"],
  "conversation_summary": ""
}
```

변경:

```json
{
  "session_id": "session_001",
  "recent_genres": ["indie"],
  "recent_artists": ["Nova Lane"],
  "recent_moods": ["night"],
  "selected_tracks": ["track_001"],
  "disliked_artists": ["Billie Eilish"],
  "disliked_tracks": ["track_999"],
  "conversation_summary": ""
}
```

규칙:

- `disliked_artists`는 `list[str]`다.
- `disliked_tracks`는 `list[str]`다.
- `disliked_genres`는 `list[str]`다.
- 값은 중복 없이 유지한다.
- 세션 컨텍스트에 필드가 없으면 빈 배열로 취급한다.
- Redis 세션 내 유지와 PostgreSQL 영구 저장을 모두 다룬다.
- PostgreSQL에 저장된 부정 취향은 새 세션 hydrate 시 SESSION_CONTEXT에 병합한다.
- 새 부정 취향은 허용 장르 매칭 또는 `music_catalog` 정확 매칭을 통과한 값만 저장한다.

### 5.2 USER_NEGATIVE_PREFERENCE 저장 계약

부정 취향은 긍정 취향 profile과 분리해 저장한다.

```sql
CREATE TABLE IF NOT EXISTS user_negative_preferences (
    user_id VARCHAR(64) PRIMARY KEY REFERENCES users(user_id),
    disliked_artists_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    disliked_tracks_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

규칙:

- `user_id`당 하나의 row만 유지한다.
- 새 부정 취향은 기존 JSON 배열과 병합한다.
- 중복 값은 제거한다.
- 삭제 또는 해제 API는 이번 범위에서 만들지 않는다.
- session flush와 별개로, 사용자가 부정 취향을 말한 턴 이후 즉시 저장한다.

### 5.3 INTENT_STATE 확장

변경:

```json
{
  "intent_type": "personalized_recommendation",
  "confidence": 0.82,
  "normalized_query": "잔잔한 곡 두 곡 추천해줘",
  "detected_moods": ["calm"],
  "detected_genres": [],
  "detected_situations": [],
  "requested_count": 2,
  "disliked_artists": [],
  "disliked_tracks": [],
  "requires_kag": true,
  "requires_rag": true
}
```

규칙:

- `requested_count`는 `int | None`이다.
- 허용 범위는 1 이상 `MAX_SELECTED_RECOMMENDATIONS` 이하로 제한한다.
- `disliked_artists`, `disliked_tracks`는 현재 턴에서 새로 감지한 부정 취향이다.

### 5.4 KAG_INPUT constraints 확장

변경:

```json
{
  "allow_discovery": true,
  "allow_new_release": true,
  "max_candidates": 2,
  "excluded_artists": ["Billie Eilish"],
  "excluded_tracks": ["track_999"]
}
```

규칙:

- `max_candidates`는 요청 곡 수가 있으면 해당 값을 사용한다.
- 요청 곡 수가 없으면 기존 기본 후보 수를 유지한다.
- `excluded_artists`는 세션 누적 부정 아티스트와 현재 턴 부정 아티스트를 합친 값이다.
- `excluded_tracks`는 세션 누적 부정 곡과 현재 턴 부정 곡을 합친 값이다.

### 5.5 KAG_STATE excluded_nodes

변경:

```json
{
  "excluded_nodes": [
    {"type": "artist", "value": "Billie Eilish"},
    {"type": "track", "value": "track_999"}
  ]
}
```

규칙:

- KAG adapter는 필터에 사용한 제외 조건을 `excluded_nodes`에 기록한다.
- RAG adapter는 `excluded_nodes`를 읽어 evidence를 한 번 더 방어적으로 필터링한다.

## 6. 컴포넌트 설계

### 6.1 InputPlannerAgent

역할:

- 사용자 입력에서 intent, mood, genre, situation을 추출한다.
- 요청 곡 수를 `requested_count`로 추출한다.
- 명시적 부정 취향을 `disliked_artists`, `disliked_tracks`로 추출한다.

규칙 기반 fallback은 다음을 지원한다.

- 숫자 표현: `1곡`, `한 곡`, `하나`, `2곡`, `두 곡`, `둘`, `3곡`, `세 곡`, `셋`
- 부정 표현: `싫어`, `싫다`, `별로`, `듣기 싫어`, `추천하지 마`, `빼줘`, `제외해줘`

LLM planner를 사용하는 경우에도 schema validation을 통과한 필드만 사용한다.

### 6.2 Session Cache

역할:

- `_empty_context()`에 `disliked_artists`, `disliked_tracks` 기본값을 추가한다.
- `update_context_from_turn()`이 현재 턴의 부정 취향을 세션 컨텍스트에 병합한다.
- 현재 턴에서 새 부정 취향이 감지되면 PostgreSQL 저장 service에 전달한다.

병합 규칙:

- 새 값이 앞에 오도록 병합한다.
- 중복을 제거한다.
- 최대 보관 개수는 각 50개로 제한한다.

### 6.3 KAG Dispatch와 Adapter

역할:

- `KagDispatchAgent`는 `kag_input_json.constraints.max_candidates`를 adapter limit으로 전달한다.
- Mock KAG는 `excluded_nodes`를 기록하고 mock 후보에서 제외 가능한 항목을 제거한다.
- Real KAG는 Neo4j query 이후 결과 row에서 제외 조건과 일치하는 후보를 제거한다.

Real KAG에서 Cypher query 자체에 제외 조건을 넣는 것은 이번 구현에서 선택 사항이다. 우선 adapter boundary에서 결정론적으로 필터링해 계약을 보장한다.

### 6.4 RAG Adapter

역할:

- Mock RAG는 3개 고정 리스트를 더 큰 deterministic fixture pool로 확장한다.
- Mock RAG와 Real RAG 모두 `excluded_nodes`에 포함된 artist 또는 content_id를 evidence에서 제거한다.
- Real RAG는 `target_section` 또는 hit metadata를 기반으로 `recommendation_category`를 결정한다.

Real RAG category 결정 순서:

1. hit의 `release_type == "new_release"`이면 `new_release`
2. `rag_input_json.target_section == "discovery_section"`이면 `discovery_candidate`
3. `rag_input_json.target_section == "new_release_section"`이면 `new_release`
4. 그 외는 `personalized_match`

### 6.5 RecommendationAgent

역할:

- 최종 추천 후보를 `content_id` 기준으로 중복 제거한다.
- `requested_count`가 있으면 해당 수만큼만 반환한다.
- `display_reason`에는 raw `evidence_summary`를 그대로 넣지 않는다.

추천 이유 생성은 별도 helper로 분리한다.

```python
def build_display_reason(item: dict) -> str:
    ...
```

이 helper는 장르, 분위기, 추천 카테고리 기반의 짧은 문장을 만든다.

### 6.6 ResponseGenerator

역할:

- LLM prompt에 "가사 또는 원문 evidence를 직접 인용하지 않는다"는 규칙을 추가한다.
- deterministic draft를 기반으로 LLM이 사용자 노출용 `display_reason`을 자연스럽게 다듬는다.
- LLM 결과의 `content_id`, `title`, `artist`가 선택된 추천 결과와 일치하고 추천 이유가 검증을 통과할 때만 LLM `display_reason`을 사용한다.
- LLM 결과가 검증을 통과하지 못하면 deterministic draft를 사용한다.
- 로컬 fallback도 `display_reason`을 raw evidence가 아닌 정제 문장으로 구성한다.
- LLM 응답 검증은 기존 `ResponseValidator`, `ProvenanceValidator`를 유지한다.

### 6.7 DisplayReasonValidator

역할:

- LLM이 다듬은 `display_reason`이 추천 결과 계약을 깨지 않는지 검증한다.
- title, artist, content_id가 바뀌었는지 검증한다.
- raw `evidence_summary` 또는 Elasticsearch raw `content`가 그대로 복사되었는지 검증한다.
- 문장 길이가 과도하게 길면 실패 처리한다.
- 검증 실패 시 deterministic draft를 사용한다.

### 6.8 NegativePreferenceRepository

역할:

- `user_negative_preferences` upsert를 담당한다.
- `user_id` 기반 부정 취향 조회를 담당한다.
- JSON 배열 병합은 repository 호출 전 service에서 결정론적으로 수행한다.

### 6.9 SessionContextHydrationService

역할:

- 기존 긍정 취향 profile hydrate에 더해 부정 취향 profile을 조회한다.
- 조회된 `disliked_artists_json`, `disliked_tracks_json`을 SESSION_CONTEXT에 병합한다.

### 6.10 MainRecommendationService

역할:

- `_build_view_model()`에서 섹션별 `content_id` 중복을 제거한다.
- `new_release`, `discovery` 섹션이 비면 DB fallback을 조회해 채운다.
- fallback 결과도 `disliked_artists`, `disliked_tracks`, 이미 표시된 `content_id`를 제외한다.

fallback 조회는 `MusicCatalogRepository`에 추가한다.

```python
find_fallback_new_releases(limit: int, excluded_content_ids: list[str], excluded_artists: list[str])
find_fallback_discovery(limit: int, preferred_genres: list[str], excluded_content_ids: list[str], excluded_artists: list[str])
```

## 7. 에러 처리

- 부정 취향 추출 실패는 추천 실패로 처리하지 않는다.
- `requested_count` 파싱 실패는 `None`으로 처리하고 기존 기본 추천 수를 사용한다.
- fallback DB 조회 실패는 해당 섹션만 빈 배열로 두고 전체 응답은 성공으로 유지한다.
- RAG evidence가 모두 필터링되면 기존 `NO_RECOMMENDATIONS` fallback 응답을 사용한다.
- LLM 추천 이유 생성 실패 시 로컬 fallback 설명을 사용한다.

## 8. 테스트 기준

### 8.1 부정 취향

- "Billie Eilish 싫어" 입력 시 `disliked_artists`에 저장된다.
- 다음 턴 추천에서 Billie Eilish evidence가 제거된다.
- KAG_STATE `excluded_nodes`에 artist 제외 조건이 남는다.

### 8.2 중복 제거

- RAG evidence에 같은 `content_id`가 3번 있어도 최종 추천에는 1번만 나온다.
- 메인 추천 view model에서도 같은 `content_id`는 한 섹션 안에 한 번만 나온다.
- 다른 섹션에 이미 표시된 곡도 fallback 섹션에 다시 나오지 않는다.

### 8.3 요청 곡 수

- "1곡 추천해줘"는 최종 추천 1개를 반환한다.
- "두 곡 추천해줘"는 최종 추천 2개를 반환한다.
- 후보가 1개뿐이면 "두 곡" 요청에도 1개만 반환한다.
- 요청 수가 없으면 기존 기본 추천 수를 사용한다.

### 8.4 메인 추천 섹션 fallback

- RAG가 `new_release` evidence를 반환하지 않아도 DB fallback으로 `new_release` 섹션을 채운다.
- RAG가 `discovery_candidate` evidence를 반환하지 않아도 DB fallback으로 `discovery` 섹션을 채운다.
- fallback 결과는 부정 취향과 중복 content_id를 제외한다.

### 8.5 추천 이유

- `evidence_summary`에 긴 가사 원문이 있어도 `display_reason`에 그대로 포함되지 않는다.
- LLM disabled 환경에서도 추천 이유는 장르, 분위기, 추천 카테고리 기반 문장이다.
- `title`, `artist`, `content_id`는 RAG/selected recommendation 값과 일치한다.

## 9. 구현 대상 파일

수정 대상:

- `app/schemas/session_context_schema.py`
- `app/schemas/intent_state_schema.py`
- `app/schemas/kag_input_schema.py`
- `app/cache/session_history_cache.py`
- `app/services/session_context_hydration_service.py`
- `app/services/session_cache_service.py`
- `app/services/negative_preference_service.py`
- `app/prompts/input_planner_prompt.py`
- `app/agents/input_planner_agent.py`
- `app/agents/intent_agent.py`
- `app/agents/kag_dispatch_agent.py`
- `app/kag/adapters/mock_kag_adapter.py`
- `app/kag/adapters/real_kag_adapter.py`
- `app/rag/adapters/mock_rag_adapter.py`
- `app/rag/adapters/rag_real_adapter.py`
- `app/rag/services/elasticsearch_retriever.py`
- `app/agents/recommendation_agent.py`
- `app/agents/response_generator.py`
- `app/validators/display_reason_validator.py`
- `app/services/main_recommendation_service.py`
- `app/repositories/query_constants.py`
- `app/repositories/music_catalog_repository.py`
- `app/repositories/negative_preference_repository.py`
- `db/schema.sql`

테스트 대상:

- `tests/test_v4_runtime_contracts.py`
- `tests/test_chatbot_service.py`
- `tests/test_v4_agent_and_detail_flow.py`
- `tests/test_mock_kag_adapter.py`
- `tests/test_real_kag_adapter.py`
- `tests/test_mock_rag_adapter.py`
- `tests/test_real_rag_adapter.py`
- `tests/test_main_recommendation_service.py`
- `tests/test_response_generator_fallback.py`
- `tests/test_negative_preference_repository.py`
- `tests/test_display_reason_validator.py`

## 10. 승인 기준

구현은 다음 조건을 모두 만족해야 완료로 본다.

- 사용자가 싫다고 말한 아티스트 또는 곡은 이후 추천 후보와 최종 응답에서 제외된다.
- 사용자가 싫다고 말한 아티스트 또는 곡은 PostgreSQL에 저장되어 새 세션 hydrate 이후에도 제외된다.
- 같은 `content_id`가 챗봇 추천과 메인 추천 화면에 중복 표시되지 않는다.
- 사용자가 요청한 곡 수가 최종 추천 개수에 반영된다.
- 메인 추천 화면의 신규 발매와 다양한 장르 섹션은 가능한 경우 fallback으로 채워진다.
- 추천 이유에 raw lyrics, raw document, 긴 evidence 원문이 그대로 노출되지 않는다.
- LLM이 생성한 추천 이유가 검증에 실패하면 deterministic draft가 사용자에게 노출된다.
- 기존 `/api/chatbot/respond`, `/api/chatbot/respond/stream`, 메인 추천 API 계약은 깨지지 않는다.
- 관련 pytest targeted suite가 통과한다.

## 11. 설계 자체 점검

- 기존 제외 범위였던 싫어요/차단 정책을 이번 설계에서 명시적으로 범위 변경했다.
- `release_date`, `popularity`처럼 현재 DB schema에 없는 필드는 사용하지 않는다.
- 부정 취향 영구 DB 저장은 품질 요구사항의 핵심이므로 이번 범위에 포함했다.
- LLM은 추천 결과를 생성하지 않고 설명만 생성한다.
- raw evidence를 추천 이유로 직접 복사하는 경로를 제거하고, LLM 후처리는 validator 통과 시에만 사용한다.
