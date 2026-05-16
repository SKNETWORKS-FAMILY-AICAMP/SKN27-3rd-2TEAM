# RIMAS v4 설계-구현 추적표

## 문서 목적

이 문서는 `docs/rimas_v_4_integrated_design_updated_final_.md`와 `docs/recommendation-quality-decision-record.md`를 기준으로 현재 구현 상태를 추적한다.

상태 값은 다음 네 가지로 고정한다.

- `구현됨`: 설계서 요구가 현재 코드와 테스트에서 확인된다.
- `부분 구현`: 핵심 구조는 있으나 설계서의 완료 기준까지는 부족하다.
- `미구현`: 설계서에 있으나 현재 구현 근거가 없다.
- `의도적 변경`: 구현이 설계서와 다르며, 별도 설계 결정으로 승인되어야 한다.

## 현재 기준 문서

- `docs/rimas_v_4_integrated_design_updated_final_.md`
- `docs/recommendation-quality-decision-record.md`
- `docs/policies/RecommendationPolicy.md`
- `docs/policies/RankingPolicy.md`
- `docs/policies/PromptPolicy.md`

## 1. 시스템 목표 20개 추적

| 번호 | 설계 목표 | 상태 | 구현 근거 | 보완 필요 사항 |
|---:|---|---|---|---|
| 1 | 사용자 질문 기반 음악 추천 제공 | 구현됨 | `app/api/chatbot_routes.py`, `app/services/chatbot_service.py`, `app/agents/orchestrator_agent.py` | 추천 품질 회귀 테스트 확대 |
| 2 | 음악 메타데이터 기반 추천 이유 생성 | 부분 구현 | `app/agents/recommendation_agent.py`, `app/agents/response_generator.py`, `app/services/music_detail_service.py` | `display_reason` 검증 실패/대체 경로 테스트 추가 |
| 3 | 새로운 취향 탐색 지원 | 구현됨 | `app/agents/input_planner_agent.py`, `app/kag/adapters/real_kag_adapter.py`, `tests/test_discovery_recommendation_flow.py` | 실제 데이터 기반 discovery section 통합 테스트 |
| 4 | 자연스러운 DJ 큐레이터 스타일 응답 생성 | 부분 구현 | `app/agents/response_generator.py`, `app/services/chatbot_stream_service.py` | PromptPolicy 기반 응답 parser/validator 경계 강화 |
| 5 | 추천 근거 기반 안전한 응답 제공 | 부분 구현 | `app/validators/provenance_validator.py`, `app/validators/display_reason_validator.py` | provenance 실패 fallback 테스트 추가 |
| 6 | 세션 기반 누적 맥락 유지 | 구현됨 | `app/cache/session_history_cache.py`, `app/services/session_cache_service.py` | Redis 장애 시 degraded 동작 테스트 보강 |
| 7 | Validator 기반 hallucination 차단 | 부분 구현 | `app/validators/*`, `app/agents/orchestrator_agent.py` | 모든 contract boundary 검증 적용 필요 |
| 8 | Runtime Contract 기반 Agent 구조 유지 | 부분 구현 | `app/schemas/*`, `app/contracts/fields.py` | `KAG_INPUT_JSON`, `RAG_INPUT_JSON` 검증 누락 보완 |
| 9 | React 기반 서비스형 UI 제공 | 부분 구현 | `frontend/src/pages/*`, `frontend/src/components/*` | `MusicDetailPage`, `NotFoundPage`, debug panel 정책 결정 |
| 10 | Neo4j 기반 관계형 추천 제공 | 구현됨 | `app/kag/adapters/real_kag_adapter.py`, `app/kag/constant.py`, `neo4j/*` | Docker 통합 검증 보강 |
| 11 | Elasticsearch 기반 설명 근거 검색 제공 | 구현됨 | `app/rag/adapters/rag_real_adapter.py`, `app/rag/services/elasticsearch_retriever.py` | 실제 ES index 데이터 품질 검증 |
| 12 | Redis 기반 세션 컨텍스트 유지 | 구현됨 | `app/cache/redis_client.py`, `app/cache/redis_keys.py`, `app/cache/session_history_cache.py` | TTL 만료/복구 테스트 |
| 13 | PostgreSQL 기반 영속 로그 저장 | 부분 구현 | `db/schema.sql`, `app/services/logging_service.py`, `app/services/main_recommendation_service.py`, `app/services/chatbot_service.py`, `app/services/session_flush_service.py` | 실제 DB 통합 검증 필요 |
| 14 | Music Detail 기반 상세 추천 정보 제공 | 구현됨 | `app/api/music_detail_routes.py`, `app/services/music_detail_service.py`, `frontend/src/components/recommendation/MusicDetailModal.tsx` | URL 직접 진입 라우팅 정책 정리 |
| 15 | KAG/RAG 병렬 개발 가능 구조 유지 | 구현됨 | `app/kag/adapters/*`, `app/rag/adapters/*` | adapter contract 테스트 확대 |
| 16 | Mock Adapter와 Real Adapter 교체 가능 구조 | 구현됨 | `RIMAS_KAG_MODE`, `RIMAS_RAG_MODE`, dispatch agent 구현 | 설정별 smoke 테스트 |
| 17 | 중복 API 호출 및 중복 retrieval 방지 | 부분 구현 | `app/services/request_lifecycle_cache.py`, API 라우터의 `request_id` 처리 | streaming/error 경로 dedupe 테스트 추가 |
| 18 | 불필요한 React re-render 최소화 | 부분 구현 | React Query, Zustand 최소 store 구조 | 렌더링 기준 테스트는 없음 |
| 19 | Runtime Contract 기반 compact transport 구조 유지 | 부분 구현 | `app/services/compact_state_builder.py` | 실제 API/log 저장 경로에서 일관 적용 필요 |
| 20 | Recommendation/Ranking/Prompt 정책 분리 | 구현됨 | `docs/policies/*`, `app/policies/*`, `app/prompts/*` | 문서와 코드 상수 동기화 테스트 |

