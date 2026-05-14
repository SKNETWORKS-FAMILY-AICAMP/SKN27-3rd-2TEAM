# RIMAS v4 설계 기준 구현 점검 리포트

작성 기준:

- 기준 설계서: `docs/rimas_v_4_integrated_design_updated_final_.md`
- 사용자 확인 문서: `C:\Users\Playdata\Desktop\컨펌_v1.txt`
- 점검 범위: 문서와 실제 구현 구조 비교
- 주의: 본 리포트 작성 과정에서 소스 코드는 수정하지 않았다.

---

## 1. 전체 결론

현재 프로젝트는 RIMAS v4 설계의 큰 폴더 구조와 일부 Runtime Contract, Redis 세션 캐시, PostgreSQL 로그 저장, Mock KAG/RAG 흐름을 갖추고 있다. 하지만 설계서가 요구하는 실제 실행 흐름과 현재 구현 흐름 사이에는 중요한 불일치가 있다.

가장 큰 문제는 다음이다.

1. `InputPlannerAgent`가 구현되어 있지만 실제 `OrchestratorAgent` 흐름에 연결되어 있지 않다.
2. 설계서상 흐름은 `Input Planner -> INTENT_STATE/KAG_INPUT_JSON -> Intent Agent -> KAG -> RAG`인데, 현재 구현은 `KAG -> RAG -> Intent -> Recommendation -> Response` 순서다.
3. `RAG_INPUT_JSON` 스키마는 존재하지만 `RagDispatchAgent`는 이를 만들거나 받지 않고 `kag_state`만 받는다.
4. `IntentAgent`가 설계서의 허용 intent enum과 다른 값을 반환한다.
5. Real KAG/RAG Adapter는 아직 미구현이고, 실제 추천은 Mock 데이터와 하드코딩된 우선순위에 크게 의존한다.
6. Redis 연결과 chat history 저장은 구현되어 있으나, 설계서의 Session Flush 요구사항과 비교하면 자동 flush/전체 로그 저장 범위가 부족하다.
7. SQL 상수화 기준이 일부 지켜지지만 `logging_service.py`, `session_flush_service.py`에는 직접 SQL 문자열이 남아 있다.
8. Music Detail API는 엔드포인트만 존재하고, 설계서가 말한 최근 RAG 조회 및 music catalog fallback은 실질적으로 미완성이다.

---

## 2. 설계서 기준 핵심 흐름과 현재 구현 비교

설계서의 고정 흐름은 다음 순서다.

```text
UI
-> API Layer
-> Request Lifecycle Cache
-> Service Layer
-> Orchestrator Agent
-> Input Planner Agent
-> Intent Agent
-> KAG Dispatch Agent
-> Neo4j KAG
-> RAG Dispatch Agent
-> Elasticsearch RAG
-> Recommendation Agent
-> Response Generator Agent
-> Validator
-> CompactStateBuilder
-> Redis / PostgreSQL
-> UI
```

현재 `OrchestratorAgent`의 챗봇 흐름은 다음에 가깝다.

```text
KAG Dispatch
-> Contract Validator
-> RAG Dispatch
-> Intent Agent
-> Recommendation Agent
-> Response Generator
-> Response Validator
-> Provenance Validator
```

따라서 사용자가 지적한 “user_input을 먼저 LLM/Input Planner가 분석하고 JSON으로 만든 뒤 KAG로 가야 하는 것 아닌가”라는 의문은 타당하다. 설계서 기준으로는 `InputPlannerAgent`가 먼저 `INTENT_STATE`와 `KAG_INPUT_JSON`을 생성해야 한다.

관련 구현:

- `app/agents/orchestrator_agent.py`: `run_chatbot()`에서 `self._kag.run(...)`이 먼저 실행된다.
- `app/agents/input_planner_agent.py`: 구현은 있으나 orchestrator에서 호출되지 않는다.

판정: **설계서와 충돌**

---

## 3. 파일별 점검

### 3.1 `app/agents/input_planner_agent.py`

사용자 지적:

- `_detect_candidates`, `_detect_situations`, `_decide_intent_type`가 키워드 기반 하드코딩이다.
- 원래 LLM으로 사용자 입력을 이해하고 `input_json`을 만들려던 것 아닌지 확인 필요.

분석:

- 현재 구현은 키워드 매칭 기반이다.
- `IntentStateSchema`, `KagInputSchema`를 생성하기는 하지만 실제 orchestrator 흐름에 연결되어 있지 않다.
- 설계서에는 LLM이 Input Planning 구간에서 사용 가능하다고 되어 있다.
- 다만 LLM이 완전히 자유롭게 mood/genre/situation을 만들면 안 된다. 설계서상 `allowed_intent_types`, `allowed_genres`, `allowed_moods`, `allowed_situations` 안에서 정규화해야 한다.

판정:

- 키워드 기반 fallback 자체는 설계서의 “RuleBasedInputPlanner fallback” 방향과 충돌하지 않을 수 있다.
- 하지만 현재처럼 LLM 기반 Input Planning이 흐름에 없고, `InputPlannerAgent`도 orchestrator에서 사용되지 않는 것은 설계서와 충돌한다.
- “LLM이 자유롭게 카테고리를 분류”하는 방식은 설계서 위반 가능성이 있다. LLM은 허용 enum 안에서만 정규화해야 한다.

권장 확인:

- MVP에서 Input Planner를 rule-based로 유지할지, Cloud LLM 기반으로 우선 연결할지 결정 필요.
- 어느 경우든 결과는 `KAG_INPUT_JSON` 계약과 enum 검증을 통과해야 한다.

