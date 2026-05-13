# RIMAS_v4_Integrated_Design.md
# React + PostgreSQL + Redis + Neo4j + Elasticsearch 기반 Multi-Agent 음악 큐레이터 시스템 최종 통합 설계 v4

# v4 변경 목적

v4는 기존 v3 설계를 유지하면서 다음을 보강한다.

1. KAG 담당자 / RAG 담당자 병렬 개발 가능 구조 추가
2. Runtime Contract 세분화
3. KAG_INPUT_JSON / RAG_INPUT_JSON 계약 추가
4. Multi-Agent LLM Flow 세부 구조 추가
5. Music Detail Flow 추가
6. Music Detail API 추가
7. Validator 흐름 세부화
8. UI 세부 구조 보강
9. Mock → Real Adapter 교체 전략 강화
10. Service Layer 중심 연결 구조 강화
11. Internal Full State / Transport Compact State 분리
12. Request Lifecycle Cache 추가
13. RecommendationPolicy / RankingPolicy / PromptPolicy 구조 추가
14. React 렌더링 및 상태 관리 정책 강화
15. PostgreSQL / Elasticsearch / Neo4j / Redis 역할 분리 강화

기존 v3 구조는 최대한 유지한다.

---

# 0. 현재 고정된 전제

RIMAS v3는 Spotify 기반 음악 메타데이터를 활용하여 사용자에게 개인화된 음악 큐레이션 경험을 제공하는 Multi-Agent 기반 음악 추천 시스템이다.

본 시스템의 고정된 구조는 이거다

User
→ UI
→ API Layer
→ Request Lifecycle Cache
→ Service Layer
→ Orchestrator Agent
→ Input Planner Agent
→ Intent Agent
→ KAG Dispatch Agent
→ Neo4j KAG
→ KAG_STATE
→ RAG Dispatch Agent
→ Elasticsearch RAG
→ RAG_STATE
→ Recommendation Agent
→ Response Generator Agent
→ LLM Client
→ Cloud LLM Provider
→ Response Parser
→ Response Validator
→ Provenance Validator
→ CompactStateBuilder
→ PostgreSQL Log
→ UI 출력

최신 구현 기준상 KAG는 Neo4j 그래프 탐색으로 추천 방향, 큐레이션 경로, 추천 후보 content_id를 결정하고, RAG는 해당 후보에 대한 설명 근거를 제공한다. LLM은 추천 후보나 content_id를 새로 만들지 않고 자연어 응답만 생성해야 한다.

---

# 1. 시스템 목표

RIMAS v4는 Spotify 기반 음악 메타데이터를 활용하여 사용자에게 개인화된 음악 큐레이션 경험을 제공하는 Multi-Agent 기반 음악 추천 시스템이다.

본 시스템은 다음을 목표로 한다.

1. 사용자 질문 기반 음악 추천 제공
2. 음악 메타데이터 기반 추천 이유 생성
3. 새로운 취향 탐색 지원
4. 자연스러운 DJ 큐레이터 스타일 응답 생성
5. 추천 근거 기반 안전한 응답 제공
6. 세션 기반 대화 맥락 유지
7. Validator 기반 Hallucination 차단
8. Runtime Contract 기반 안전한 Agent 구조 유지
9. React 기반 실제 서비스형 UI 제공
10. Neo4j 기반 관계형 추천 제공
11. Elasticsearch 기반 설명 근거 검색 제공
12. Redis 기반 세션 컨텍스트 유지
13. PostgreSQL 기반 영속 로그 저장
14. Music Detail 기반 상세 추천 정보 제공
15. KAG/RAG 병렬 개발 가능 구조 유지
16. Mock Adapter → Real Adapter 확장 가능 구조 유지
17. 중복 API 호출 및 중복 Retrieval 방지
18. 불필요한 React Re-render 최소화
19. Runtime Contract 기반 Compact Transport 구조 유지
20. Recommendation / Ranking / Prompt 정책 분리

---

# 2. 핵심 설계 원칙

## 2.1 Runtime Contract 기반 구조

모든 실행 흐름은 JSON Contract 기반으로 동작한다.

필수 Runtime Contract:

- SESSION_CONTEXT
- KAG_INPUT_JSON
- KAG_STATE
- RAG_INPUT_JSON
- RAG_STATE
- RESPONSE_STATE
- INTERACTION_LOG
- MUSIC_DETAIL_VIEW_MODEL

---

## 2.2 Runtime State 분리 원칙

Runtime State는 다음 두 종류로 분리한다.

### Internal Full State

역할:

- 내부 Agent 흐름 유지
- Retrieval Trace 유지
- Validator 검증 유지
- Debugging 유지
- Provenance 유지

특징:

- 내부 전용
- 상세 trace 포함
- 전체 metadata 포함 가능
- Redis 및 Backend 내부 처리용

### Transport Compact State

역할:

- Frontend 전송
- API 응답
- 최소 ViewModel 전달

특징:

- 최소 필드만 유지
- 내부 전략 제거
- retrieval trace 제거
- raw validator trace 제거

---

## 2.3 CompactStateBuilder 구조

상태 변환은 명시적 변환 계층을 통해 수행한다.

구조:

Full State
→ CompactStateBuilder
→ Compact State

CompactStateBuilder 역할:

- Frontend 전송용 최소 데이터 생성
- 내부 trace 제거
- strategy 내부값 제거
- Validator 내부 상태 제거
- response payload 축소

금지:

- 추천 생성
- 추천 수정
- content_id 변경

---

## 2.4 UI 원칙

UI는 절대 추천을 생성하지 않는다.

허용:

- API 호출
- 추천 카드 렌더링
- 세션 상태 표시
- 추천 이유 표시
- 큐레이터 응답 표시
- Developer Debug Panel 표시
- Modal 상태 표시
- URL Query State 처리

금지:

- 추천 생성
- SQL 실행
- Neo4j 직접 호출
- Elasticsearch 직접 호출
- LLM 직접 호출
- 내부 전략 노출
- raw JSON 고객 노출
- Validator 우회

---

## 2.5 React 상태 관리 원칙

React는 최소 상태 기반 구조를 유지한다.

원칙:

- Zustand Store 최소화
- selector 기반 subscribe 강제
- broad subscribe 금지
- derived state duplication 금지
- useEffect 중복 최소화
- API 중복 호출 금지
- React Query / SWR cache 우선 사용
- unnecessary re-render 금지

금지:

- 동일 데이터 다중 store 저장
- 동일 API 다중 호출
- derived state 저장
- render 중 API 호출
- 무한 effect loop

---

## 2.6 LLM 원칙

LLM은 추천 엔진이 아니다.

LLM은 다음 두 구간에서만 사용한다.

1. Input Planning
- user_input을 구조화한다.
- intent, mood, genre, situation 후보를 정규화한다.
- KAG_INPUT_JSON 생성을 보조한다.

2. Response Generation
- KAG/RAG 결과와 selected_recommendations를 기반으로 자연어 응답을 생성한다.

LLM 허용:

- 사용자 입력 의도 해석
- genre, mood, situation 후보 정규화
- KAG_INPUT_JSON 생성 보조
- 자연어 큐레이터 응답 생성
- 추천 이유 설명
- 음악 정보 설명
- 분위기 설명

LLM 금지:

- 추천 후보 생성
- content_id 생성
- title 생성
- artist 생성
- KAG_STATE 생성
- RAG_STATE 생성
- KAG 결과 수정
- RAG 결과 수정
- KAG 선택 과정 개입
- RAG 검색 결과 재선택
- recommendation_category 임의 변경
- Runtime Contract 수정
- 내부 strategy_code 노출
- retrieval_trace 노출
- validator_trace 노출
- RAG evidence에 없는 설명 생성

---

## 2.7 Validator 중심 구조