## 2. 설계서 테스트 기준 12개 추적

| 번호 | 테스트 기준 | 상태 | 현재 테스트 근거 | 보완 필요 사항 |
|---:|---|---|---|---|
| 1 | personalized recommendation 반환 및 중복 없음 | 부분 구현 | `tests/test_negative_preference_filtering.py`, `tests/test_discovery_recommendation_flow.py` | main recommendation API 수준 중복 테스트 추가 |
| 2 | discovery recommendation 반환 및 discovery ratio 정책 만족 | 부분 구현 | `tests/test_discovery_recommendation_flow.py` | ratio 기준이 코드/문서에 명확하지 않아 결정 필요 |
| 3 | recommendation reason 질문에 evidence 기반 설명 반환 | 부분 구현 | `tests/test_curator_ui_contract.py` | chatbot response provenance 테스트 추가 |
| 4 | RAG_STATE에 없는 content_id 차단 | 부분 구현 | `app/validators/provenance_validator.py` | 실패 시 fallback까지 검증하는 테스트 추가 |
| 5 | Runtime Contract 누락 시 LLM 실행 차단 | 부분 구현 | `app/validators/contract_validator.py` | `KAG_INPUT_JSON`, `RAG_INPUT_JSON` boundary 테스트 추가 |
| 6 | 동일 request_id 다중 요청 차단 | 부분 구현 | `app/services/request_lifecycle_cache.py` | API route 단위 409 테스트 추가 |
| 7 | 동일 API 반복 호출에서 React Query cache 사용 | 부분 구현 | `frontend/src/pages/MainRecommendationPage.tsx`, `frontend/src/pages/ChatbotPage.tsx` | 프론트 테스트 환경 부재 |
| 8 | InputPlanner가 enum 범위 외 값을 제거하고 content_id/title/artist를 만들지 않음 | 구현됨 | `app/agents/input_planner_agent.py`, `tests/test_artist_recommendation_flow.py` | LLM parser 실패 케이스 추가 |
| 9 | invalid JSON LLM 출력 시 fallback 실행 | 미구현 | 명시 테스트 없음 | LLM client stub 기반 테스트 필요 |
| 10 | LLM이 KAG_STATE/RAG_STATE를 만들려 할 때 폐기 | 부분 구현 | `ResponseGenerator` sanitize, provenance validator | malicious LLM output 테스트 필요 |
| 11 | RecommendationAgent selected_recommendations contract 준수 | 구현됨 | `tests/test_negative_preference_filtering.py`, `app/agents/recommendation_agent.py` | source.kag 값 정책 결정 필요 |
| 12 | ResponseGenerator가 selected_recommendations 기반 RESPONSE_STATE 생성 | 부분 구현 | `app/agents/response_generator.py` | title/artist 변조 LLM 응답 테스트 추가 |

## 3. 완료 기준 추적

### 3.1 기능 완료

| 완료 기준 | 상태 | 근거 | 보완 필요 사항 |
|---|---|---|---|
| Main Recommendation Page 동작 | 구현됨 | `frontend/src/pages/MainRecommendationPage.tsx`, `app/api/recommendation_routes.py` | main flow 검증 강화 |
| Chatbot Page 동작 | 구현됨 | `frontend/src/pages/ChatbotPage.tsx`, `app/api/chatbot_routes.py` | streaming fallback 테스트 |
| Redis Session Context 동작 | 구현됨 | `app/cache/session_history_cache.py` | Redis 장애 테스트 |
| Neo4j KAG 동작 | 부분 구현 | `app/kag/adapters/real_kag_adapter.py` | 실제 Docker/Neo4j 통합 검증 |
| Elasticsearch RAG 동작 | 부분 구현 | `app/rag/adapters/rag_real_adapter.py` | 실제 ES 통합 검증 |
| Multi-Agent Flow 동작 | 부분 구현 | `app/agents/orchestrator_agent.py` | 설계서 순서와 실제 순서 불일치 결정 필요 |
| Validator 동작 | 부분 구현 | `app/validators/*` | boundary별 검증 누락 보완 |
| CompactStateBuilder 동작 | 부분 구현 | `app/services/compact_state_builder.py` | API/log 저장 경로 일관 적용 |
| Request Lifecycle Cache 동작 | 부분 구현 | `app/services/request_lifecycle_cache.py` | route 테스트 추가 |
| RecommendationAgent 통합 수행 | 구현됨 | `app/agents/recommendation_agent.py` | section fallback 정책 문서화 |
| Curation Agent 없이 Chatbot Flow 동작 | 구현됨 | `app/agents/orchestrator_agent.py` | 없음 |