---

### 3.2 `app/agents/intent_agent.py`

사용자 지적:

- `_classify`가 하드코딩이다.
- 분류 rule을 정책으로 정리하거나 enum 기반으로 관리하는 것이 좋아 보인다.

분석:

- 현재 `_classify()`는 문자열 포함 여부로 intent를 분류한다.
- 더 큰 문제는 반환값이 설계서의 허용 intent와 다르다는 점이다.

설계서 허용 intent:

```text
personalized_recommendation
new_release_recommendation
discovery_recommendation
music_information
recommendation_reason
general_chat
```

현재 `IntentAgent` 반환 가능 값:

```text
recommendation_reason_question
new_release_recommendation
similar_taste_recommendation
music_information_question
new_taste_discovery
personalized_recommendation
general_chat
```

판정: **명확한 설계서 충돌**

권장 확인:

- `IntentAgent`는 `InputPlannerAgent`가 만든 `INTENT_STATE`를 검증/확정하는 역할로 되돌리는 것이 설계서에 맞다.
- intent enum은 `app/schemas/intent_state_schema.py` 또는 `app/common/constants.py` 중 하나를 단일 기준으로 정해야 한다.

---

### 3.3 `app/agents/orchestrator_agent.py`

사용자 지적:

- 흐름상 LLM/Input Planner가 먼저 user input을 분석해야 하는데 빠진 것 같다.
- `run_recommendation()`은 LLM 없이 동작하는 것은 동의하지만 기존 유저 정보 기반 추천과 신규 유저 fallback/sorting이 필요해 보인다.

분석:

- 챗봇 흐름에서 `InputPlannerAgent` 호출이 없다.
- `IntentAgent`도 KAG/RAG 이후에 실행된다.
- 설계서 기준 Chatbot Flow는 `Input Planner -> INTENT_STATE/KAG_INPUT_JSON -> Intent Agent -> KAG -> RAG` 순서다.
- Main Recommendation Flow는 “LLM Response Generation 없이도 동작 가능”하다고 되어 있으나, Input Planner와 Intent 검증은 여전히 실행되어야 한다고 명시되어 있다.
- 현재 `run_recommendation()`은 `self._kag.run(user_id, "", session_context)`와 `self._rag.run(kag_state)`만 실행한다.

판정: **설계서와 충돌**

신규 유저 sorting 관련:

- 설계서에는 “신규 유저는 sorting으로 추천한다”는 요구가 명시되어 있지 않다.
- 설계서 기준으로는 session context, Spotify metadata, Neo4j relationship, Elasticsearch evidence 기반이어야 한다.
- 신규 유저 cold-start 전략은 요구사항으로 추가하려면 별도 확인이 필요하다.

---

### 3.4 `app/agents/rag_dispatch_agent.py`

사용자 지적:

- `kag_state`를 받는 것은 맞지만 user query도 받아야 할 것 같다.
- JSON을 어디에서 받는지 불명확하다.

분석:

- 설계서상 RAG Dispatch Agent는 `RAG_INPUT_JSON`을 생성해야 한다.
- `RAG_INPUT_JSON`에는 `query_text`, `intent_type`, `kag_recommended_content_ids`, `target_section`, `evidence_need`, `retrieval_constraints`가 포함된다.
- 현재 `RagDispatchAgent.run()`은 `kag_state` 하나만 받고, `RagInputSchema`를 생성하지 않는다.
- `app/schemas/rag_input_schema.py`는 존재하지만 실행 흐름에서 사용되지 않는다.

판정: **설계서와 충돌**

권장 확인:

- `RAG_INPUT_JSON` 생성 책임을 `RagDispatchAgent`가 가질지, 별도 builder가 가질지 결정 필요.
- user query는 `InputPlannerAgent`의 `normalized_query` 또는 `KAG_INPUT_JSON.query_context.normalized_query`에서 전달되는 구조가 설계서에 가장 가깝다.

---

### 3.5 `app/agents/recommendation_agent.py`

사용자 지적:

- `priority`, `_CATEGORY_SECTION_MAP` 등 하드코딩이 많다.

분석:

- 현재 추천 선택 우선순위와 section mapping이 코드 내부에 직접 있다.
- 설계서에는 `RecommendationPolicy.md`, `RankingPolicy.md`, `PromptPolicy.md`로 정책을 분리한다고 되어 있다.
- 현재 저장소에는 설계서에 적힌 `app/policies/RecommendationPolicy.md`, `RankingPolicy.md`, `PromptPolicy.md` 구조가 확인되지 않았다.
- `score`도 `1.0 - rank * 0.05` 방식으로 단순 계산된다.
- `source`가 항상 `{"kag": False, "rag": True}`로 반환된다. 설계서상 selected recommendation은 KAG/RAG 기반 여부를 반영해야 하므로, KAG 기반 추천 후보임을 잃는 구조다.

판정: **설계서와 부분 충돌**

권장 확인:

- 정책 문서 파일을 실제로 만들고, 코드가 해당 정책에 맞게 따르도록 할지 결정 필요.
- 단, 정책 파일을 만든다는 요구는 설계서에는 있지만 현재 구현 단계에서 어디까지 해야 하는지는 별도 확인이 필요하다.

---

### 3.6 `app/api/music_detail_routes.py`, `app/services/music_detail_service.py`

사용자 지적:

- 상세 구성이나 내용이 부족하다.
- 노래 기본 정보, 취향과 얼마나 맞는지/다른지도 보여주면 좋겠다.