최종 신뢰 기준은 Prompt가 아니라 Validator다.

검증:

- Contract Validator
- Response Validator
- Provenance Validator

---

## 2.8 데이터 중심 구조

현재 버전에서는 ML을 제거한다.

추천 기준:

- Spotify Metadata
- Session Context
- Neo4j Relationship
- Elasticsearch Evidence

ML은 추후 Optional Extension으로 추가 가능하도록만 설계한다.

---


# 3. 전체 시스템 아키텍처

React UI
→ FastAPI API Layer
→ Request Lifecycle Cache
→ Service Layer
→ Orchestrator Agent
→ Input Planner Agent
→ INTENT_STATE 생성
→ KAG_INPUT_JSON 생성
→ Contract Validator
→ Intent Agent
→ confirmed_intent_state 생성
→ KAG Dispatch Agent
→ Neo4j KAG
→ KAG_STATE
→ Contract Validator
→ RAG Dispatch Agent
→ RAG_INPUT_JSON 생성
→ Elasticsearch RAG
→ RAG_STATE
→ Contract Validator
→ Recommendation Agent
→ selected_recommendations 생성
→ Response Generator Agent
→ LLM Client
→ Cloud LLM Provider
→ Response Parser
→ Response Validator
→ Provenance Validator
→ CompactStateBuilder
→ Redis Save
→ PostgreSQL Flush
→ React Response

---

# 4. 전체 실행 흐름

## 4.1 Main Recommendation Flow

1. 사용자가 Main Recommendation Page 진입
2. Frontend가 recommendation API 호출
3. Request Lifecycle Cache 중복 요청 검사
4. Backend API Layer 요청 수신
5. Redis Session Context 조회
6. MainRecommendationService 실행
7. Orchestrator Agent 실행
8. Input Planner Agent 실행
9. INTENT_STATE 생성
10. KAG_INPUT_JSON 생성
11. Contract Validator 검증
12. Intent Agent 실행
13. confirmed_intent_state 생성
14. KAG Dispatch Agent 실행
15. MockKagAdapter 또는 RealKagAdapter 선택
16. Neo4j KAG 탐색
17. KAG_STATE 반환
18. Contract Validator 검증
19. RAG Dispatch Agent 실행
20. KAG_STATE 기반 RAG_INPUT_JSON 생성
21. MockRagAdapter 또는 RealRagAdapter 선택
22. Elasticsearch Retrieval 실행
23. RAG_STATE 반환
24. Contract Validator 검증
25. Recommendation Agent 실행
26. selected_recommendations 생성
27. Recommendation ViewModel 생성
28. CompactStateBuilder 실행
29. PostgreSQL interaction_logs 저장
30. Frontend Response 반환
31. React Recommendation Section 렌더링

Main Recommendation Flow는 LLM Response Generation 없이도 동작 가능해야 한다.
단, Input Planner Agent는 user_input이 없더라도 session_context 기반으로 KAG_INPUT_JSON을 생성할 수 있다.
Intent Agent는 Main Recommendation Flow에서도 INTENT_STATE를 검증하고 confirmed_intent_state를 생성한다.

---

## 4.2 Chatbot Flow

1. 사용자가 ChatbotPage 입력
2. Frontend가 chatbot API 호출
3. Request Lifecycle Cache 중복 요청 검사
4. API Layer 요청 수신
5. Redis Session Context 조회
6. ChatbotService 실행
7. Orchestrator Agent 실행
8. Input Planner Agent 실행
9. INTENT_STATE 생성
10. KAG_INPUT_JSON 생성
11. Contract Validator 검증
12. Intent Agent 실행
13. KAG Dispatch Agent 실행
14. MockKagAdapter 또는 RealKagAdapter 선택
15. Neo4j KAG 탐색
16. KAG_STATE 반환
17. Contract Validator 검증
18. RAG Dispatch Agent 실행
19. KAG_STATE 기반 RAG_INPUT_JSON 생성
20. MockRagAdapter 또는 RealRagAdapter 선택
21. Elasticsearch Retrieval 실행
22. RAG_STATE 반환
23. Contract Validator 검증
24. Recommendation Agent 실행
25. selected_recommendations 생성
26. Response Generator Agent 실행
27. LLM Client 실행
28. Cloud LLM Provider 호출
29. Response Parser 실행
30. Response Validator 검증
31. Provenance Validator 검증
32. CompactStateBuilder 실행
33. Redis Session History 저장
34. PostgreSQL interaction_logs 저장
35. React UI 반환

---

## 4.3 Music Detail Flow

1. 사용자가 RecommendationCard 클릭
2. URL Query 기반 detail 상태 생성
3. 예시:

/music?detail=nl_track_001

4. content_id 확보
5. Frontend가 Music Detail API 호출
6. MusicDetailService 실행
7. 최근 RAG_STATE 조회
8. content_id 기반 evidence 조회
9. 없으면 music_catalog 조회
10. MusicDetailViewModel 생성
11. CompactStateBuilder 실행
12. PostgreSQL detail_view_logs 저장
13. MusicDetailModal 출력
14. 필요 시 Full Page 확장 가능

---

## 4.4 Session Flush Flow

1. Session 종료 감지
2. Redis Session History 조회
3. chat_session_turns 저장
4. chat_sessions 저장
5. interaction_logs 저장
6. Redis Session 제거

---

# 5. Multi-Agent 구조

## 5.1 Agent 목록

1. Orchestrator Agent
2. Input Planner Agent
3. Intent Agent
4. KAG Dispatch Agent
5. RAG Dispatch Agent
6. Recommendation Agent
7. Response Generator Agent
8. Validator Controller

---

## 5.2 Orchestrator Agent

### 역할

- 전체 흐름 제어
- Agent 호출 순서 관리
- Session Context 조회
- Validator 흐름 제어
- Fallback 흐름 제어
- Runtime Contract 검증 흐름 제어

### 입력

- user_input
- session_id
- user_id

### 출력

- RESPONSE_STATE

### 금지

- 추천 곡 직접 생성
- RAG 없는 추천 생성
- KAG_STATE 수정
- RAG_STATE 수정
- UI 렌더링 수행

---

## 5.3 Input Planner Agent

### 역할

Input Planner Agent는 user_input을
KAG가 사용할 수 있는 구조화 입력으로 변환한다.

역할:

- user_input 분석
- intent 후보 추출
- mood 후보 추출
- genre 후보 추출
- situation 후보 추출
- KAG_INPUT_JSON 초안 생성
- session_context 반영
- enum 기반 정규화

### 입력

- user_input
- session_context
- user_id
- session_id
- request_id

### 출력

- INTENT_STATE
- KAG_INPUT_JSON

### 금지

- 추천 후보 생성
- content_id 생성
- title 생성
- artist 생성
- KAG_STATE 생성
- RAG_STATE 생성
- RESPONSE_STATE 생성
- KAG 결과 수정
- RAG 결과 수정
- graph traversal 직접 수행
- Elasticsearch retrieval 직접 수행

---

## 5.4 Intent Agent

### 역할

Intent Agent는 Input Planner Agent가 생성한 INTENT_STATE를 검증하고,
서비스 흐름에서 사용할 intent_type을 확정한다.

역할:

- INTENT_STATE 검증
- intent_type 허용값 검증
- confidence 기준 검증
- requires_kag / requires_rag 판단값 검증
- general_chat fallback 여부 판단
- Orchestrator에 다음 실행 흐름 반환

### 입력

- user_input
- session_context
- INTENT_STATE

### 출력

- confirmed_intent_state

### intent_type 허용값

- personalized_recommendation
- new_release_recommendation
- discovery_recommendation
- music_information
- recommendation_reason
- general_chat

### 금지

- 추천 생성
- 설명 생성
- KAG_INPUT_JSON 수정
- KAG_STATE 생성
- RAG_STATE 생성
- Runtime Contract 수정

