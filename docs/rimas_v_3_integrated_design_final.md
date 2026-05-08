# RIMAS_v3_Integrated_Design.md
# React + PostgreSQL + Redis + Neo4j + Elasticsearch 기반 음악 큐레이터 시스템 최종 통합 설계

---

# 1. 시스템 목표

RIMAS v3는 Spotify 기반 음악 메타데이터를 활용하여 사용자에게 개인화된 음악 큐레이션 경험을 제공하는 Multi-Agent 기반 음악 추천 시스템이다.

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

---

# 2. 핵심 설계 원칙

## 2.1 Runtime Contract 기반 구조

모든 실행 흐름은 JSON Contract 기반으로 동작한다.

필수 Runtime Contract:

- SESSION_CONTEXT
- KAG_STATE
- RAG_STATE
- RESPONSE_STATE
- INTERACTION_LOG

---

## 2.2 UI 원칙

UI는 절대 추천을 생성하지 않는다.

허용:

- API 호출
- 추천 카드 렌더링
- 세션 상태 표시
- 추천 이유 표시
- 큐레이터 응답 표시
- Developer Debug Panel 표시

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

## 2.3 LLM 원칙

LLM은 큐레이터 역할만 수행한다.

LLM 허용:

- 자연어 큐레이터 응답 생성
- 추천 이유 설명
- 음악 정보 설명
- 분위기 설명

LLM 금지:

- 추천 후보 생성
- 존재하지 않는 곡 생성
- 존재하지 않는 아티스트 생성
- 정책 판단
- Runtime Contract 수정
- 내부 코드 노출
- RAG_STATE 없는 응답 생성

---

## 2.4 Validator 중심 구조

최종 신뢰 기준은 Prompt가 아니라 Validator다.

검증:

- Response Validator
- Provenance Validator
- Contract Validator

---

## 2.5 데이터 중심 구조

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
→ Orchestrator Agent
→ Redis Session Context
→ Neo4j KAG
→ Elasticsearch RAG
→ LLM Curator Agent
→ Response Validator
→ Provenance Validator
→ Redis Save
→ PostgreSQL Flush
→ React Response

---

# 4. 전체 실행 흐름

## 4.1 Main Recommendation Flow

1. 사용자가 Main Recommendation Page 진입
2. Frontend가 recommendation API 호출
3. Backend API Layer 요청 수신
4. Redis Session Context 조회
5. Orchestrator Agent 실행
6. Neo4j KAG 추천 방향 탐색
7. Elasticsearch RAG 설명 근거 검색
8. ViewModel 생성
9. Validator 검증
10. PostgreSQL interaction_logs 저장
11. Frontend Response 반환
12. React Recommendation Section 렌더링

---

## 4.2 Chatbot Flow

1. 사용자가 ChatbotPage 입력
2. Frontend가 chatbot API 호출
3. API Layer 요청 수신
4. Redis Session Context 조회
5. Orchestrator Agent 실행
6. Intent Agent 실행
7. KAG Dispatch Agent 실행
8. Neo4j KAG 탐색
9. RAG Dispatch Agent 실행
10. Elasticsearch RAG 검색
11. Recommendation Agent 실행
12. Response Generator Agent 실행
13. Response Validator 검증
14. Provenance Validator 검증
15. Redis Session History 저장
16. PostgreSQL interaction_logs 저장
17. React UI 반환

---

## 4.3 Session Flush Flow

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
2. Intent Agent
3. KAG Dispatch Agent
4. RAG Dispatch Agent
5. Recommendation Agent
6. Response Generator Agent
7. Validator Controller

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

## 5.3 Intent Agent

### 역할

- 사용자 의도 분류

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
- Runtime Contract 수정

---

## 5.4 KAG Dispatch Agent

### 역할

- Neo4j 기반 추천 방향 결정
- 사용자 취향 관계 탐색
- content_id 후보 반환
- 추천 category 결정
- 추천 route 결정