분석:

- Music Detail API 엔드포인트는 존재한다.
- 하지만 라우터는 `content_id`만 넘기고 최근 `RAG_STATE`를 조회하지 않는다.
- 서비스는 `recent_rag_state`가 없으면 `title`, `artist`, `display_reason`, `evidence_summary`를 빈 문자열로 반환한다.
- 설계서상 Music Detail Flow는 “최근 RAG_STATE 조회 -> content_id 기반 evidence 조회 -> 없으면 music_catalog 조회 -> MusicDetailViewModel 생성”이다.
- 현재 구현은 “없으면 music_catalog 조회”가 실제로 구현되어 있지 않다.

판정: **설계서와 충돌 / 기능 미완성**

취향 일치도 표시 관련:

- “내 취향과 얼마나 맞는지/다른지”는 좋은 UX 아이디어지만, 기준 설계서의 Music Detail 필수 계약에는 명확히 정의되어 있지 않다.
- 추가하려면 `MUSIC_DETAIL_VIEW_MODEL` 계약 확장이 필요하므로 확인 후 진행해야 한다.

---

### 3.7 `app/cache/redis_client.py`, `app/cache/session_history_cache.py`, `app/services/session_flush_service.py`

사용자 지적:

- Redis에 있던 캐시 데이터가 세션 종료 시 PostgreSQL에 들어가야 할 것 같다.
- `set/get`만 있는 것 같고 실제 연결/히스토리 저장 확인이 필요하다.
- README에 Redis 링크/설명이 부족해 보인다.

분석:

- Redis 연결은 `redis.ConnectionPool` 기반으로 구현되어 있다.
- Docker Compose에서도 backend가 `REDIS_HOST=redis`로 Redis 서비스에 연결하도록 되어 있고, Redis healthcheck도 있다.
- chat history는 `rimas:session:{session_id}:history` 리스트에 `lpush`로 저장된다.
- session context는 `rimas:session:{session_id}:context` JSON string으로 저장된다.
- `session_flush_service.py`는 Redis history를 `chat_sessions`, `chat_session_turns`에 저장하고 Redis 세션을 삭제한다.

부족한 점:

- 설계서의 Session Flush Flow에는 `interaction_logs` 저장도 포함되어 있으나, 현재 flush 구현은 `interaction_logs`를 쓰지 않는다.
- TTL 만료 전에 자동 flush하는 백그라운드 흐름은 없다.
- Redis 오류는 `redis_client.py`에서 대부분 로그 후 `None` 또는 빈 배열로 반환되어, 상위 계층에서 Redis 장애를 명확히 구분하기 어렵다.
- README는 Redis 역할은 설명하지만, Redis key 구조와 flush API 사용 예시는 부족하다.

판정: **부분 구현 / 설계서 대비 부족**

---

### 3.8 `app/common/constants.py`

사용자 지적:

- `DEFAULT_USER_ID`가 하드코딩처럼 보인다.
- `ALLOWED_MOODS`, `ALLOWED_SITUATIONS`, `ALLOWED_GENRES`가 너무 적고 하드코딩 같다.
- LLM이 자율적으로 분류하면 안 되는지 확인 필요.

분석:

- 설계서상 allowed enum은 존재해야 한다. Input Planner Prompt 규칙에도 허용 목록 안에서만 선택한다고 되어 있다.
- 따라서 allowed enum 자체는 설계서와 충돌하지 않는다.
- 문제는 목록이 너무 적고, 데이터 소스 또는 정책 문서와 동기화되는 구조가 아니라 코드 상수에 고정되어 있다는 점이다.
- `DEFAULT_USER_ID`는 로컬/샘플 실행에는 유용할 수 있지만 운영 경로에서 기본 사용자로 암묵 사용되면 위험하다.

판정:

- allowed enum 존재: **설계서상 허용**
- enum 값 부족 및 관리 위치 불명확: **개선 필요**
- LLM 자유 분류: **설계서 위반 가능성 있음**

---

### 3.9 `app/common/default_state.py`

사용자 지적:

- fallback이 단일 메시지라서 다양한 실패 이유와 재질문 유도가 부족하다.

분석:

- 현재 fallback은 하나의 `FALLBACK_RESPONSE_STATE`만 제공한다.
- 설계서에는 `fallback_messages.py`가 LLM 실패, Parser 실패, Validator 실패 별 고정 응답을 관리한다고 되어 있다.
- 현재 설계서의 `app/prompts/fallback_messages.py` 구조는 저장소에 확인되지 않았다.

판정: **설계서 대비 부족**

주의:

- fallback을 다양화하려면 실패 유형별 계약과 UI 표시 정책을 먼저 확정해야 한다.

---

### 3.10 `app/config/settings.py`

사용자 지적:

- `getenv`에 default를 주는 것이 보안적으로 맞는지 의문이다.

분석:

- 현재 DB/Redis/Neo4j/OpenAI 설정은 환경변수에서 읽고, 없으면 로컬 기본값을 사용한다.
- Docker Compose도 개발용 기본 password를 제공한다.
- 로컬 개발 환경에서는 기본값이 편의성을 높인다.
- 운영 환경에서는 secret에 default를 두는 것은 위험하다. 특히 DB/Neo4j password가 비어 있거나 기본값으로 동작하면 배포 환경에서 문제가 된다.

판정: **개발 환경은 허용 가능, 운영 기준으로는 보안 정책 미흡**

권장 확인:

- 이 프로젝트가 수업/로컬 실행 기준인지, 배포 가능한 운영 기준까지 요구하는지 확인 필요.
- 운영 기준이면 필수 secret 누락 시 기동 실패하도록 바꾸는 정책이 필요하다.

---

### 3.11 `self-check.md`

사용자 지적:

- `app/core` 폴더가 설계서 Folder Structure에 없다.

분석:

- 실제 저장소에는 `app/core/middleware.py`, `app/core/logging_config.py`가 존재한다.
- 설계서의 Folder Structure에는 `app/core`가 없다.
- `self-check.md`에는 `app/core`가 포함되어 현재 구조를 더 잘 반영한다.

판정: **설계서 문서 업데이트 필요**

주의:

- `app/core` 자체가 문제라기보다는, 설계서와 실제 구조가 동기화되지 않은 것이 문제다.

---

### 3.12 `app/kag/adapters/mock_kag_adapter.py`

사용자 지적:

- Mock이라도 너무 하드코딩이다.
- LLM 분석으로 변경할 수 있는지 확인 필요.

분석:

- 현재 Mock KAG는 항상 `track_001`, `track_002`, `track_003`을 반환한다.
- primary goal, route, target section도 키워드 기반이다.
- Mock Adapter이므로 고정 데이터는 테스트/로컬 흐름 검증 목적에서는 허용 가능하다.
- 하지만 설계서상 KAG는 Neo4j graph traversal 담당이고, RealKagAdapter는 아직 `NotImplementedError` 상태다.

판정:

- Mock 고정 데이터: **테스트용으로는 허용 가능**
- 현재 서비스가 실제 KAG처럼 동작한다고 보기에는 부족: **기능 미완성**
- Mock KAG를 LLM으로 대체: **비권장 / 설계서 위반 가능성 큼**

이유:

- 설계서에서 LLM은 추천 후보, content_id, KAG_STATE를 생성하면 안 된다.
- KAG 후보는 Neo4j/데이터 기반으로 생성되어야 한다.
- LLM은 Input Planning 보조에는 사용할 수 있지만 KAG 결과 생성자로 쓰면 안 된다.

---

### 3.13 `app/llm/response_state_schema.py`

사용자 메모:

- 전반적인 state는 나쁘지 않아 보인다.

분석:

- JSON Schema 형태로 `RESPONSE_STATE` 계약을 정의하고 있다.
- `additionalProperties: False`가 있어 LLM 응답의 불필요한 필드 유입을 막는 방향은 설계서와 맞다.
- 다만 설계서에는 prompt output schema 폴더 구조가 별도로 정의되어 있는데, 현재는 `app/llm/response_state_schema.py`에 위치한다.

판정: **계약 방향은 적절하나 설계서 폴더 구조와는 일부 차이**

---

### 3.14 `app/schemas/intent_state_schema.py`

사용자 지적:

- `IntentType`과 `ALLOWED_INTENT_TYPES`가 중복처럼 보인다.

분석:

- `IntentType`은 Pydantic 타입 검증용 Literal이다.
- `ALLOWED_INTENT_TYPES`는 런타임 상수 set이다.
- 둘 다 같은 목록을 유지해야 하는데, 현재는 중복 정의라 drift 위험이 있다.
- 실제로 `IntentAgent`는 둘과 다른 intent 값을 반환하고 있다.

판정: **중복 관리 위험 / 현재 구현과 충돌**

권장 확인:

- `IntentType`을 단일 기준으로 두고 `ALLOWED_INTENT_TYPES`를 거기서 파생할지, 반대로 constants를 기준으로 schema를 만들지 결정 필요.

---

### 3.15 `app/services/compact_state_builder.py`

사용자 질문:

- 왜 compact하게 진행하는지, 최소 필요한 변수만 프론트로 전달하는 것인지?

설명:

- 맞다. 설계서상 CompactStateBuilder는 내부 Full State에서 프론트/API 응답에 필요한 최소 필드만 남기는 계층이다.
- 내부 `retrieval_trace`, `validator_trace`, strategy 내부값, raw metadata를 고객 응답에 노출하지 않기 위한 목적이다.
- 현재 구현도 `kag_state`, `rag_state`, `response_state`에서 제한된 필드만 골라 반환한다.

판정: **설계서 방향과 대체로 일치**

주의:

- `main_recommendation_service.py`의 응답에는 `debug`에 `session_context`, `kag_state`, `rag_state`가 그대로 포함된다.
- 설계서상 Developer Debug Panel은 허용되지만, 고객 응답에 raw JSON을 노출하면 안 된다.
- 이 `debug`가 실제 사용자 화면/API 응답에 그대로 노출되는지 확인이 필요하다.

---

### 3.16 `app/services/logging_service.py`, `app/services/session_flush_service.py`

사용자 지적:

- SQL 쿼리문을 하드코딩하지 말고 상수/클래스로 관리해야 한다.

분석:

- `app/repositories/query_constants.py`는 존재한다.
- `interaction_log_repository.py`는 query constants를 사용한다.
- 그러나 `logging_service.py`와 `session_flush_service.py`는 직접 multiline SQL을 포함한다.
- 설계서 구현 금지 규칙에도 “직접 SQL 문자열 남발” 금지가 있다.

판정: **설계서 및 사용자 기준과 충돌**

권장 확인:

- 서비스 계층에서 직접 SQL을 유지할지, repository 계층으로 옮길지 결정 필요.
- 기준 설계서의 package boundary를 따르면 repository/query_constants로 이동하는 것이 더 맞다.

---

### 3.17 `app/services/music_detail_service.py`

사용자 지적:

- 노래 기본 정보와 취향 일치/차이를 보여주면 좋겠다.

분석:

- 현재 서비스는 최근 RAG evidence가 있을 때만 제목/아티스트/장르/무드를 채운다.
- 라우터가 recent RAG state를 넘기지 않기 때문에 일반 API 호출에서는 대부분 빈 상세가 반환될 수 있다.
- music_catalog 조회 fallback이 없다.

판정: **설계서 대비 미완성**

추가 기능 관련:

- 취향 일치도/차이 설명은 설계서에 명시된 필드는 아니다.
- 구현하려면 `MusicDetailViewModelSchema` 확장과 RAG evidence 또는 session context 기반 계산 정책이 필요하다.

---

### 3.18 `app/services/request_lifecycle_cache.py`

사용자 질문:

- 역할이 애매하다.

설명:

- 의도는 동일 `request_id`가 동시에 중복 실행되는 것을 막는 것이다.
- 설계서의 “중복 API 호출 및 중복 Retrieval 방지”에 대응한다.
- 현재 구현은 단일 프로세스 메모리 set 기반이다.

문제:

- 실제 API/service 흐름에서 사용되는 곳이 확인되지 않는다.
- 다중 프로세스/다중 컨테이너에서는 프로세스별 메모리 set이 분리되어 중복 차단이 안 된다.
- request_id 생성/전달 정책도 API 계약에 명확히 드러나지 않는다.

판정: **스켈레톤만 구현 / 실제 흐름 미연결**

---

### 3.19 `data/processed`

사용자 질문:

- 왜 있는지 확인 필요.

분석:

- `data/processed/matched_spotify_enriched.csv`가 존재하며 약 46MB 크기다.
- 이름상 Spotify 관련 가공 데이터로 보인다.
- 설계서상 Spotify metadata는 추천 기준의 핵심 데이터이므로 데이터 폴더 자체는 이상하지 않다.
- 다만 현재 RAG/KAG 실제 adapter가 미구현이라 이 파일이 실제 서비스 흐름에서 사용되는지는 별도 확인이 필요하다.

판정: **존재 자체는 타당 / 사용 경로 확인 필요**

---

### 3.20 `db/seed.sql`

사용자 질문:

- mock 데이터인지, 임의 값처럼 보인다.

분석:

- `users` 3명과 `music_catalog` 3곡을 넣는 seed다.
- `track_001`, `track_002`, `track_003`은 Mock KAG/RAG가 쓰는 ID와 맞춰져 있다.
- 따라서 현재 seed는 “최소 동작 확인용 샘플/목 성격의 canonical seed”에 가깝다.

판정: **개발/테스트 seed로는 타당, 실제 데이터 적재로 보기는 부족**

---

### 3.21 `seed`

사용자 질문:

- 왜 있는지 상세 확인 필요.

분석:

- 현재 `seed/`에는 `.gitkeep`만 있다.
- 실제 시드 SQL은 `db/seed.sql`에 있다.
- 따라서 현재 `seed/`는 비어 있는 예약 폴더다.

판정: **현재 기능 없음 / 정리 또는 용도 문서화 필요**

---

## 4. 공통 질문 답변

### 4.1 state, input state, output state를 왜 나누는가?

설계서 기준으로 state는 역할이 다르다.

`KAG_INPUT_JSON`:

- KAG가 사용할 입력 계약이다.
- user input, session context, intent, mood/genre/situation 후보를 구조화한 값이다.
- 추천 결과가 아니라 “KAG에게 무엇을 탐색하라고 요청할지”를 담는다.

`KAG_STATE`:

- KAG 실행 결과다.
- 추천 목표, 경로, target section, 후보 content id 등을 담는다.
- 설계상 Neo4j graph traversal 결과여야 한다.

`RAG_INPUT_JSON`:

- RAG가 사용할 입력 계약이다.
- KAG가 고른 content id, target section, query text, evidence need를 담는다.

`RAG_STATE`:

- RAG 실행 결과다.
- 추천 후보의 title, artist, evidence_summary, retrieval_trace 등을 담는다.
- 설계상 Elasticsearch evidence retrieval 결과여야 한다.

`RESPONSE_STATE`:

- 사용자에게 반환할 최종 응답 계약이다.
- 자연어 응답, 표시 추천 목록, 사용된 content id를 담는다.

`Internal Full State`와 `Transport Compact State`:

- Full State는 내부 agent/validator/debug/provenance를 위해 상세 정보를 보관한다.
- Compact State는 프론트/API 전송용으로 최소 필드만 남긴다.
- trace와 내부 전략을 외부에 노출하지 않기 위해 분리한다.

현재 구현은 schema 파일들은 어느 정도 존재하지만, `KAG_INPUT_JSON`과 `RAG_INPUT_JSON`이 실제 agent 흐름에 충분히 연결되지 않았다.

---

### 4.2 Redis 연결과 chat history 저장은 맞는가?

현재 기준으로는 Redis 연결 구조와 chat history 저장 구조는 있다.

- Docker Compose에서 backend는 `REDIS_HOST=redis`로 연결한다.
- Redis 서비스는 `redis:7-alpine`이고 healthcheck가 있다.
- `session_history_cache.py`는 history와 context key를 분리한다.
- 챗봇 응답 후 `session_cache_service.save_turn_and_update_context()`가 호출되어 history와 context를 Redis에 저장한다.

하지만 부족한 점도 있다.