---

## 5.5 KAG Dispatch Agent

### 역할

- KAG_INPUT_JSON 검증
- MockKagAdapter / RealKagAdapter 선택
- Neo4j KAG 실행
- timeout 처리
- retry 처리
- fallback 처리
- KAG_STATE 반환
- Contract Validator 연결

### 입력

- confirmed_intent_state
- KAG_INPUT_JSON
- session_context
- request_id

### 출력

- KAG_STATE

### 금지

- 최종 자연어 응답 생성
- 추천 이유 생성
- UI 렌더링
- RAG_STATE 수정
- RESPONSE_STATE 생성

### 내부 흐름

KAG Dispatch Agent
→ KAG_INPUT_JSON 검증
→ Adapter Router 실행
→ MockKagAdapter 또는 RealKagAdapter 선택
→ Neo4j Query 실행
→ KAG_STATE 생성
→ Contract Validator 연결
→ 반환

---

## 5.6 RAG Dispatch Agent

### 역할

- RAG_INPUT_JSON 생성
- MockRagAdapter / RealRagAdapter 선택
- Elasticsearch Retrieval 실행
- Retrieval Strategy 선택
- Hybrid Retrieval 분기
- fallback retrieval 처리
- retrieval_trace 생성
- RAG_STATE 반환
- Contract Validator 연결

### 입력

- confirmed_intent_state
- KAG_STATE
- session_context
- request_id

### 출력

- RAG_STATE

### 금지

- 추천 전략 결정
- 존재하지 않는 곡 생성
- 최종 응답 생성
- KAG_STATE 수정
- RESPONSE_STATE 생성

### 내부 흐름

RAG Dispatch Agent
→ RAG_INPUT_JSON 생성
→ Adapter Router 실행
→ MockRagAdapter 또는 RealRagAdapter 선택
→ Elasticsearch Retrieval 실행
→ retrieval_trace 생성
→ RAG_STATE 생성
→ Contract Validator 연결
→ 반환

---

## 5.7 Recommendation Agent

### 역할

Recommendation Agent는 기존 Curation Agent 역할을 포함한다.

역할:

- RAG 후보 중 최종 표시 대상 선택
- personalized / discovery / new_release 비율 조정
- section 기반 recommendation 분류
- section별 recommendation view model 구성
- diversity score 반영
- duplicate recommendation 제거
- rerank 수행
- selected_recommendations 생성

### 출력

- selected_recommendations

### selected_recommendations Contract

```json
{
  "selected_recommendations": [
    {
      "content_id": "nl_track_001",
      "title": "Midnight Loop",
      "artist": "Nova Lane",
      "section": "personalized",
      "recommendation_category": "personalized_candidate",
      "display_reason": "차분한 밤 분위기와 연결되는 곡",
      "rank": 1,
      "score": 0.87,
      "source": {
        "kag": true,
        "rag": true
      }
    }
  ]
}
```
필드 설명:

- content_id: RAG_STATE와 KAG_STATE에 존재하는 곡 ID
- title: RAG evidence 기준 title
- artist: RAG evidence 기준 artist
- section: UI 노출 섹션
- recommendation_category: 추천 분류
- display_reason: 사용자에게 보여줄 추천 이유
- rank: 최종 표시 순서
- score: RankingPolicy 기준 점수
- source: KAG/RAG 기반 여부

금지:

- RAG_STATE에 없는 content_id 포함 금지
- title 임의 수정 금지
- artist 임의 수정 금지
- display_reason 임의 생성 금지
- section 임의 변경 금지
- retrieval_trace 수정 금지
- KAG routing 정보 수정 금지

### 사용 정책

RecommendationPolicy.md:

- 추천 전략
- discovery 허용 범위
- personalized 비율
- section 정책
- section별 노출 개수

RankingPolicy.md:

- score 계산
- rerank 기준
- duplicate 제거
- diversity score
- 최종 표시 순서

### 금지

- 새로운 content_id 생성
- title 수정
- artist 수정
- recommendation_category 수정
- RAG_STATE에 없는 곡 추가
- KAG_STATE의 target_section 임의 변경

---

## 5.8 Response Generator Agent

### 역할

Response Generator Agent는 Recommendation Agent가 확정한 selected_recommendations와
RAG_STATE의 evidence를 기반으로 사용자에게 보여줄 자연어 큐레이터 응답을 생성한다.

역할:

- DJ 큐레이터 스타일 응답 생성
- 추천 이유를 사용자 친화적 문장으로 변환
- 음악 정보 설명
- 분위기 설명
- RESPONSE_STATE 생성
- LLM Client 호출
- Response Parser 연결
- Response Validator 연결
- Provenance Validator 연결

### 입력

- user_input
- session_context
- compact_kag_state
- compact_rag_state
- selected_recommendations
- PromptPolicy

### 출력

- RESPONSE_STATE

### 내부 흐름

Response Generator Agent
→ selected_recommendations 확인
→ RAG evidence 확인
→ PromptPolicy 로드
→ response_prompt 생성
→ LLM Client 호출
→ Cloud LLM Provider 응답 수신
→ Response Parser 실행
→ RESPONSE_STATE 생성
→ Response Validator 검증
→ Provenance Validator 검증
→ 반환

### RESPONSE_STATE 생성 기준

RESPONSE_STATE는 반드시 selected_recommendations에 포함된 content_id만 사용한다.

RESPONSE_STATE의 display_recommendations는 selected_recommendations를 기반으로 생성한다.

chatbot_response는 RAG_STATE의 evidence와 selected_recommendations의 display_reason 범위 안에서만 생성한다.

### 사용 정책

PromptPolicy.md:

- prompt template
- system prompt
- tone
- forbidden rule
- response length
- fallback message
- JSON output rule

### 금지

- 추천 후보 생성
- selected_recommendations 수정
- Recommendation Agent 결과 재선택
- content_id 생성
- title 수정
- artist 수정
- display_reason 임의 변경
- 존재하지 않는 곡 생성
- 존재하지 않는 아티스트 생성
- RAG evidence 밖 설명 생성
- KAG_STATE 수정
- RAG_STATE 수정
- 내부 전략 노출
- retrieval_trace 노출
- validator_trace 노출
- raw JSON 노출

---

# 6. React Frontend 구조

## 6.1 Frontend 역할

Frontend는 API 결과를 표시한다.

Frontend는 추천을 생성하지 않는다.

---

## 6.2 React 페이지

- MainRecommendationPage
- ChatbotPage
- MusicDetailPage
- Layout
- NotFoundPage

MusicDetailPage는 URL 기반 Modal 구조를 우선 적용한다.

예시:

/music?detail=nl_track_001

필요 시 Full Page 구조로 확장 가능하다.

---

## 6.3 React 컴포넌트

- TopTasteHeader
- CharacterDjBanner
- RecommendationSection
- RecommendationCard
- MusicDetailModal
- MusicMetadataSection
- RecommendationReasonSection
- RelatedTracksSection
- PersonalizedGuideSection
- ChatHeader
- ChatHistory
- ChatInput
- CuratorResponseArea
- RelatedRecommendationCards
- DeveloperDebugPanel

---

## 6.4 React Store

### userStore

역할:

- user_id 저장
- login state 저장
- session 정보 저장

### recommendationStore

역할:

- recommendation state 저장
- personalized section 저장
- discovery section 저장
- new release section 저장

### chatStore

역할:

- chat history 저장
- chatbot loading state 저장
- response state 저장

### musicDetailStore

역할:

- 현재 선택된 content_id 저장
- Music Detail 상태 저장
- Detail Modal 상태 저장

---

## 6.5 React Query 정책

원칙:

- React Query 또는 SWR cache 우선 사용
- 동일 API 중복 호출 금지
- stale request 최소화
- inflight request dedupe 유지
- query invalidation 최소화

금지:

- render 기반 API 호출
- effect loop 기반 refetch
- 동일 endpoint 다중 fetch

---

## 6.6 React 금지 규칙

금지:

- 추천 생성
- SQL 실행
- Neo4j 직접 호출
- Elasticsearch 직접 호출
- LLM 직접 호출
- Runtime Contract 수정
- raw JSON 기본 노출
- 내부 전략 노출
- broad Zustand subscribe
- derived state duplication
- 무한 render loop
- Provider 직접 호출
- Prompt 생성 로직 포함
- Runtime Contract 우회

---

# 7. FastAPI Backend 구조

## 7.1 Backend 역할

- API 제공
- Multi-Agent 흐름 제어
- Validator 제어
- Session Cache 제어
- DB 저장
- Request Lifecycle Cache 관리

---

## 7.2 Request Lifecycle Cache

### 역할

- 중복 API 요청 차단
- 중복 Validator 실행 방지
- 중복 Retrieval 방지
- inflight request dedupe

### 내부 흐름

Request Start
→ request_id 등록
→ inflight cache 확인
→ 중복 차단
→ 처리 완료
→ expire 처리

### 방지 대상

- Neo4j repeated query
- Elasticsearch repeated retrieval
- duplicated validator run
- duplicate API call

---

## 7.3 API Layer

### recommendation_routes.py

역할:

- Main Recommendation API 제공

### chatbot_routes.py

역할:

- Chatbot API 제공

### music_detail_routes.py

역할:

- Music Detail API 제공

### session_routes.py

역할:

- Session History API 제공
- Session Flush API 제공

---

## 7.4 Service Layer

### main_recommendation_service.py

역할:

- Main Recommendation Flow 실행

### chatbot_service.py

역할:

- Chatbot Flow 실행

### llm_flow_service.py

역할:

- Multi-Agent 흐름 실행
- Input Planner Agent 실행
- Intent Agent 실행
- KAG Dispatch Agent 실행
- RAG Dispatch Agent 실행
- Recommendation Agent 실행
- Response Generator Agent 실행
- LLM Client 연결
- Response Parser 연결
- Validator 실행

### compact_state_builder.py

역할:

- Full State → Compact State 변환

### request_lifecycle_cache.py

역할:

- inflight request 관리
- duplicate request 차단

### session_cache_service.py

역할:

- Redis Session Context 관리

### session_flush_service.py

역할:

- Redis → PostgreSQL flush 처리

---

# 8. Redis Session Context 구조

## 8.1 목적

Redis는 세션 기반 대화 히스토리를 저장한다.

---

## 8.2 Redis Key

rimas:session:{session_id}:history

---

## 8.3 Session 저장 데이터

- compact_response_state
- compact_rag_state
- compact_kag_state
- selected_recommendations
- created_at

Internal Full State는 Backend 내부에서만 유지한다.

---

## 8.4 Session Context 역할

Session Context는 다음을 유지한다.

- 최근 선호 장르
- 최근 선호 아티스트
- 최근 대화 흐름
- 최근 추천 흐름
- 최근 분위기

---

## 8.5 TTL 정책

기본:

- 30분 ~ 2시간

현재 기본:

- 2시간

---

## 8.6 Flush 조건

Redis → PostgreSQL 저장 조건:

- 세션 종료
- TTL 만료 직전
- 일정 턴 수 초과
- 사용자 이탈
- 수동 flush API 호출

---

# 9. PostgreSQL 구조

## 9.1 목적

PostgreSQL은 canonical metadata 및 영속 저장을 담당한다.

---

## 9.2 저장소 역할 분리

| 저장소 | 역할 |
| --- | --- |
| PostgreSQL | canonical metadata + logs |
| Elasticsearch | retrieval evidence |
| Neo4j | graph traversal |
| Redis | session cache |

---

## 9.3 주요 테이블

- users
- music_catalog
- interaction_logs
- chat_sessions
- chat_session_turns
- detail_view_logs

현재 v4에서는 PostgreSQL을 minimal canonical storage 중심으로 유지한다.

---

## 9.4 users

역할:

- 사용자 정보 저장

---

## 9.5 music_catalog

역할:

- 최소 canonical 음악 메타데이터 저장

포함:

- track_id
- title
- artist
- genre
- mood
- release_type

---

## 9.6 interaction_logs

역할:

- 시스템 실행 로그 저장

저장:

- compact_kag_state_json
- compact_rag_state_json
- compact_response_state_json
- validation_status
- latency_ms
- error_type
- request_id

---

## 9.7 chat_sessions

역할:

- Session 메타데이터 저장

---

## 9.8 chat_session_turns

역할:

- 사용자 대화 히스토리 저장

---

## 9.9 detail_view_logs

역할:

- Music Detail 접근 로그 저장

---

# 10. Neo4j KAG 구조

## 10.1 목적

Neo4j는 음악 관계 기반 추천 방향 탐색과 추천 후보 content_id 생성을 담당한다.

현재 런타임 기준은 `neo4j/` 폴더에 구현된 MusicCatalog 중심 그래프 구조다. 설계서 초기안의 `Track` 중심 명칭은 앱 런타임에서는 `MusicCatalog`로 해석한다.

KAG/RAG/API 공통 `content_id`는 `MusicCatalog.track_id`를 사용한다.

---

## 10.2 Node 구조

- MusicCatalog
- Genre
- SubGenre 또는 PlaylistSubGenre
- Artist
- Mood
- Tempo
- ReleaseYear
- DimWeather
- DimSeason
- DimEmotion
- DimTimeOfDay
- DimEnergyLevel
- DimCtxCommute
- DimCtxHome
- DimCtxFocus
- DimCtxExercise
- DimCtxSocial
- DimCtxEmotionSit
- DimCtxTravel
- DimCtxSpecial

User 기반 그래프 노드와 사용자 청취 관계는 확장 대상이며, 현재 Real KAG 1차 연결 범위에는 포함하지 않는다.

---

## 10.3 Relationship 구조

- MusicCatalog -[:HAS_GENRE]-> Genre
- MusicCatalog -[:HAS_SUBGENRE]-> SubGenre
- MusicCatalog -[:PERFORMED_BY]-> Artist
- MusicCatalog -[:HAS_MOOD]-> Mood
- MusicCatalog -[:HAS_TEMPO]-> Tempo
- MusicCatalog -[:RELEASED_IN]-> ReleaseYear
- MusicCatalog -[:HAS_DIM_WEATHER]-> DimWeather
- MusicCatalog -[:HAS_DIM_SEASON]-> DimSeason
- MusicCatalog -[:HAS_DIM_EMOTION]-> DimEmotion
- MusicCatalog -[:HAS_DIM_TIME_OF_DAY]-> DimTimeOfDay
- MusicCatalog -[:HAS_DIM_ENERGY_LEVEL]-> DimEnergyLevel
- MusicCatalog -[:HAS_DIM_CTX_*]-> DimCtx*

관계명은 실제 Neo4j 적재 결과와 앱 KAG 쿼리 상수가 반드시 일치해야 한다. `HAS_SUBGENRE`와 `HAS_PLAYLIST_SUBGENRE`처럼 동일 의미의 관계명이 중복될 경우, 실제 적재 기준으로 하나를 선택해 런타임 쿼리를 정렬한다.

초기 설계의 `LIKES_GENRE`, `LIKES_MOOD`, `LISTENED_TO`, `SIMILAR_TO`, `ADJACENT_TO`, `COMPATIBLE_WITH`, `FITS_SITUATION`, `HAS_EMOTION`은 사용자 이력 그래프 또는 확장 그래프 단계에서 다시 도입할 수 있다.

---

## 10.4 KAG 역할