### 출력

- KAG_STATE

### 금지

- 최종 자연어 생성
- 추천 이유 생성
- UI 렌더링
- RAG_STATE 수정

---

## 5.5 RAG Dispatch Agent

### 역할

- Elasticsearch 기반 설명 근거 검색
- 추천 이유 검색
- 음악 정보 검색
- 곡 설명 검색
- 분위기 설명 검색

### 출력

- RAG_STATE

### 금지

- 추천 전략 결정
- 존재하지 않는 곡 생성
- 최종 응답 생성
- KAG_STATE 수정

---

## 5.6 Recommendation Agent

### 역할

- RAG 후보 중 최종 표시 대상 선택

### 출력

- selected_recommendations

### 금지

- 새로운 content_id 생성
- title 수정
- artist 수정
- recommendation_category 수정

---

## 5.7 Response Generator Agent

### 역할

- DJ 큐레이터 스타일 응답 생성
- 추천 이유 설명
- 음악 정보 설명
- RESPONSE_STATE 생성

### 출력

- RESPONSE_STATE

### 금지

- 추천 후보 생성
- 존재하지 않는 곡 생성
- 내부 전략 노출
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
- Layout
- NotFoundPage

---

## 6.3 React 컴포넌트

- TopTasteHeader
- CharacterDjBanner
- RecommendationSection
- RecommendationCard
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

---

## 6.5 React 금지 규칙

금지:

- 추천 생성
- SQL 실행
- Neo4j 직접 호출
- Elasticsearch 직접 호출
- LLM 직접 호출
- Runtime Contract 수정
- raw JSON 기본 노출
- 내부 전략 노출

---

# 7. FastAPI Backend 구조

## 7.1 Backend 역할

- API 제공
- Multi-Agent 흐름 제어
- Validator 제어
- Session Cache 제어
- DB 저장

---

## 7.2 API Layer

### recommendation_routes.py

역할:

- Main Recommendation API 제공

### chatbot_routes.py

역할:

- Chatbot API 제공

### session_routes.py

역할:

- Session History API 제공
- Session Flush API 제공

---

## 7.3 Service Layer

### main_recommendation_service.py

역할:

- Main Recommendation Flow 실행

### chatbot_service.py

역할:

- Chatbot Flow 실행

### llm_flow_service.py

역할:

- Multi-Agent 흐름 실행

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

- user_input
- response_state
- kag_state
- rag_state
- selected_recommendations
- created_at

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

PostgreSQL은 영속 저장을 담당한다.

---

## 9.2 주요 테이블

- users
- music_catalog
- spotify_tracks
- spotify_audio_features
- spotify_artist_metadata
- spotify_genre_metadata
- spotify_mood_metadata
- spotify_lyrics
- interaction_logs
- chat_sessions
- chat_session_turns

---

## 9.3 users

역할:

- 사용자 정보 저장

---

## 9.4 music_catalog

역할:

- 통합 음악 메타데이터 저장

포함:

- track_id
- title
- artist
- genre
- mood
- situation_tags
- emotion_tags

---

## 9.5 spotify_tracks

역할:

- Spotify 원천 메타데이터 저장

---

## 9.6 spotify_audio_features

역할:

- Spotify audio feature 저장

포함:

- danceability
- energy
- valence
- acousticness
- instrumentalness
- speechiness
- tempo_bpm

---

## 9.7 interaction_logs

역할:

- 시스템 실행 로그 저장

저장:

- kag_state_json
- rag_state_json
- response_state_json
- validation_status
- latency_ms
- error_type

---

## 9.8 chat_sessions

역할:

- Session 메타데이터 저장

---

## 9.9 chat_session_turns

역할:

- 사용자 대화 히스토리 저장

---

# 10. Neo4j KAG 구조

## 10.1 목적

Neo4j는 음악 관계 기반 추천 방향 탐색을 담당한다.