- Redis 장애 시 명확한 실패 응답보다는 빈 값으로 진행될 수 있다.
- 세션 flush는 API 호출 기반이고 TTL 만료 시 자동 flush는 없다.
- flush 시 `chat_sessions`, `chat_session_turns`는 저장하지만 설계서에 있는 `interaction_logs` flush는 구현되어 있지 않다.
- README에는 Redis 역할은 있으나 key 구조, flush API 사용 예시, Redis 확인 명령은 부족하다.

판정: **연결 구조는 있음 / 운영적 완성도와 문서화는 부족**

---

## 5. 충돌·이상 징후 우선순위

### 높음

1. `OrchestratorAgent` 실행 순서가 설계서와 다르다.
2. `InputPlannerAgent`가 실제 흐름에 연결되어 있지 않다.
3. `IntentAgent` 반환 intent가 설계서 enum과 다르다.
4. `RAG_INPUT_JSON`이 실제 흐름에서 사용되지 않는다.
5. Real KAG/RAG Adapter가 미구현이다.
6. Music Detail이 설계서의 최근 RAG 조회 및 music_catalog fallback을 구현하지 않는다.

### 중간

1. Recommendation 정책이 코드 내부 하드코딩이고 정책 문서 구조가 없다.
2. SQL이 일부 서비스에 직접 작성되어 있다.
3. RequestLifecycleCache가 실제 API/service 흐름에 연결되어 있지 않다.
4. Redis flush가 설계서의 전체 저장 범위와 자동화 기대에 못 미친다.
5. fallback 메시지가 단일 상태에 가깝다.

### 낮음 또는 문서 정리

1. `app/core`가 설계서 Folder Structure에 없다.
2. `seed/`는 현재 예약 폴더로만 존재한다.
3. README에 Redis key/flush/확인 방법 설명이 부족하다.
4. `data/processed`의 실제 사용 흐름이 문서화되어 있지 않다.

---

## 6. 구현 전 확인이 필요한 결정 사항

아래는 함부로 구현하면 안 되고, 먼저 결정이 필요한 항목이다.

1. Input Planner를 Cloud LLM 기반으로 연결할 것인가, rule-based fallback을 MVP 기본으로 둘 것인가?
2. `IntentType`의 단일 기준을 `schemas.intent_state_schema.IntentType`으로 둘 것인가, `common.constants.ALLOWED_INTENT_TYPES`로 둘 것인가?
3. `RAG_INPUT_JSON` 생성 책임을 `RagDispatchAgent` 내부에 둘 것인가, 별도 builder/service로 분리할 것인가?
4. Mock KAG/RAG는 테스트 전용으로 유지하고 Real Adapter를 구현할 것인가?
5. Recommendation/Ranking/Prompt 정책 문서를 실제 `app/policies/`로 만들고 코드가 이를 따르게 할 것인가?
6. Music Detail에 “취향 일치도/차이”를 추가할 것인가? 추가한다면 ViewModel 계약을 어떻게 확장할 것인가?
7. 운영 환경에서 secret 기본값을 허용할 것인가, 누락 시 기동 실패로 바꿀 것인가?
8. Redis TTL 만료 시 자동 PostgreSQL flush까지 요구할 것인가, API flush만 MVP 범위로 둘 것인가?

---

## 7. 최종 판단

사용자가 이상하다고 본 지점 대부분은 실제로 설계서 기준에서 확인할 가치가 있다. 특히 agent 흐름, intent enum, RAG input 계약, Real Adapter 미구현, Music Detail 미완성, SQL 위치 문제는 단순 취향 문제가 아니라 설계서와 현재 구현의 정합성 문제다.

반대로 `ALLOWED_MOODS`, `ALLOWED_GENRES`, `ALLOWED_SITUATIONS` 같은 enum 자체는 설계서상 필요한 장치다. 이 부분을 LLM 자유 분류로 바꾸는 것은 안전하지 않다. 올바른 방향은 LLM이 사용자 입력을 해석하되, 결과는 반드시 허용 enum과 Runtime Contract 검증을 통과하도록 제한하는 것이다.

현재 단계에서 가장 먼저 정리해야 할 것은 코드 수정이 아니라 실행 흐름의 기준 확정이다. 특히 `InputPlannerAgent -> IntentAgent -> KAG -> RAG` 순서를 설계서대로 복원할지, 현재 구현 흐름을 새 기준으로 문서화할지 먼저 결정해야 한다.

---

## 8. 구조·모듈화·리팩토링 점검 (2026-05-14)

이 섹션은 설계서 정합성과 무관하게 현재 코드 자체의 구조적 문제점을 정리한다.
소스 수정은 하지 않았으며, 수정이 필요한 항목과 근거만 기록한다.

---

### 8.1 `session_cache_service.py` — 의미 없는 thin wrapper

**파일**: `app/services/session_cache_service.py`

현재 코드가 하는 일:

```python
def load_context(session_id, user_id=None):
    return cache.get_context(session_id, user_id=user_id)

def save_turn_and_update_context(...):
    cache.append_turn(...)
    cache.update_context_from_turn(...)
```

`session_history_cache`를 1:1로 위임만 하고 추가 로직이 없다. 현재 구조에서 이 파일은 `import alias`와 다를 바 없고, 호출 경로만 늘려 가독성을 해친다.

**수정 방향**:
- 서비스 계층이 캐시를 직접 쓰거나
- 이 파일에 실제 비즈니스 판단(예: degraded 모드 처리, 컨텍스트 병합 정책)을 담거나
- 둘 중 하나를 선택해야 한다. 현재 상태는 양쪽 어느 쪽도 아니다.

---