KAG는:

- 추천 방향 결정
- 추천 후보 탐색
- 추천 후보 content_id 생성
- 취향 확장 경로 탐색
- recommendation_category 결정
- route 결정
- UI section 방향 결정

---

## 10.5 KAG 금지 규칙

금지:

- 최종 자연어 생성
- 추천 이유 생성
- LLM 호출
- 존재하지 않는 content_id 생성
- UI 렌더링
- RAG_STATE 수정
- RESPONSE_STATE 생성

---

# 11. Elasticsearch RAG 구조

## 11.1 목적

Elasticsearch RAG는 KAG가 확정한 후보 `content_id`에 대해 추천 이유, 음악 설명, 분위기 설명, 검색 근거를 보강한다.

RAG는 추천 후보를 새로 만들지 않는다. KAG가 제공한 `content_id` 범위 안에서만 evidence를 검색하고 `RAG_STATE`를 구성한다.

---

## 11.2 Index 구조

목표 인덱스:

- rimas_tracks
- rimas_lyrics
- rimas_artist_info
- rimas_genre_info
- rimas_mood_info
- rimas_recommendation_evidence

현재 `app/rag` 추가 구현 기준 개발/검증 인덱스:

- `spotify_songs`

`spotify_songs`는 `content`, `embedding`, `metadata` 필드를 가진 개발용 Elasticsearch 인덱스로 사용한다. 운영 인덱스 명명과 최종 매핑은 위 목표 인덱스 구조에 맞춰 별도 확정한다.

---

## 11.3 저장 메타데이터

MusicCatalog:

- track_id
- title
- artist
- genre
- mood
- tempo
- situation_tags
- emotion_tags
- release_date
- lyrics_summary

현재 `app/rag/services/retrieval.py`와 `app/rag/musicCatalogRepository/sql_repostiory.py` 기준 검색 대상 메타데이터 후보:

- metadata.song
- metadata.Artist(s)
- metadata.Genre
- metadata.emotion
- metadata.Album
- metadata.text

최종 운영 전에는 위 필드명을 `MusicCatalog`/PostgreSQL/Neo4j의 `track_id = content_id` 기준 필드명과 정렬해야 한다.

---

## 11.4 RAG 역할

RAG는:

- 추천 이유 제공
- 음악 설명 제공
- 곡 정보 제공
- 분위기 설명 제공
- recommendation evidence 제공
- retrieval_trace 제공
- KAG 후보 `content_id`와 evidence의 매칭 검증

---

## 11.5 현재 RAG 구현 계층

`app/rag`는 다음 계층으로 분리한다.

- `ragStateBuilder/`: `RagRequest`, `RagState`, `RagOutput` 계약과 경량 workflow 구성
- `contractValidator/`: RAG 내부 최소 계약 검증 계층
- `musicCatalogRepository/`: 음악 카탈로그/검색 저장소 접근 경계
- `adapters/`: Mock/Real RAG 교체 지점
- `services/`: retrieval, embedding, indexing, generation 실행 서비스
- `common/`: Elasticsearch vector, pgvector 등 검색 보조 유틸리티
- `data/`: 개발용 CSV/embedding JSON 데이터

최종 Real RAG Adapter 기준 파일은 `app/rag/adapters/rag_real_adapter.py`로 확정한다. `app/rag/adapters/real_rag_adapter.py`는 구현 이전에 만들어진 임시 파일이며, 연결 완료 후 폐기 후보로 분류한다.

`services/retrieval.py`, `services/indexing.py`, `services/embedding.py`는 Real RAG 연결을 위한 후보 구현/실험 코드로 취급하며, Dispatch Agent에 연결하기 전 계약 정리가 필요하다.

---

## 11.6 검색 전략

Real RAG 검색은 다음 순서를 기준으로 한다.

1. KAG가 전달한 후보 `content_id`와 사용자 질의를 기반으로 RAG 입력을 구성한다.
2. 메타데이터 필터로 검색 범위를 제한한다.
3. BM25/키워드 검색과 embedding 기반 vector 검색을 결합한다.
4. 검색 결과를 reranking한다.
5. `content_id`가 KAG 후보 범위를 벗어나지 않는지 검증한다.
6. `RAG_STATE.recommended_content_evidence`와 `retrieval_trace`를 생성한다.

현재 `services/retrieval.py`는 lexical, semantic, hybrid 검색 모드를 포함한다. embedding은 `app/rag/services/embedding.py`의 `qwen3-embedding:0.6b` Ollama 모델 후보를 사용한다.

---

## 11.7 RAG 내부 Validator 범위

RAG 내부 Validator는 최소 계약 검증만 담당한다.

검증 범위:

- `recommended_content_evidence[*].content_id`가 KAG 후보 `content_id` 범위 안에 있는지
- RAG 출력 필수 필드가 존재하는지
- `evidence_summary`가 비어 있지 않은지
- `retrieval_trace`가 존재하는지

금지:

- 최종 자연어 응답 검증
- UI 표시 문구 검증
- Recommendation Agent ranking 검증
- LLM hallucination 전체 판정

최종 응답/출처 검증은 공통 `app/validators` 계층에서 담당한다.

---

## 11.8 RAG 금지 규칙

금지:

- 추천 전략 결정
- 존재하지 않는 곡 생성
- KAG 후보에 없는 content_id 생성 또는 추가
- 최종 응답 생성
- KAG_STATE 수정
- LLM으로 RAG_STATE 전체를 임의 생성

---

## 11.9 RAG Dispatch Adapter 선택 조건

`app/agents/rag_dispatch_agent.py`는 환경변수 `RIMAS_RAG_MODE`로 Mock/Real RAG Adapter를 선택한다.

선택 기준:

- 기본값은 `mock`이다.
- `RIMAS_RAG_MODE=mock`이면 Mock RAG Adapter를 사용한다.
- `RIMAS_RAG_MODE=real`이면 `app/rag/adapters/rag_real_adapter.py` 기준 Real RAG Adapter를 사용한다.
- Real RAG 선택 시 Elasticsearch 연결 실패, 인덱스 없음, 필수 evidence 부족이 발생하면 조용히 Mock으로 전환하지 않는다.
- Real RAG 실패는 `fallback` 또는 `failed` 상태로 명시적으로 반환한다.

요청 payload가 Adapter 선택권을 직접 갖지 않는다. Adapter 선택은 런타임 설정 책임이며, 클라이언트 입력으로 `rag_mode`를 받지 않는다.

---

## 11.10 정해야 하는 부분

Real RAG 연결 전 확정이 필요한 항목:

- `musicCatalogRepository`의 오타 파일명(`*_repostiory.py`)은 Real RAG 연결 완료 후 import 영향 범위를 확인한 뒤 한 번에 정리한다.

---

# 12. Runtime Contract

## 12.0 INTENT_STATE

```json
{
  "status": "success",
  "intent_type": "personalized_recommendation",
  "confidence": 0.82,
  "normalized_query": "사용자 취향 기반 음악 추천",
  "detected_moods": ["calm", "night"],
  "detected_genres": ["indie"],
  "detected_situations": ["late_night"],
  "requires_kag": true,
  "requires_rag": true
}
```
---
## 12.1 SESSION_CONTEXT

```json
{
  "session_id": "session_001",
  "recent_genres": ["indie", "dream_pop"],
  "recent_artists": ["artist_a"],
  "recent_moods": ["night", "calm"],
  "conversation_summary": "사용자는 차분한 밤 분위기의 음악을 선호함"
}
```
---
## 12.2 KAG_INPUT_JSON
```json
{
  "request_id": "req_001",
  "user_id": "user_001",
  "session_id": "session_001",
  "intent_type": "personalized_recommendation",
  "query_context": {
    "normalized_query": "사용자 취향 기반 음악 추천",
    "mood_candidates": ["calm", "night"],
    "genre_candidates": ["indie"],
    "situation_candidates": ["late_night"]
  },
  "constraints": {
    "allow_discovery": true,
    "allow_new_release": true,
    "max_candidates": 10
  }
}
```
---