---

## 10.2 Node 구조

- User
- Track
- Artist
- Genre
- Mood
- Playlist
- Situation
- Emotion

---

## 10.3 Relationship 구조

- User -[:LIKES_GENRE]-> Genre
- User -[:LIKES_MOOD]-> Mood
- User -[:LISTENED_TO]-> Track
- Track -[:HAS_GENRE]-> Genre
- Track -[:HAS_MOOD]-> Mood
- Track -[:SIMILAR_TO]-> Track
- Genre -[:ADJACENT_TO]-> Genre
- Mood -[:COMPATIBLE_WITH]-> Mood
- Track -[:FITS_SITUATION]-> Situation
- Track -[:HAS_EMOTION]-> Emotion

---

## 10.4 KAG 역할

KAG는:

- 추천 방향 결정
- 추천 후보 탐색
- 취향 확장 경로 탐색
- recommendation_category 결정
- route 결정
- UI section 방향 결정

---

## 10.5 KAG 금지 규칙

금지:

- 최종 자연어 생성
- 추천 이유 생성
- UI 렌더링
- RAG_STATE 수정
- RESPONSE_STATE 생성

---

# 11. Elasticsearch RAG 구조

## 11.1 목적

Elasticsearch는 추천 이유와 설명 근거 검색을 담당한다.

---

## 11.2 Index 구조

- rimas_tracks
- rimas_lyrics
- rimas_artist_info
- rimas_genre_info
- rimas_mood_info
- rimas_recommendation_evidence

---

## 11.3 저장 메타데이터

Track:

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

---

## 11.4 RAG 역할

RAG는:

- 추천 이유 제공
- 음악 설명 제공
- 곡 정보 제공
- 분위기 설명 제공
- recommendation evidence 제공

---

## 11.5 RAG 금지 규칙

금지:

- 추천 전략 결정
- 존재하지 않는 곡 생성
- 최종 응답 생성
- KAG_STATE 수정

---

# 12. Runtime Contract

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

## 12.2 KAG_STATE

```json
{
  "status": "success",
  "recommendation_goal": {
    "primary_goal": "discovery_recommendation"
  },
  "recommended_content_ids": [
    "track_001",
    "track_002"
  ],
  "recommendation_category": "discovery_candidate",
  "route": "safe_discovery",
  "target_section": "discovery_section"
}
```

---

## 12.3 RAG_STATE

```json
{
  "status": "success",
  "recommended_content_evidence": [
    {
      "content_id": "track_001",
      "title": "Midnight Loop",
      "artist": "Nova Lane",
      "genre": ["indie"],
      "mood": ["night"],
      "evidence_summary": "차분한 밤 분위기와 연결되는 곡"
    }
  ],
  "recommendation_reason": {
    "summary": "사용자의 최근 선호 분위기와 연결되는 곡"
  }
}
```

---

## 12.4 RESPONSE_STATE