### 8.2 `_merge_unique` 함수 중복 정의

**파일 A**: `app/cache/session_history_cache.py:127`
**파일 B**: `app/services/taste_event_service.py:67`

두 파일에 각각 `_merge_unique(existing, new_items, limit)` 함수가 정의되어 있고, 로직도 유사하다.

```python
# session_history_cache.py
def _merge_recent(existing: list, new_items: list, limit: int) -> list:
    merged = new_items + [x for x in existing if x not in new_items]
    return merged[:limit]

# taste_event_service.py
def _merge_unique(existing: list, new_items: list, limit: int) -> list:
    merged = new_items + [x for x in existing if x not in new_items]
    return merged[:limit]
```

코드가 완전히 동일하다. 하나가 수정되면 다른 하나는 버그가 생기는 구조다.

**수정 방향**: `app/common/` 또는 `app/utils/` 아래 공용 유틸리티로 추출하고 두 곳에서 import해서 사용한다.

---

### 8.3 `rag/` 내부 이중 디렉토리 구조

**경로 A**: `app/rag/ragStateBuilder/` — `builder.py`, `edges.py`, `nodes.py`, `schema.py`
**경로 B**: `app/rag/builders/` — `rag_state_builder.py`

같은 목적처럼 보이는 두 디렉토리가 공존한다. 어느 쪽이 실제 사용 중인지, 어느 쪽이 구버전인지 코드만으로는 명확하지 않다.

추가로 `app/rag/adapters/rag_adapter.py`와 `app/rag/adapters/rag_real_adapter.py`도 역할이 겹쳐 보인다.

**수정 방향**:
- 실제 import 경로를 추적해 사용 중인 쪽을 확인하고, 미사용 디렉토리를 제거하거나 통합한다.
- 어느 쪽을 쓸지 결정하고 나머지를 삭제한다.

---

### 8.4 검증 레이어가 두 곳에 분산

**경로 A**: `app/validators/` — `base_validator.py`, `contract_validator.py`, `response_validator.py`, `provenance_validator.py`, `display_reason_validator.py`
**경로 B**: `app/rag/contractValidator/` — `base_validator.py`, `format_validator.py`, `hallucination_validator.py`, `logic_validator.py`

최상위 `validators/`와 `rag/contractValidator/` 둘 다 계약 검증 코드를 포함한다. `base_validator.py`가 두 곳에 각각 존재한다.

**수정 방향**:
- RAG 전용 검증이 맞다면 `app/rag/contractValidator/`는 `app/rag/validators/`로 이름을 바꾸고 역할을 명확히 한다.
- 최상위 `BaseValidator`를 공용 기반 클래스로 사용하도록 정리한다.
- 같은 이름의 `base_validator.py`가 두 곳에 있으면 import 혼란이 생긴다.

---

### 8.5 `BaseAgent` 인터페이스가 너무 느슨함

**파일**: `app/agents/base_agent.py`

```python
class BaseAgent(ABC):
    @abstractmethod
    def run(self, **kwargs) -> dict:
        raise NotImplementedError
```

`run(**kwargs) -> dict`는 시그니처가 없어서:
- 각 Agent가 어떤 인자를 필수로 받아야 하는지 강제할 수 없다.
- IDE에서 타입 힌트가 나오지 않는다.
- 잘못된 인자를 넘겨도 정적 분석이 잡아주지 못한다.

현재 각 Agent가 실제로 받는 파라미터는 모두 다르고, 기반 클래스는 이를 전혀 표현하지 않는다.

**수정 방향 (선택)**:
- `BaseAgent`를 마커 클래스로만 유지하고 타입 문서를 각 구현체에 충분히 작성한다.
- 또는 Protocol이나 Generic을 사용해 각 Agent의 입출력 계약을 명시한다.
- 최소한 각 `run()` 구현체에 파라미터 타입 힌트라도 완성한다 (현재 일부만 있음).

---

### 8.6 라우터에 모듈 레벨 싱글톤 생성

**파일**: `app/api/chatbot_routes.py:15-16`

```python
_service = ChatbotService()
_stream_service = ChatbotStreamService(chatbot_service=_service)
```

모듈 import 시 즉시 `ChatbotService()`가 생성된다. `ChatbotService`는 내부에서 `OrchestratorAgent`를, `OrchestratorAgent`는 `OpenAiLlmClient`를 생성하려 시도한다. DB/Redis 연결 없이 import만 해도 초기화 오류가 발생할 수 있다.

`recommendation_routes.py`, `taste_routes.py` 등도 동일한 패턴이다.

**수정 방향**:
- FastAPI의 `Depends()`를 사용하거나
- `@app.on_event("startup")` / `lifespan`에서 초기화하거나
- 최소한 함수 레벨로 지연 초기화(`_service = None` + `def get_service()`)를 적용한다.

---

### 8.7 `main_recommendation_service.py`의 `debug` 필드 정보 노출

**파일**: `app/services/main_recommendation_service.py:125-142`

```python
return {
    ...
    "debug": {
        "session_context": session_context,
        "kag_state": kag_state,
        "rag_state": rag_state,
        "latency_ms": latency_ms,
    },
}
```

`session_context`(사용자 취향, 싫어하는 아티스트 목록), `kag_state`, `rag_state`(내부 추천 전략) 전체가 API 응답에 포함된다. 프론트엔드가 이를 렌더링하지 않더라도 네트워크 응답에 노출된다.