## 12.3 Internal Full KAG_STATE

```json
{
  "status": "success",
  "recommendation_goal": {
    "primary_goal": "new_taste_discovery"
  },
  "recommended_content_ids": [
    "nl_track_001",
    "nl_track_002"
  ],
  "candidate_tracks": [
    {
      "content_id": "nl_track_001",
      "track_id": "nl_track_001",
      "track_name": "Midnight Loop",
      "track_artist": "Nova Lane",
      "recommendation_score": 87
    }
  ],
  "curation_strategy": {
    "strategy_code": "SAFE_DISCOVERY_FROM_PERSONAL_TASTE"
  },
  "routing": {
    "target_page": "chatbot_page"
  },
  "selected_path": "personalized_to_safe_discovery"
}
```

---

## 12.4 Compact KAG_STATE

```json
{
  "status": "success",
  "recommendation_goal": {
    "primary_goal": "new_taste_discovery"
  },
  "recommended_content_ids": [
    "nl_track_001",
    "nl_track_002"
  ],
  "target_section": "discovery_section"
}
```

---

## 12.5 Internal Full RAG_STATE

```json
{
  "status": "success",
  "recommended_content_evidence": [
    {
      "content_id": "nl_track_001",
      "title": "Midnight Loop",
      "artist": "Nova Lane",
      "genre": ["indie"],
      "mood": ["night"],
      "evidence_summary": "차분한 밤 분위기와 연결되는 곡"
    }
  ],
  "retrieval_trace": {
    "retrieval_strategy": "hybrid_search"
  }
}
```

---

## 12.6 Compact RAG_STATE

```json
{
  "status": "success",
  "display_recommendations": [
    {
      "content_id": "nl_track_001",
      "title": "Midnight Loop",
      "artist": "Nova Lane",
      "display_reason": "차분한 밤 분위기와 연결되는 곡"
    }
  ]
}
```
---

## 12.7 RAG_INPUT_JSON

```json
{
  "request_id": "req_001",
  "user_id": "user_001",
  "session_id": "session_001",
  "intent_type": "personalized_recommendation",
  "kag_recommended_content_ids": [
    "nl_track_001",
    "nl_track_002"
  ],
  "target_section": "personalized_section",
  "query_text": "차분한 밤 분위기의 인디 음악 추천 이유",
  "evidence_need": [
    "track_description",
    "mood_reason",
    "recommendation_reason"
  ],
  "retrieval_constraints": {
    "max_evidence_per_track": 3,
    "require_content_id_match": true
  }
}
```

---

## 12.8 RESPONSE_STATE

```json
{
  "status": "success",
  "response_type": "curator_recommendation",
  "chatbot_response": "차분한 밤 분위기를 좋아한다면 Midnight Loop를 추천드릴게요.",
  "display_recommendations": [
    {
      "content_id": "nl_track_001",
      "title": "Midnight Loop",
      "artist": "Nova Lane",
      "label": "취향 기반 추천",
      "display_reason": "차분한 밤 분위기와 연결되는 곡"
    }
  ],
  "used_content_ids": [
    "nl_track_001"
  ]
}
```

---

# 13. API Contract

## 13.1 Main Recommendation API

### Endpoint

GET /api/recommendations/main

---

### Request

```json
{
  "user_id": "user_001",
  "session_id": "session_001"
}
```

---

### Response

```json
{
  "status": "success",
  "page_type": "main_recommendation_page",
  "view_model": {
    "personalized": [],
    "new_release": [],
    "discovery": []
  }
}
```

---

## 13.2 Chatbot Response API

### Endpoint

POST /api/chatbot/respond

---

### Request

```json
{
  "user_id": "user_001",
  "session_id": "session_001",
  "user_input": "내 취향에 맞는 노래 추천해줘"
}
```

---

### Response

```json
{
  "status": "success",
  "response_state": {
    "status": "success",
    "response_type": "curator_recommendation",
    "chatbot_response": "추천 응답",
    "display_recommendations": []
  }
}
```

---

## 13.3 Music Detail API

### Endpoint

GET /api/music/detail/{content_id}

---

## 13.4 Session Flush API

### Endpoint

POST /api/sessions/{session_id}/flush

---

## 13.5 Session History API

### Endpoint

GET /api/sessions/{session_id}/history

---

# 14. Validator 구조

## 14.1 Contract Validator

검증:

- SESSION_CONTEXT 구조
- KAG_STATE 구조
- RAG_STATE 구조
- RESPONSE_STATE 구조
- Compact State 구조
- required field 검증
- type 검증

실패 시:

- LLM 실행 금지
- fallback 전환

---

## 14.2 Response Validator

검증:

- RESPONSE_STATE 구조
- 필수 필드 존재 여부
- status 검증
- display_recommendations 구조 검증
- duplicated recommendation 검증
- invalid display field 검증

실패 시:

- fallback 전환

---

## 14.3 Provenance Validator

검증:

- content_id 존재 여부
- title 일치 여부
- artist 일치 여부
- RAG 기반 응답 여부
- 내부 전략 노출 여부
- hallucination 여부
- retrieval evidence 존재 여부

실패 시:

- fallback 전환
- success 저장 금지

---

# 15. Prompt 구조

## 15.1 Prompt 관리 원칙

Prompt는 Python Prompt Module 방식으로 관리한다.