### 3.2 저장 완료

| 완료 기준 | 상태 | 근거 | 보완 필요 사항 |
|---|---|---|---|
| interaction_logs 저장 | 부분 구현 | `app/services/logging_service.py`, `app/services/chatbot_service.py`, `app/services/main_recommendation_service.py`, `db/schema.sql` | 실제 DB 통합 검증 필요 |
| chat_sessions 저장 | 구현됨 | `app/services/session_flush_service.py` | flush 실패 테스트 |
| chat_session_turns 저장 | 부분 구현 | `app/services/session_flush_service.py` | `response_state_json` 저장 누락 여부 확인 필요 |
| detail_view_logs 저장 | 구현됨 | `app/api/music_detail_routes.py` | 실패 시 영향 격리 테스트 |
| Session Flush 동작 | 구현됨 | `app/api/session_routes.py`, `app/services/session_flush_service.py` | 빈 세션/중복 flush 테스트 |

### 3.3 검증 완료

| 완료 기준 | 상태 | 근거 | 보완 필요 사항 |
|---|---|---|---|
| Response Validation 동작 | 구현됨 | `app/validators/response_validator.py` | schema 엄격성 강화 검토 |
| Provenance Validation 동작 | 구현됨 | `app/validators/provenance_validator.py` | fallback 연결 테스트 |
| fallback 동작 | 부분 구현 | `app/common/default_state.py`, `OrchestratorAgent._fallback` | logging/fallback 저장 경로 보완 |
| RAG 없는 추천 차단 | 부분 구현 | `RecommendationAgent`, `ProvenanceValidator` | main/chatbot 통합 테스트 |
| duplicated recommendation 차단 | 구현됨 | `RecommendationAgent`, `ContractValidator` | API view model 중복 테스트 |
| hallucination 차단 | 부분 구현 | `ResponseGenerator` sanitize, validators | LLM 변조 응답 테스트 |

### 3.4 UI 완료

| 완료 기준 | 상태 | 근거 | 보완 필요 사항 |
|---|---|---|---|
| React Recommendation UI 동작 | 구현됨 | `frontend/src/pages/MainRecommendationPage.tsx` | UI 테스트 부재 |
| Chatbot UI 동작 | 구현됨 | `frontend/src/pages/ChatbotPage.tsx` | stream error 테스트 부재 |
| Recommendation Card UI 동작 | 구현됨 | `frontend/src/components/recommendation/RecommendationCard.tsx` | 없음 |
| Developer Debug Panel 분리 | 미구현 | 관련 컴포넌트 없음 | 설계 유지 여부 결정 필요 |
| MusicDetailModal 동작 | 구현됨 | `frontend/src/components/recommendation/MusicDetailModal.tsx` | URL 직접 진입 정책 결정 |
| URL 기반 Modal 동작 | 부분 구현 | `MainRecommendationPage`의 `detail` query 처리 | 라우터 없는 직접 진입 보완 필요 |
| unnecessary re-render 없음 | 부분 구현 | React Query/Zustand 사용 | 계측/테스트 없음 |

## 4. 우선 보완 순서

사용자 승인 순서에 따라 다음 순서로 진행한다.

1. 문서-구현 추적표 작성
2. Orchestrator 흐름 재정의
3. Contract 검증 강화
4. `interaction_logs` 저장 경로 완성
5. 프론트 라우팅 구조 정리
6. 테스트 기준 보강

## 5. 구현 전 결정이 필요한 항목

다음 항목은 설계서와 현재 구현의 차이가 있어, 코드 변경 전에 결정해야 한다.

1. Orchestrator 실행 순서는 설계서 기준에 맞춰 `IntentAgent`를 KAG 전에 배치하는 것으로 반영했다.
2. Main Recommendation Flow에서 `RecommendationAgent`를 반드시 통과시킬지, 현재처럼 RAG evidence 기반 view model 구성을 의도적 변경으로 둘지 결정한다.
3. `interaction_logs` 저장 실패는 현재 서비스 패턴에 맞춰 사용자 응답과 분리한다.
4. Frontend는 외부 router 의존성 추가 없이 URL path 기반 SPA 라우팅을 적용한다.

## 6. 현재 검증 상태

문서 작성 직전 확인한 검증 결과는 다음과 같다.

- `C:\Python314\python.exe -m pytest -q`: 20 passed, pytest cache 쓰기 권한 경고 1건
- `npm run build` in `frontend`: 성공