```json
{
  "status": "success",
  "response_type": "curator_recommendation",
  "chatbot_response": "차분한 밤 분위기를 좋아한다면 Midnight Loop를 추천드릴게요.",
  "display_recommendations": [
    {
      "content_id": "track_001",
      "title": "Midnight Loop",
      "artist": "Nova Lane",
      "label": "취향 기반 추천",
      "display_reason": "차분한 밤 분위기와 연결되는 곡"
    }
  ],
  "used_content_ids": [
    "track_001"
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

## 13.3 Session Flush API

### Endpoint

POST /api/sessions/{session_id}/flush

---

## 13.4 Session History API

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

실패 시:

- fallback 전환
- success 저장 금지

---

# 15. Prompt 구조

## 15.1 Prompt 목록

- intent_prompt.py
- kag_prompt.py
- rag_prompt.py
- recommendation_prompt.py
- response_prompt.py
- fallback_messages.py

---

## 15.2 Prompt 공통 규칙

모든 Prompt는:

- JSON 출력만 허용
- Runtime Contract 수정 금지
- RAG 없는 추천 금지
- 내부 전략 노출 금지
- hallucination 금지

---

# 16. Folder Structure

```txt
rimas/
  frontend/
    src/
      pages/
        MainRecommendationPage.tsx
        ChatbotPage.tsx

      components/
        RecommendationCard.tsx
        RecommendationSection.tsx
        ChatHistory.tsx
        ChatInput.tsx
        CuratorResponseArea.tsx
        CharacterDjBanner.tsx
        DeveloperDebugPanel.tsx

      stores/
        userStore.ts
        recommendationStore.ts
        chatStore.ts

      api/
        recommendationApi.ts
        chatbotApi.ts
        sessionApi.ts

      types/
        kagState.ts
        ragState.ts
        responseState.ts

      styles/
        theme.ts
        globals.css

  backend/
    app/
      api/
        recommendation_routes.py
        chatbot_routes.py
        session_routes.py

      agents/
        orchestrator_agent.py
        intent_agent.py
        kag_dispatch_agent.py
        rag_dispatch_agent.py
        recommendation_agent.py
        response_generator.py

      adapters/
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
        session_cache_service.py
        session_flush_service.py

      cache/
        redis_client.py
        session_history_cache.py

      schemas/
        session_context_schema.py
        kag_state_schema.py
        rag_state_schema.py
        response_state_schema.py
        interaction_log_schema.py

      contracts/
        fields.py
        enums.py

      common/
        constants.py
        default_state.py
        labels.py

      config/
        settings.py

  infra/
    docker-compose.yml

    postgres/

    redis/

    neo4j/

    elasticsearch/
```

---

# 17. Docker Compose 구조

## 서비스 목록

- frontend
- backend
- postgres
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

---

# 19. 단계별 구현 순서

1. Runtime Contract 고정
2. PostgreSQL 설계
3. Redis Session 구조 구현
4. Neo4j Graph 구성
5. Elasticsearch Index 구성
6. FastAPI API 구현
7. Multi-Agent Flow 구현
8. Validator 구현
9. React UI 구현
10. Docker Compose 통합
11. 통합 테스트
12. Session Flush 테스트
13. Provenance Validation 테스트
14. 배포 준비

---

# 20. 테스트 기준

## 테스트 01

조건:

- personalized recommendation 요청

검증:

- personalized recommendation 반환

---

## 테스트 02

조건:

- discovery recommendation 요청

검증:

- discovery recommendation 반환

---

## 테스트 03

조건:

- recommendation reason 질문

검증:

- recommendation evidence 기반 설명 반환

---

## 테스트 04

조건:

- RAG_STATE 없는 content_id 포함

검증:

- Provenance Validation 실패

---

## 테스트 05

조건:

- Runtime Contract 누락

검증:

- Contract Validation 실패

---

# 21. 완료 기준

## 기능 완료

- Main Recommendation Page 동작
- Chatbot Page 동작
- Redis Session Context 동작
- Neo4j KAG 동작
- Elasticsearch RAG 동작
- Multi-Agent Flow 동작
- Validator 동작

---

## 저장 완료

- interaction_logs 저장
- chat_sessions 저장
- chat_session_turns 저장
- Session Flush 동작

---

## 검증 완료

- Response Validation 동작
- Provenance Validation 동작
- fallback 동작
- RAG 없는 추천 차단

---

## UI 완료

- React Recommendation UI 동작
- Chatbot UI 동작
- Recommendation Card UI 동작
- Developer Debug Panel 분리

---

# 22. 최종 핵심 정의

RIMAS v3의 핵심은 다음이다.

"Spotify 음악 메타데이터와 그래프 기반 관계 탐색을 활용하여,
세션 맥락 기반 개인화 큐레이션을 제공하는
Validator 중심 Multi-Agent 음악 추천 시스템"