PromptPolicy.md는 정책 문서로 유지하고,
실제 실행 Prompt는 backend/app/prompts/*.py에서 관리한다.

Prompt는 Runtime Contract와 Output Schema를 기준으로 생성한다.

금지:

- Prompt 내부 hardcoded recommendation
- Prompt 내부 content_id 생성
- Prompt 내부 title 생성
- Prompt 내부 artist 생성
- Runtime Contract 우회
- Validator 우회
- raw JSON 고객 노출
- 내부 strategy_code 노출
- retrieval_trace 노출
- validator_trace 노출

---

## 15.2 Prompt 파일 구조

### base_prompt.py

역할:

- 모든 Prompt의 공통 규칙 관리

공통 규칙:

- hallucination 금지
- JSON only
- strategy leak 금지
- Runtime Contract 수정 금지
- 없는 곡 생성 금지
- 없는 아티스트 생성 금지
- 내부 trace 노출 금지
- Provider 응답이 JSON이 아니면 실패 처리

---

### input_planner_prompt.py

역할:

- user_input을 INTENT_STATE, KAG_INPUT_JSON으로 변환

입력:

- user_input
- session_context
- allowed_intent_types
- allowed_genres
- allowed_moods
- allowed_situations
- allowed_target_sections

출력:

- INTENT_STATE
- KAG_INPUT_JSON

규칙:

- 추천 후보를 생성하지 않는다.
- content_id를 생성하지 않는다.
- title을 생성하지 않는다.
- artist를 생성하지 않는다.
- KAG_STATE를 생성하지 않는다.
- RAG_STATE를 생성하지 않는다.
- RESPONSE_STATE를 생성하지 않는다.
- 허용 enum 밖의 intent_type은 general_chat으로 처리한다.
- mood, genre, situation은 허용 목록 안에서만 선택한다.
- 모호한 값은 빈 배열로 둔다.
- 출력은 JSON만 허용한다.

---

### intent_prompt.py

역할:

- INTENT_STATE 검증 및 intent_type 확정 보조

주의:

- Intent Agent는 기본적으로 INTENT_STATE를 검증/확정한다.
- intent_prompt.py는 LLM 기반 보조가 필요할 때만 사용한다.
- MVP에서는 Input Planner의 INTENT_STATE와 enum 검증을 우선 사용한다.

금지:

- KAG_INPUT_JSON 수정
- KAG_STATE 생성
- RAG_STATE 생성
- 추천 후보 생성
- 설명 생성

---

### recommendation_prompt.py

역할:

- recommendation 설명 생성 보조

주의:

- Recommendation Agent가 추천 후보를 확정한 뒤에만 사용 가능하다.
- RAG evidence 범위 안에서만 설명을 생성한다.

금지:

- selected_recommendations 수정
- content_id 생성
- title 수정
- artist 수정
- RAG_STATE에 없는 곡 추가

---

### response_prompt.py

역할:

- curator response 생성
- RESPONSE_STATE 생성 보조

입력:

- user_input
- session_context
- compact_kag_state
- compact_rag_state
- selected_recommendations
- PromptPolicy

규칙:

- selected_recommendations에 포함된 content_id만 사용한다.
- title, artist, display_reason을 임의로 변경하지 않는다.
- RAG evidence 밖 설명을 생성하지 않는다.
- 내부 strategy_code를 노출하지 않는다.
- retrieval_trace를 노출하지 않는다.
- validator_trace를 노출하지 않는다.
- 출력은 JSON만 허용한다.
- JSON 외 문장은 출력하지 않는다.
- 응답은 2~4문장 이내로 제한한다.

---

### fallback_messages.py

역할:

- fallback response 관리
- LLM 실패 시 고정 응답 제공
- Parser 실패 시 고정 응답 제공
- Validator 실패 시 고정 응답 제공

---

## 15.3 Prompt Output Schema

### prompt_output_schema/

역할:

- Prompt output schema 관리
- JSON structure validation
- required field validation
- enum validation

포함:

- input_planner_output_schema.py
- intent_output_schema.py
- response_output_schema.py

---

### response_parsers/

역할:

- Prompt 결과 parsing
- invalid output handling
- fallback parser 처리

포함:

- input_planner_parser.py
- intent_parser.py
- response_parser.py

---

## 15.4 Provider 선택 정책

LLM Provider는 Cloud LLM Provider 즉시 연결을 기본 방안으로 확정한다.

기본 Provider 후보:

- OpenAIProvider
- GroqProvider

테스트 Provider:

- MockLLMProvider

운영 원칙:

- 실제 응답 품질 검증을 위해 Cloud LLM Provider를 우선 연결한다.
- MockLLMProvider는 테스트 전용으로 유지한다.
- Provider 선택은 provider_registry.py에서만 수행한다.
- Agent 내부에서 Provider를 직접 선택하지 않는다.
- Service Layer에서 Provider를 직접 선택하지 않는다.

---

## 15.5 Model Config 정책

model_config.py는 다음 값을 관리한다.

- provider
- model_name
- temperature
- max_tokens
- timeout_seconds
- retry_count
- json_mode
- fallback_provider

기본 설정 예시:

provider: openai
model_name: gpt 계열 모델
temperature: 0.2
max_tokens: 700
timeout_seconds: 15
retry_count: 1
json_mode: true
fallback_provider: mock

정책:

- temperature는 낮게 유지한다.
- json_mode는 true를 기본값으로 둔다.
- timeout 발생 시 fallback response를 반환한다.
- retry_count는 과도하게 늘리지 않는다.
- Provider 장애 시 fallback_provider를 사용한다.

---

## 15.6 Parser / Fallback 정책

Input Planner Parser 실패 시:

- LLM 결과를 폐기한다.
- RuleBasedInputPlanner fallback을 사용한다.
- KAG_INPUT_JSON은 fallback input 기준으로 생성한다.

Response Parser 실패 시:

- LLM 결과를 폐기한다.
- fallback response를 반환한다.
- success 저장을 금지한다.

Validator 실패 시:

- fallback response를 반환한다.
- success 저장을 금지한다.
- PostgreSQL에는 error_type과 validation_status를 기록한다.

---

# 16. Folder Structure

```txt
rimas/
  frontend/
    src/
      pages/
        MainRecommendationPage.tsx
        ChatbotPage.tsx
        MusicDetailPage.tsx

      components/
        RecommendationCard.tsx
        RecommendationSection.tsx
        ChatHistory.tsx
        ChatInput.tsx
        CuratorResponseArea.tsx
        CharacterDjBanner.tsx
        DeveloperDebugPanel.tsx
        MusicDetailModal.tsx

      stores/
        userStore.ts
        recommendationStore.ts
        chatStore.ts
        musicDetailStore.ts

      api/
        recommendationApi.ts
        chatbotApi.ts
        sessionApi.ts
        musicDetailApi.ts

      types/
        kagState.ts
        ragState.ts
        responseState.ts
        compactState.ts

      hooks/
        useRecommendationQuery.ts
        useChatbotQuery.ts
        useMusicDetailQuery.ts

      styles/
        theme.ts
        globals.css

  backend/
    app/
      llm/
        llm_client.py
        llm_provider.py
        openai_provider.py
        groq_provider.py
        mock_llm_provider.py
        model_config.py
        provider_registry.py
        llm_response_schema.py
        llm_error.py

      api/
        recommendation_routes.py
        chatbot_routes.py
        music_detail_routes.py
        session_routes.py

      agents/
        orchestrator_agent.py
        input_planner_agent.py
        intent_agent.py
        kag_dispatch_agent.py
        rag_dispatch_agent.py
        recommendation_agent.py
        response_generator.py
        validator_controller.py

      kag/
        connection.py
        constant.py
        querys.py
        adapters/
          real_kag_adapter.py

      rag/
        design.md
        output.md
        adapters/
          rag_adapter.py
          mock_rag_adapter.py
          real_rag_adapter.py
          rag_mock_adapter.py
          rag_real_adapter.py
        builders/
          rag_state_builder.py
        ragStateBuilder/
          schema.py
          nodes.py
          edges.py
          builder.py
        contractValidator/
          base_validator.py
          format_validator.py
          logic_validator.py
          hallucination_validator.py
        musicCatalogRepository/
          base_repostiory.py
          sql_repostiory.py
          loader.py
          loader2.py
          loader_lyrics.py
        services/
          retrieval.py
          embedding.py
          indexing.py
          rag_generation.py
        common/
          elasticsearch_vector.py
          custom_pgvector.py
        data/
          spotify_songs.csv
          embedded_data_part111.json

      adapters/
        kag_adapter.py
        mock_kag_adapter.py
        real_kag_adapter.py
        rag_adapter.py
        mock_rag_adapter.py
        real_rag_adapter.py
        neo4j_kag_adapter.py
        elasticsearch_rag_adapter.py

      validators/
        contract_validator.py
        response_validator.py
        provenance_validator.py

      repositories/
        interaction_log_repository.py
        chat_session_repository.py
        music_catalog_repository.py
        query_constants.py

      services/
        main_recommendation_service.py
        chatbot_service.py
        llm_flow_service.py
        music_detail_service.py
        compact_state_builder.py
        request_lifecycle_cache.py
        session_cache_service.py
        session_flush_service.py

      cache/
        redis_client.py
        session_history_cache.py

      prompts/
        base_prompt.py
        intent_prompt.py
        recommendation_prompt.py
        response_prompt.py
        fallback_messages.py
        input_planner_prompt.py

      prompt_output_schema/
        input_planner_output_schema.py
        intent_output_schema.py
        response_output_schema.py

      response_parsers/
        input_planner_parser.py
        intent_parser.py
        response_parser.py

      schemas/
        session_context_schema.py
        kag_input_schema.py
        kag_state_schema.py
        rag_input_schema.py
        rag_state_schema.py
        response_state_schema.py
        interaction_log_schema.py
        music_detail_schema.py
        intent_state_schema.py

      contracts/
        fields.py
        enums.py

      policies/
        RecommendationPolicy.md
        RankingPolicy.md
        PromptPolicy.md

      common/
        constants.py
        default_state.py
        labels.py

      config/
        settings.py

  docker-compose.yml
  Dockerfile

  db/
    schema.sql
    seed.sql

  neo4j/
    data/
    common/
    data_insert.py
```

---

# 17. Docker Compose 구조

런타임 Docker 기준은 루트 `docker-compose.yml`과 루트 `Dockerfile`이다.

`neo4j/docker-compose.yml`은 Neo4j 단독 실행용 과거 구성 또는 참고 구성으로 취급하며, 운영/통합 런타임 기준에서 제외한다. Neo4j 데이터 적재 자동화가 필요하면 루트 compose 기준 one-shot loader 서비스 또는 별도 적재 명령으로 분리한다.

## 서비스 목록

- frontend
- backend
- db(PostgreSQL)
- redis
- neo4j
- elasticsearch

---

## 권장 포트

- React: 5173
- Backend: 8000
- PostgreSQL: 5432
- Redis: 6379
- Neo4j Browser: 7474
- Neo4j Bolt: 7687
- Elasticsearch: 9200

---

# 18. 구현 금지 규칙

금지:

- UI 추천 생성
- Validator 우회
- RAG 없는 추천 생성
- 내부 전략 노출
- 하드코딩
- 전역 상태 공유
- 직접 SQL 문자열 남발
- LLM 단독 추천 구조
- raw JSON 고객 노출
- Runtime Contract 임의 수정
- KAG Dispatch Agent 없이 KAG 직접 호출 금지
- RAG Dispatch Agent 없이 Retrieval 직접 호출 금지
- Adapter 우회 금지
- Mock/Real Adapter 직접 하드코딩 금지
- LLM이 content_id 생성 금지
- LLM이 title/artist 생성 금지
- 백엔드 애플리케이션 시작 시 Neo4j 대량 적재 금지
- 루트 compose를 우회한 Neo4j 런타임 compose 사용 금지
- broad Zustand subscribe
- duplicated API fetch
- duplicated retrieval
- duplicated validator run
- render 기반 API 호출
- derived state duplication
- Agent 내부 Provider 직접 선택 금지
- LLM이 KAG_STATE 생성 금지
- LLM이 RAG_STATE 생성 금지
- LLM이 recommendation_category 변경 금지
- retrieval_trace 외부 노출 금지
- validator_trace 외부 노출 금지
- Prompt 내부 hardcoded recommendation 금지

---

# 19. 단계별 구현 순서

1. Runtime Contract 고정
2. INTENT_STATE 고정
3. KAG_INPUT_JSON 구조 고정
4. RAG_INPUT_JSON 구조 고정
5. Internal Full State / Compact State 구조 고정
6. CompactStateBuilder 구현
7. PostgreSQL 설계
8. Redis Session 구조 구현
9. Neo4j MusicCatalog 기반 Graph 구성
10. RAG_STATE/RAG_INPUT_JSON 계약과 `ragStateBuilder` 고정
11. RAG `contractValidator` 형식/로직 검증 구현
12. Elasticsearch Index 구성
13. RAG retrieval/embedding/indexing 서비스 연결
14. LLM Layer 구현
15. Input Planner Agent 구현
16. KAG Dispatch Agent 구현
17. RAG Dispatch Agent 구현
18. FastAPI API 구현
19. Multi-Agent Flow 구현
20. Validator 구현
21. Music Detail Flow 구현
22. React UI 구현
23. Docker Compose 통합
24. 통합 테스트
25. Session Flush 테스트
26. Provenance Validation 테스트
27. 배포 준비

---

# 20. 테스트 기준

## 테스트 01

조건:

- personalized recommendation 요청

검증:

- personalized recommendation 반환
- duplicate recommendation 없음

---

## 테스트 02

조건:

- discovery recommendation 요청

검증:

- discovery recommendation 반환
- discovery ratio 정책 만족

---

## 테스트 03

조건:

- recommendation reason 질문

검증:

- recommendation evidence 기반 설명 반환
- hallucination 없음

---

## 테스트 04

조건:

- RAG_STATE 없는 content_id 포함

검증:

- Provenance Validation 실패
- fallback response 반환

---

## 테스트 05

조건:

- Runtime Contract 누락

검증:

- Contract Validation 실패
- LLM 실행 금지

---

## 테스트 06

조건:

- 동일 request_id 다중 요청

검증:

- duplicate request 차단
- inflight cache 동작

---

## 테스트 07

조건:

- 동일 API 반복 호출

검증:

- React Query cache 사용
- unnecessary fetch 없음

---
---

## 테스트 08

조건:

- Input Planner Agent가 정상 user_input을 처리한다.

검증:

- INTENT_STATE가 생성된다.
- KAG_INPUT_JSON이 생성된다.
- 허용 enum 밖의 mood, genre, situation이 포함되지 않는다.
- content_id, title, artist가 생성되지 않는다.

---

## 테스트 09

조건:

- LLM Provider가 invalid JSON을 반환한다.

검증:

- input_planner_parser.py 또는 response_parser.py가 실패 처리한다.
- fallback이 실행된다.
- success 저장이 차단된다.

---

## 테스트 10

조건:

- LLM이 KAG_STATE 또는 RAG_STATE를 생성하려고 한다.

검증:

- Parser 또는 Contract Validator가 실패 처리한다.
- LLM 결과가 폐기된다.
- KAG_STATE는 KAG Dispatch Agent 결과만 사용된다.
- RAG_STATE는 RAG Dispatch Agent 결과만 사용된다.

---

## 테스트 11

조건:

- Recommendation Agent가 selected_recommendations를 생성한다.

검증:

- selected_recommendations Contract를 만족한다.
- RAG_STATE에 없는 content_id가 포함되지 않는다.
- duplicate recommendation이 없다.
- rank와 score가 존재한다.

---

## 테스트 12

조건:

- Response Generator Agent가 selected_recommendations를 기반으로 RESPONSE_STATE를 생성한다.

검증:

- RESPONSE_STATE는 selected_recommendations 안의 content_id만 사용한다.
- title, artist가 변경되지 않는다.
- RAG evidence 밖 설명이 포함되지 않는다.
- Provenance Validator를 통과한다.

# 21. 완료 기준

## 기능 완료

- Main Recommendation Page 동작
- Chatbot Page 동작
- Redis Session Context 동작
- Neo4j KAG 동작
- Elasticsearch RAG 동작
- Multi-Agent Flow 동작
- Validator 동작
- CompactStateBuilder 동작
- Request Lifecycle Cache 동작
- Recommendation Agent가 section 구성, rerank, duplicate 제거, diversity 반영을 통합 수행
- Curation Agent 없이 Chatbot Flow 동작

---

## 저장 완료

- interaction_logs 저장
- chat_sessions 저장
- chat_session_turns 저장
- detail_view_logs 저장
- Session Flush 동작

---

## 검증 완료

- Response Validation 동작
- Provenance Validation 동작
- fallback 동작
- RAG 없는 추천 차단
- duplicated recommendation 차단
- hallucination 차단

---

## UI 완료

- React Recommendation UI 동작
- Chatbot UI 동작
- Recommendation Card UI 동작
- Developer Debug Panel 분리
- MusicDetailModal 동작
- URL 기반 Modal 동작
- unnecessary re-render 없음

---

# 22. 최종 핵심 정의 수정

RIMAS v4의 핵심은 다음이다.

"Spotify 음악 메타데이터와 그래프 기반 관계 탐색을 활용하여,
KAG/RAG Runtime Contract 기반 병렬 개발이 가능하며,
Internal Full State / Compact State 구조와 Validator 중심 검증 체계를 유지하는
Multi-Agent 음악 큐레이터 시스템"