**수정 방향**:
- `APP_ENV == "prod"`일 때는 `debug` 키를 응답에서 제거한다.
- 또는 `compact_state_builder`를 통해 내부 state가 외부로 나가지 않도록 한다.
- 8.6의 라우터 싱글톤과 함께 수정하면 환경 변수 기반 분기가 자연스럽게 가능하다.

---

### 8.8 `InputPlannerAgent._detect_candidates`의 키워드 맵 혼재

**파일**: `app/agents/input_planner_agent.py:147-161`

`_detect_candidates()`는 mood와 genre 모두를 처리하는 공용 함수인데, 내부 `keyword_map`에 mood(`calm`, `night`, `bright`)와 genre(`indie`, `dream_pop`, `ambient`, `rnb`)가 섞여 있다. 함수는 `allowed` 파라미터로 걸러내지만, 매핑 테이블 자체가 분류 없이 합쳐져 있다.

```python
keyword_map = {
    "calm": [...],      # mood
    "night": [...],     # mood
    "indie": [...],     # genre
    "dream_pop": [...], # genre
}
```

**수정 방향**:
- `MOOD_KEYWORD_MAP`, `GENRE_KEYWORD_MAP`을 `app/common/constants.py`에 분리해 정의한다.
- `_detect_candidates`를 mood/genre별로 각각 호출하거나, 매핑 테이블을 인자로 주입한다.
- `ALLOWED_MOODS`, `ALLOWED_GENRES` 상수와 이 매핑 테이블이 같은 파일에 있어야 동기화가 쉽다.

---

### 8.9 `rag/` 내 설계 문서와 소스코드 혼재

다음 파일들이 소스 코드 트리 안에 존재한다:

- `app/rag/design.md`
- `app/rag/output.md`
- `app/rag/kag_query_implementation_classification.md`
- `app/rag/real_neo4j_kag_adapter_design.md`
- `app/rag/rimas_kag_query_mvp_plan_v_1.md`
- `app/rag/adapters/description.md`
- `app/rag/contractValidator/description.md`
- `app/rag/musicCatalogRepository/description.md`
- `app/rag/ragStateBuilder/description.md`
- `app/rag/services/description.md`

마크다운 설계 문서가 Python 패키지 디렉토리에 섞여 있으면 `glob`이나 패키지 탐색 시 의도치 않게 포함될 수 있고, Python 파일과 문서 파일의 경계가 모호해진다.

**수정 방향**: 최상위 `docs/rag/` 또는 `docs/design/` 아래로 이동한다. 단, 이동 시 git history에서 파일을 추적하기 위해 `git mv`를 사용해야 한다.

---

### 8.10 `IntentType`과 `ALLOWED_INTENT_TYPES` 이중 관리

**파일 A**: `app/schemas/intent_state_schema.py` — `IntentType` Literal
**파일 B**: `app/common/constants.py` — `ALLOWED_INTENT_TYPES` set

동일한 intent 목록이 두 곳에 별도로 정의되어 있다. 하나가 바뀌면 다른 하나도 수동으로 바꿔야 하는 drift 구조다. 실제로 `IntentAgent`는 둘과 다른 값을 반환하고 있어 현재도 이미 불일치 상태다 (섹션 3.2 참조).

**수정 방향**:
- `IntentType` Literal을 단일 기준으로 삼고 `ALLOWED_INTENT_TYPES = set(get_args(IntentType))`으로 파생한다.
- 또는 `constants.py`의 `ALLOWED_INTENT_TYPES`를 기준으로 하고, schema는 `Literal[tuple(ALLOWED_INTENT_TYPES)]`로 참조한다.
- 어느 방향이든 한 곳에서만 관리해야 한다.

---

### 8.11 `TasteEventService`가 session context를 직접 읽고 쓴다

**파일**: `app/services/taste_event_service.py:40-45`

```python
ctx = self._cache.get_context(session_id)
ctx["recent_genres"] = _merge_unique(...)
...
self._cache.set_context(session_id, ctx)
```

서비스 계층이 캐시 객체를 직접 읽어 dict를 수정하고 다시 저장하는 패턴이다. 이는 `session_history_cache.update_context_from_turn()`이 하는 일과 동일한 레이어다. 두 코드 경로가 독립적으로 context를 수정하면 race condition이나 데이터 유실 위험이 있다.

**수정 방향**:
- context 수정은 `session_history_cache`의 함수를 통해서만 하거나
- `update_context_from_taste_event()` 같은 전용 함수를 캐시 레이어에 추가해 서비스가 이를 호출하도록 한다.

---

### 8.12 우선순위 요약

| 항목 | 위험도 | 수정 난이도 |
|------|--------|------------|
| 8.2 `_merge_unique` 중복 | 중 (버그 drift) | 낮음 |
| 8.3 `rag/` 이중 디렉토리 | 중 (혼란) | 중간 |
| 8.4 검증 레이어 분산 | 중 (import 혼란) | 중간 |
| 8.7 `debug` 필드 노출 | 높음 (정보 노출) | 낮음 |
| 8.10 `IntentType` 이중 관리 | 높음 (버그 drift) | 낮음 |
| 8.11 context 직접 수정 | 높음 (race condition) | 중간 |
| 8.1 thin wrapper | 낮음 (가독성) | 낮음 |
| 8.5 `BaseAgent` 시그니처 | 낮음 (타입 안전성) | 중간 |
| 8.6 모듈 레벨 싱글톤 | 중 (초기화 오류) | 중간 |
| 8.8 키워드 맵 혼재 | 낮음 (유지보수) | 낮음 |
| 8.9 문서/코드 혼재 | 낮음 (구조 혼란) | 낮음 |
