# RIMAS Design.md v2
# Personalized Music Recommendation + Curator-Based Expansion Architecture

---

# 1. 문서 목적

본 문서는 RIMAS 시스템의 전체 설계 기준을 정의한다.

RIMAS v2는 기존의 사용자 기반 개인화 추천을 제거하지 않는다.
기존 개인화 추천을 기본 축으로 유지하면서, 다음 기능을 확장한다.

1. 기존 사용자 취향 기반 추천
2. 새로 업데이트된 노래 추천
3. 새로운 취향 탐색 추천
4. 사용자가 원하는 음악/아티스트/장르 정보 제공
5. LLM 기반 큐레이터형 설명

따라서 RIMAS v2의 핵심은 다음과 같다.

- ML은 사용자 상태와 취향 기반 입력 정보를 제공한다.
- KAG는 사용자 기반 추천 방향과 큐레이션 경로를 결정한다.
- RAG는 추천 후보와 설명 근거를 제공한다.
- LLM은 추천 후보를 새로 만들지 않고, 사용자가 이해하기 쉬운 큐레이터형 자연어 응답만 생성한다.
- UI는 추천 결과와 설명을 보기 좋게 표시하고, 내부 판단 지표는 고객에게 노출하지 않는다.

---

# 2. 기존 설계에서 유지할 핵심 원칙

기존 Design.md에서 유지할 원칙은 다음과 같다.

1. JSON 계약 기반 시스템
2. ML Output / KAG_STATE / RAG_STATE 원본 수정 금지
3. KAG_STATE는 의사결정 기준
4. RAG_STATE는 추천 및 설명 근거 기준
5. LLM은 자연어 응답만 생성
6. UI는 Service만 호출
7. UI에서 추천 생성 금지
8. 고객 UI에 내부 판단 지표 노출 금지
9. Contract Validation 실패 시 LLM 실행 금지
10. Response Validation 실패 시 fallback 전환
11. Provenance Validation 실패 시 fallback 전환
12. PostgreSQL 로그 저장
13. Mock Adapter → Real Adapter 교체 가능 구조 유지

---

# 3. 기존 설계에서 변경되는 부분

기존 설계의 중심:
- 이탈 방지
- 잔류 설득
- churn_reason 기반 전략
- retention_reason 기반 응답
- Chat Area가 추천 UI 내부 보조 영역으로 존재

변경 후 설계의 중심:
- 개인화 음악 추천
- 최신 업데이트 음악 추천
- 새 취향 탐색
- 음악 정보 큐레이션
- Chatbot Page 별도 분리
- LLM은 설득자가 아니라 음악 큐레이터 역할 수행

단, 기존의 사용자 상태 기반 추천은 유지한다.
즉, 큐레이터 역할은 기존 추천을 대체하는 것이 아니라 기존 추천 결과를 더 잘 설명하고 확장하는 역할이다.

---

# 4. 전체 시스템 목표

RIMAS v2의 목표는 다음과 같다.

1. 사용자의 기존 취향을 기반으로 적합한 음악을 추천한다.
2. 사용자의 기존 취향과 연결되는 최신 업데이트 음악을 추천한다.
3. 사용자의 기존 취향에서 확장 가능한 새로운 취향 후보를 추천한다.
4. 사용자가 음악, 아티스트, 장르, 추천 이유를 질문하면 설명한다.
5. 추천 결과를 단순 리스트가 아니라 DJ 큐레이션 경험처럼 제공한다.
6. 추천과 설명의 근거는 반드시 KAG_STATE / RAG_STATE / ML Output 기반으로 제한한다.

---

# 5. 전체 시스템 흐름

## 5.1 Main Recommendation Page 진입 흐름

Page Entry
→ selected_user_id 확인
→ ML Output 조회
→ KAG_STATE 생성 또는 수신
→ RAG_STATE 생성 또는 수신
→ Contract Validation
→ Recommendation View Model 생성
→ Main Recommendation Page 출력
→ interaction_logs 저장

## 5.2 Chatbot Page 질문 흐름

User Input
→ selected_user_id 확인
→ ML Output 조회
→ KAG_STATE 생성 또는 수신
→ RAG_STATE 생성 또는 수신
→ Contract Validation
→ Intent Agent
→ Curation Agent
→ Recommendation Agent
→ Response Generator
→ Response Validation
→ Provenance Validation
→ interaction_logs 저장
→ Chatbot Page 출력

## 5.3 전체 통합 흐름

User Input / Page Entry
→ ML Output 조회
→ KAG_STATE 수신
→ RAG_STATE 수신
→ Contract Validation
→ LLM Curator Flow
→ Response Validation
→ Provenance Validation
→ DB 저장
→ UI 출력

---

# 6. 시스템 레이어 구조

## 6.1 UI Layer

역할:
- 사용자 입력을 받는다.
- Main Recommendation Page를 출력한다.
- Chatbot Page를 출력한다.
- 추천 카드, DJ 메시지, 개인화 안내, 음악 정보 응답을 표시한다.
- Developer Debug Panel을 developer_mode=True일 때만 표시한다.

입력:
- user_id
- user_input
- page_state
- response_state

출력:
- recommendation_cards
- chatbot_response
- personalized_guide
- debug_panel

금지:
- SQL 직접 실행 금지
- ML Output 수정 금지
- KAG_STATE 수정 금지
- RAG_STATE 수정 금지
- 추천 생성 금지
- LLM 직접 호출 금지
- 내부 판단 지표 고객 노출 금지

---

## 6.2 Service Layer

역할:
- 전체 실행 흐름을 제어한다.
- Repository, Adapter, Validator, Agent, LLM Flow를 조합한다.
- Main Recommendation Page와 Chatbot Page의 실행 흐름을 분리한다.
- 성공/실패 결과를 interaction_logs에 저장한다.

입력:
- user_id
- user_input
- page_type

출력:
- response_state
- view_model
- log_result

금지:
- JSON 계약 임의 변경 금지
- Validation 실패 무시 금지
- KAG/RAG 결과 임의 수정 금지
- UI 렌더링 직접 수행 금지

---

## 6.3 Repository Layer

역할:
- PostgreSQL 조회 및 저장을 담당한다.
- ML Output을 조회한다.
- interaction_logs를 저장한다.
- SQL은 query_constants.py에서 상수화한다.

입력:
- user_id
- interaction_log
- query_parameter

출력:
- ml_output
- saved_log_id
- query_result

금지:
- 비즈니스 정책 판단 금지
- LLM 호출 금지
- UI 의존 금지
- SQL 하드코딩 금지

---

## 6.4 Adapter Layer

역할:
- KAG_STATE와 RAG_STATE를 반환한다.
- MockKagAdapter / RealKagAdapter를 동일 인터페이스로 분리한다.
- MockRagAdapter / RealRagAdapter를 동일 인터페이스로 분리한다.
- 구현체 교체 시 Service Layer 코드는 변경하지 않는다.

입력:
- user_id
- user_input
- ml_output
- kag_state

출력:
- KAG_STATE
- RAG_STATE

금지:
- 최종 자연어 응답 생성 금지
- JSON 구조 임의 변경 금지
- LLM 역할 수행 금지
- UI 렌더링 금지

---

## 6.5 KAG Layer

역할:
- 사용자 기반 추천 방향을 결정한다.
- 큐레이션 의도를 결정한다.
- 추천 모드를 결정한다.
- UI 라우팅 방향을 결정한다.
- 기존 개인화 추천, 최신곡 추천, 새 취향 탐색, 정보 제공 모드를 구분한다.

KAG는 다음을 담당한다.

1. 사용자 기반 추천 방향 결정
- 기존 취향 유지 추천
- 기존 장르 기반 추천
- 기존 분위기 기반 추천
- 최근 활동 기반 추천
- 사용자의 현재 상태 기반 추천 강도 조정

2. 신규 업데이트 추천 방향 결정
- 최신곡 추천 여부 결정
- 최신곡을 기존 취향과 연결할지 결정
- 최신곡을 새 취향 확장으로 보여줄지 결정

3. 새로운 취향 탐색 방향 결정
- 기존 취향과 가까운 확장
- 기존 분위기와 연결되는 다른 장르
- 너무 이질적이지 않은 새 장르
- 아티스트 기반 탐색
- 분위기 기반 탐색

4. 정보 제공 방향 결정
- 곡 정보 질문
- 아티스트 정보 질문
- 장르 정보 질문
- 추천 이유 질문
- 플레이리스트 맥락 질문

5. UI 라우팅 결정
- main_recommendation_page
- chatbot_page
- personalized_recommendation_section
- new_release_section
- discovery_section
- information_answer_section

KAG가 하지 않는 것:
- 실제 음악 후보 생성 금지
- 추천 이유 문장 생성 금지
- 최종 응답 생성 금지
- RAG_STATE 수정 금지
- ML Output 수정 금지

---

## 6.6 RAG Layer

역할:
- 추천 후보를 제공한다.
- 추천 근거를 제공한다.
- 음악 정보 설명 근거를 제공한다.
- LLM 응답의 provenance 기준이 된다.

RAG는 다음을 담당한다.

1. 기존 유저 기반 추천 후보 제공
- taste_profile과 연결되는 곡
- preferred_genres와 연결되는 곡
- preferred_mood와 연결되는 곡
- 최근 감상 패턴과 연결되는 곡
- 사용자의 기존 취향을 유지하는 추천 후보

2. 신규 업데이트 추천 후보 제공
- 최근 업데이트된 곡
- 신규 발매곡
- 새로 추가된 플레이리스트 후보
- 기존 취향과 연결 가능한 최신곡

3. 새로운 취향 탐색 후보 제공
- 기존 장르와 인접한 장르
- 기존 분위기와 연결되는 다른 스타일
- 사용자가 부담 없이 시도 가능한 확장 후보
- 기존 취향에서 너무 멀지 않은 안전한 확장 후보

4. 음악 정보 근거 제공
- 곡 설명
- 아티스트 설명
- 장르 설명
- 추천 이유 설명
- 플레이리스트 설명
- 음악적 분위기 설명

5. LLM 응답 근거 제공
- recommended_content_evidence
- recommendation_reason
- information_evidence
- recommendation_scripts

RAG가 하지 않는 것:
- 사용자 전략 결정 금지
- UI 라우팅 결정 금지
- KAG_STATE 수정 금지
- 최종 자연어 응답 생성 금지
- 존재하지 않는 음악 후보 생성 금지

---

## 6.7 Agent Layer

구성:
1. Intent Agent
2. Curation Agent
3. Recommendation Agent
4. Response Generator

### Intent Agent

역할:
- user_input의 의도를 분류한다.

입력:
- user_input
- KAG_STATE
- RAG_STATE

출력:
- intent_result

의도 유형:
- personalized_recommendation
- new_release_recommendation
- new_taste_discovery
- similar_taste_recommendation
- music_information_question
- recommendation_reason_question
- general_chat

금지:
- 추천 후보 생성 금지
- RAG_STATE에 없는 음악 언급 금지

### Curation Agent

역할:
- KAG_STATE의 curation_strategy와 RAG_STATE의 evidence를 기반으로 응답 방향을 구성한다.

입력:
- intent_result
- KAG_STATE
- RAG_STATE

출력:
- curation_plan

처리:
- 개인화 추천 중심인지 판단
- 최신곡 중심인지 판단
- 새 취향 탐색 중심인지 판단
- 정보 설명 중심인지 판단
- 응답 톤 결정
- 사용할 RAG evidence 범위 선택

금지:
- KAG_STATE에 없는 전략 생성 금지
- RAG_STATE에 없는 추천 생성 금지

### Recommendation Agent

역할:
- RAG_STATE의 recommended_content_evidence에서 UI와 응답에 사용할 후보를 선택한다.

입력:
- curation_plan
- RAG_STATE

출력:
- selected_recommendations

처리:
- content_id 기준 선택
- recommendation_category 기준 분류
- personalized / new_release / discovery / similar 기준 그룹핑
- UI 카드용 데이터 추출

금지:
- 새로운 content_id 생성 금지
- title, artist, genre 임의 생성 금지

### Response Generator

역할:
- 최종 자연어 응답을 생성한다.

입력:
- user_input
- ML Output
- KAG_STATE
- RAG_STATE
- selected_recommendations
- curation_plan

출력:
- RESPONSE_STATE

처리:
- DJ 큐레이터 스타일 응답 생성
- 추천 이유 설명
- 음악 정보 설명
- fallback 응답 생성

금지:
- 추천 후보 생성 금지
- RAG_STATE에 없는 음악 언급 금지
- 내부 전략명 고객 노출 금지
- churn 관련 원문 고객 노출 금지

---

## 6.8 Validator Layer

구성:
1. Contract Validator
2. Response Validator
3. Provenance Validator

### Contract Validator

역할:
- KAG_STATE / RAG_STATE / ML Output 구조 검증

검증:
- 필수 필드 존재 여부
- 타입 검증
- status 값 검증
- 배열/객체 구조 검증
- content_id 중복 검증
- recommendation_category 허용값 검증

실패 시:
- LLM 실행 금지
- fallback 응답 생성
- interaction_logs 저장

### Response Validator

역할:
- LLM 출력 구조 검증

검증:
- status 존재 여부
- chatbot_response 존재 여부
- display_recommendations 구조 검증
- used_content_ids 구조 검증
- fallback 여부 검증

실패 시:
- fallback 응답 전환
- success로 저장 금지

### Provenance Validator

역할:
- LLM 응답이 KAG/RAG/ML 근거를 벗어나지 않았는지 검증

검증:
- used_content_ids가 RAG_STATE.recommended_content_evidence에 존재하는지 확인
- display_recommendations의 title/artist가 RAG_STATE와 일치하는지 확인
- 내부 전략명이 고객 응답에 노출되지 않았는지 확인
- KAG_STATE에 없는 route/strategy/action을 사용하지 않았는지 확인
- ML Output이 LLM 전후 동일한지 확인

실패 시:
- fallback 응답 전환
- validation_status = failed 저장
- success로 저장 금지

---

# 7. 페이지 구조

## 7.1 Main Recommendation Page

목적:
- 사용자에게 추천 결과를 가장 먼저 보여준다.
- 기존 개인화 추천, 신규 업데이트 추천, 새 취향 탐색 추천을 카드로 표시한다.
- Chatbot Page로 이동할 수 있는 진입점을 제공한다.

구성:
1. Top Taste Header
2. Character DJ Banner
3. Personalized Recommendation Section
4. New Release Section
5. Discovery Section
6. Personalized Guide Section
7. Chatbot Page 이동 버튼
8. Developer Debug Panel

표시:
- user_id
- 취향 뱃지
- 오늘의 추천 테마
- 추천 음악 카드
- 추천 이유
- 큐레이터 안내 문구

금지:
- churn_probability 표시 금지
- churn_risk_level 표시 금지
- churn_reason 원문 표시 금지
- internal segment 표시 금지
- recommendation_strategy 내부명 표시 금지
- selected_path 표시 금지
- raw JSON 표시 금지
- Evidence Panel 고객 노출 금지
- Strategy Panel 고객 노출 금지

---

## 7.2 Chatbot Page

목적:
- 사용자가 음악에 대해 질문하고 설명을 받을 수 있는 별도 페이지이다.
- 추천 이유, 음악 정보, 아티스트 정보, 새 취향 탐색 질문을 처리한다.

구성:
1. Chat Header
2. Chat History
3. User Input
4. Curator Response Area
5. Related Recommendation Cards
6. Developer Debug Panel

처리 가능한 질문:
- “나한테 맞는 노래 추천해줘”
- “새로 나온 노래 중에 추천해줘”
- “내 취향이랑 다른 것도 추천해줘”
- “이 노래 왜 추천했어?”
- “이 아티스트는 어떤 스타일이야?”
- “비슷한 분위기의 다른 곡도 있어?”

금지:
- RAG_STATE에 없는 곡 추천 금지
- 존재하지 않는 아티스트 정보 생성 금지
- 내부 전략명 노출 금지

---

# 8. 폴더 구조

rimas/
  app/
    main.py

    common/
      constants.py
      default_state.py
      labels.py

    pages/
      main_recommendation_page.py
      chatbot_page.py

    ui/
      components/
        sidebar.py
        top_taste_header.py
        character_dj_banner.py
        personalized_recommendation_section.py
        new_release_section.py
        discovery_section.py
        recommendation_card_section.py
        personalized_guide_section.py
        music_taste_section.py
        chat_area.py
        chatbot_header.py
        related_recommendation_cards.py
        developer_debug_panel.py

      styles/
        theme.py
        css.py

    services/
      main_recommendation_service.py
      chatbot_service.py
      llm_flow_service.py
      validation_service.py
      logging_service.py
      view_model_service.py

    agents/
      intent_agent.py
      curation_agent.py
      recommendation_agent.py
      response_generator.py

    adapters/
      kag_adapter.py
      rag_adapter.py
      mock_kag_adapter.py
      mock_rag_adapter.py
      real_kag_adapter.py
      real_rag_adapter.py

    validators/
      contract_validator.py
      response_validator.py
      provenance_validator.py

    repositories/
      ml_output_repository.py
      interaction_log_repository.py
      query_constants.py

    schemas/
      ml_output_schema.py
      kag_state_schema.py
      rag_state_schema.py
      intent_result_schema.py
      curation_plan_schema.py
      selected_recommendation_schema.py
      response_state_schema.py
      interaction_log_schema.py

    contracts/
      ml_output_example.json
      kag_state_example.json
      rag_state_example.json
      intent_result_example.json
      curation_plan_example.json
      selected_recommendations_example.json
      response_state_example.json
      interaction_log_example.json

    config/
      settings.py

  docs/
    Design.md
    기능정의서.md
    요구사항 정의서.md
    WBS.md
    JSON_CONTRACT.md
    UX_IMPLEMENTATION_PLAN.md

  tests/
    test_contract_validator.py
    test_response_validator.py
    test_provenance_validator.py
    test_main_recommendation_service.py
    test_chatbot_service.py
    test_mock_kag_adapter.py
    test_mock_rag_adapter.py

---

# 9. 단계별 Input / Output 스키마

## 9.1 ML Output 조회 단계

목적:
- 사용자 기반 추천에 필요한 기본 상태와 취향 정보를 조회한다.

Input:
{
  "user_id": "user_001"
}

Output:
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

필수 필드:
- status
- user_id
- taste_profile
- behavior_profile
- recommendation_profile

---

## 9.2 KAG_STATE 생성 단계

목적:
- 사용자 상태와 입력을 기반으로 추천 방향과 큐레이션 경로를 결정한다.

Input:
{
  "user_input": "새로운 취향으로 들을만한 노래 추천해줘",
  "ml_output": {
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
}

Output:
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

필수 필드:
- status
- user
- recommendation_goal
- user_context
- curation_intent
- curation_strategy
- content_requirements
- routing
- selected_path

허용 status:
- success
- partial_match
- empty_result
- timeout
- error

---

## 9.3 RAG_STATE 생성 단계

목적:
- KAG_STATE가 결정한 방향에 맞는 추천 후보와 설명 근거를 제공한다.

Input:
{
  "kag_state": {
    "status": "success",
    "user": {
      "user_id": "user_001"
    },
    "recommendation_goal": {
      "primary_goal": "new_taste_discovery",
      "secondary_goal": "personalized_recommendation"
    },
    "curation_intent": {
      "intent_type": "new_taste_discovery"
    },
    "content_requirements": {
      "must_include": ["personalized_match", "discovery_candidate"],
      "optional_include": ["new_release"],
      "avoid": ["too_aggressive_genre_shift"]
    }
  }
}

Output:
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
    },
    {
      "content_id": "track_002",
      "title": "Soft Orbit",
      "artist": "Luna Field",
      "album": "Orbit Notes",
      "genre": ["dream_pop", "ambient"],
      "mood": ["calm", "night", "soft"],
      "tempo": "slow",
      "release_type": "existing_catalog",
      "recommendation_category": "discovery_candidate",
      "evidence_summary": "기존 calm/night 분위기와 연결되지만 dream_pop/ambient 계열로 취향 확장이 가능한 곡",
      "match_reason": {
        "genre_match": false,
        "mood_match": true,
        "tempo_match": false,
        "new_taste_expansion": true
      }
    },
    {
      "content_id": "track_003",
      "title": "Fresh Signal",
      "artist": "Mira Tone",
      "album": "Updated Signal",
      "genre": ["indie", "electro_pop"],
      "mood": ["bright", "clean"],
      "tempo": "medium",
      "release_type": "new_release",
      "recommendation_category": "new_release",
      "evidence_summary": "최근 업데이트된 곡이며 사용자의 indie 선호와 일부 연결됨",
      "match_reason": {
        "genre_match": true,
        "mood_match": false,
        "tempo_match": true,
        "new_taste_expansion": true
      }
    }
  ],
  "recommendation_reason": {
    "summary": "기존 개인화 추천을 기본으로 유지하면서, 부담 없는 새 취향 후보와 최신 업데이트 곡을 함께 구성함",
    "reason_items": [
      "기존 rnb/indie 취향과 연결되는 곡을 포함함",
      "calm/night 분위기를 유지하면서 새로운 장르로 확장 가능한 곡을 포함함",
      "최근 업데이트된 곡 중 기존 취향과 일부 연결되는 곡을 포함함"
    ]
  },
  "information_evidence": [
    {
      "info_id": "genre_dream_pop_001",
      "info_type": "genre",
      "title": "dream_pop",
      "summary": "부드러운 사운드와 몽환적인 분위기가 특징인 장르로, calm/night 무드와 연결하기 좋음"
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

필수 필드:
- status
- recommendation_context
- recommended_content_evidence
- recommendation_reason
- recommendation_scripts

권장 필드:
- information_evidence

recommended_content_evidence 필수 필드:
- content_id
- title
- artist
- genre
- mood
- release_type
- recommendation_category
- evidence_summary

recommendation_category 허용값:
- personalized_match
- similar_taste
- new_release
- discovery_candidate
- information_related

release_type 허용값:
- existing_catalog
- new_release
- updated_playlist
- unknown

---

## 9.4 Intent Agent 단계

Input:
{
  "user_input": "이 노래 왜 추천했어?",
  "kag_state": {},
  "rag_state": {}
}

Output:
{
  "status": "success",
  "intent_type": "recommendation_reason_question",
  "confidence": 0.91,
  "target_content_id": "track_002",
  "requires_recommendation": false,
  "requires_information": true
}

intent_type 허용값:
- personalized_recommendation
- new_release_recommendation
- new_taste_discovery
- similar_taste_recommendation
- music_information_question
- recommendation_reason_question
- general_chat

---

## 9.5 Curation Agent 단계

Input:
{
  "intent_result": {},
  "kag_state": {},
  "rag_state": {}
}

Output:
{
  "status": "success",
  "curation_mode": "explain_recommendation_reason",
  "response_focus": "discovery_candidate",
  "tone": "friendly_dj",
  "allowed_content_ids": ["track_001", "track_002", "track_003"],
  "primary_content_id": "track_002",
  "use_information_evidence": true
}

curation_mode 허용값:
- recommend_personalized
- recommend_new_release
- recommend_discovery
- explain_recommendation_reason
- explain_music_information
- general_curator_response
- fallback

---

## 9.6 Recommendation Agent 단계

Input:
{
  "curation_plan": {},
  "rag_state": {}
}

Output:
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

검증:
- selected_recommendations.content_id는 RAG_STATE.recommended_content_evidence에 반드시 존재해야 한다.
- title, artist는 RAG_STATE의 값과 반드시 일치해야 한다.
- display_reason은 evidence_summary 또는 recommendation_reason 기반이어야 한다.

---

## 9.7 Response Generator 단계

Input:
{
  "user_input": "새로운 취향으로 들을만한 노래 추천해줘",
  "ml_output": {},
  "kag_state": {},
  "rag_state": {},
  "curation_plan": {},
  "selected_recommendations": []
}

Output:
{
  "status": "success",
  "response_type": "curator_recommendation",
  "chatbot_response": "기존에 좋아하던 차분한 밤 분위기는 유지하면서, 조금 새로운 결로 넘어갈 수 있는 곡으로 Luna Field의 Soft Orbit을 추천드릴게요. dream pop과 ambient 쪽으로 살짝 확장되는 곡이라 낯설지만 부담스럽지는 않을 거예요.",
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
      "taste_profile.preferred_moods",
      "recommendation_profile.discovery_readiness"
    ],
    "used_kag_fields": [
      "recommendation_goal.primary_goal",
      "curation_intent.intent_type",
      "curation_strategy.strategy_code",
      "content_requirements.must_include"
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

---

## 9.8 DB 저장 단계

Input:
{
  "user_id": "user_001",
  "user_input": "새로운 취향으로 들을만한 노래 추천해줘",
  "ml_output": {},
  "kag_state": {},
  "rag_state": {},
  "response_state": {},
  "validation_result": {},
  "latency_ms": 1420
}

Output:
{
  "status": "success",
  "log_id": "log_20260504_0001",
  "saved_at": "2026-05-04T19:30:00+09:00"
}

저장 필드:
- log_id
- user_id
- user_input
- ml_output_json
- kag_state_json
- rag_state_json
- response_state_json
- validation_status
- error_type
- latency_ms
- created_at

저장 규칙:
- JSON 원본 그대로 저장
- success/fallback/error 모두 저장
- Validation 실패 응답은 success로 저장하지 않는다.
- LLM 호출 실패도 로그 저장한다.

---

# 10. 상태값 정의

공통 status 허용값:
- success
- partial_match
- empty_result
- timeout
- error

상태별 의미:

success:
- 모든 필수 데이터가 존재하고 정상 처리됨

partial_match:
- 일부 추천 근거는 부족하지만 최소 응답 가능

empty_result:
- 추천 후보 또는 정보 근거가 없음

timeout:
- KAG/RAG/LLM 호출 제한 시간 초과

error:
- 구조 오류, 호출 실패, 검증 실패 등 시스템 오류

---

# 11. UI 표시 정책

## 11.1 고객 UI 표시 허용

표시 가능:
- 추천 음악 제목
- 아티스트
- 앨범명
- 장르
- 분위기
- 추천 이유
- DJ 큐레이터 메시지
- 개인화 안내 문구
- 최신곡 안내
- 새 취향 탐색 안내
- 음악 정보 설명

## 11.2 고객 UI 표시 금지

표시 금지:
- churn_probability
- churn_risk_level
- churn_reason 원문
- internal segment
- curation_strategy 내부 코드
- selected_path
- raw JSON
- ML Output 원본
- KAG_STATE 원본
- RAG_STATE 원본
- validation 내부 상세
- Strategy Panel
- Evidence Panel

## 11.3 Developer Debug Panel 표시

조건:
- developer_mode = True

표시:
- ML Output
- KAG_STATE
- RAG_STATE
- selected_path
- validation_result
- latency_ms
- error_type

기본:
- 숨김

---

# 12. Session State

SESSION_DEFAULTS = {
    "selected_user_id": "user_001",
    "current_page": "main_recommendation_page",
    "current_ml_output": None,
    "current_kag_state": None,
    "current_rag_state": None,
    "current_response_state": None,
    "chat_history": [],
    "last_status": None,
    "last_error": None
}

UI_SESSION_DEFAULTS = {
    "developer_mode": False,
    "selected_taste_badge": None,
    "character_message": None,
    "recommendation_groups": {
        "personalized_match": [],
        "similar_taste": [],
        "new_release": [],
        "discovery_candidate": []
    }
}

규칙:
- session_state는 UI 상태 관리에만 사용한다.
- KAG/RAG/ML 원본은 session_state에서 수정하지 않는다.
- 전역 변수로 상태를 공유하지 않는다.
- 페이지 간 공유가 필요한 데이터는 Service Layer를 통해 재조회하거나 안전하게 전달한다.

---

# 13. 예외 처리 정책

## 13.1 ML Output 없음

처리:
- KAG 실행 금지
- RAG 실행 금지
- LLM 실행 금지
- fallback 응답 생성
- interaction_logs 저장

error_type:
- ML_OUTPUT_NOT_FOUND

## 13.2 KAG 실패

처리:
- RAG 실행 금지
- LLM 실행 금지
- fallback 응답 생성
- interaction_logs 저장

error_type:
- KAG_STATE_ERROR

## 13.3 RAG 실패

처리:
- LLM 실행 금지
- fallback 응답 생성
- interaction_logs 저장

error_type:
- RAG_STATE_ERROR

## 13.4 Contract Validation 실패

처리:
- LLM 실행 금지
- fallback 응답 생성
- interaction_logs 저장

error_type:
- CONTRACT_VALIDATION_FAILED

## 13.5 LLM 호출 실패

처리:
- fallback 응답 생성
- interaction_logs 저장

error_type:
- LLM_CALL_FAILED

## 13.6 Response Validation 실패

처리:
- fallback 응답 전환
- success 저장 금지
- interaction_logs 저장

error_type:
- RESPONSE_VALIDATION_FAILED

## 13.7 Provenance Validation 실패

처리:
- fallback 응답 전환
- success 저장 금지
- interaction_logs 저장

error_type:
- PROVENANCE_VALIDATION_FAILED

---

# 14. 구현 금지 규칙

데이터:
- 존재하지 않는 데이터 생성 금지
- ML Output 수정 금지
- KAG_STATE 수정 금지
- RAG_STATE 수정 금지
- RAG_STATE에 없는 추천 생성 금지

LLM:
- 정책 결정 금지
- 추천 후보 생성 금지
- 계산 수행 금지
- 내부 코드명 고객 노출 금지
- 근거 없는 추천 설명 금지

UI:
- UI에서 Service 우회 금지
- UI에서 SQL 실행 금지
- UI에서 추천 생성 금지
- UI에서 KAG/RAG/ML 원본 수정 금지

구현:
- 하드코딩 금지
- 전역 변수 금지
- SQL 쿼리 상수화 필수
- API Key 하드코딩 금지
- 모델명 하드코딩 금지
- 반복되는 경로 문자열 상수화 권장
- 5줄 이상 반복되는 import/path 구성은 상수화 또는 모듈화 권장

---

# 15. 테스트 기준

## 테스트 01: 기존 개인화 추천

조건:
- user_001의 preferred_genres = ["rnb", "indie"]
- recommendation_goal.primary_goal = personalized_recommendation

검증:
- personalized_match 추천 카드가 표시된다.
- 추천 곡은 RAG_STATE에 존재한다.
- 고객 UI에 내부 전략명은 노출되지 않는다.

## 테스트 02: 최신 업데이트 음악 추천

조건:
- user_input = "새로 나온 노래 추천해줘"
- recommendation_category = new_release

검증:
- New Release Section이 표시된다.
- release_type = new_release인 곡만 최신곡 카드에 표시된다.
- RAG_STATE에 없는 최신곡은 표시되지 않는다.

## 테스트 03: 새로운 취향 탐색 추천

조건:
- user_input = "내 취향이랑 다른 것도 추천해줘"
- recommendation_category = discovery_candidate

검증:
- Discovery Section이 표시된다.
- 기존 취향과 연결되는 설명이 포함된다.
- 너무 단정적인 취향 확장 문구를 사용하지 않는다.

## 테스트 04: 추천 이유 질문

조건:
- user_input = "이 노래 왜 추천했어?"

검증:
- Response Generator가 recommendation_reason 또는 evidence_summary 기반으로 설명한다.
- RAG_STATE에 없는 이유를 생성하지 않는다.

## 테스트 05: 음악 정보 질문

조건:
- user_input = "dream pop이 뭐야?"

검증:
- information_evidence 기반으로 설명한다.
- 근거가 없으면 fallback 또는 제한적 설명으로 전환한다.

## 테스트 06: ML Output 없음

검증:
- KAG/RAG/LLM 실행 안 함
- fallback 메시지 표시
- error_type = ML_OUTPUT_NOT_FOUND 저장

## 테스트 07: RAG에 없는 곡 생성 방지

조건:
- LLM 응답에 RAG_STATE에 없는 content_id가 포함됨

검증:
- Provenance Validation 실패
- fallback 응답 전환
- success 저장 금지

---

# 16. 완료 기준

기능 완료:
- Main Recommendation Page 정상 출력
- Chatbot Page 정상 출력
- 기존 개인화 추천 정상 표시
- 최신곡 추천 정상 표시
- 새 취향 탐색 추천 정상 표시
- 음악 정보 질문 응답 가능
- 추천 이유 설명 가능

계약 완료:
- ML Output Schema 정의 완료
- KAG_STATE Schema 정의 완료
- RAG_STATE Schema 정의 완료
- RESPONSE_STATE Schema 정의 완료
- interaction_logs Schema 정의 완료

검증 완료:
- Contract Validation 동작
- Response Validation 동작
- Provenance Validation 동작
- fallback 동작
- RAG_STATE에 없는 추천 생성 방지

저장 완료:
- PostgreSQL interaction_logs 저장
- success/fallback/error 로그 저장
- latency 저장
- validation_result 저장

UI 완료:
- 고객 UI 내부 지표 미노출
- Developer Debug Panel 분리
- 추천 카드 UI 적용
- DJ 캐릭터 영역 표시
- Chatbot Page 분리

확장 완료:
- MockKagAdapter → RealKagAdapter 교체 가능
- MockRagAdapter → RealRagAdapter 교체 가능
- Agent 구조 확장 가능
- UI Section 추가 가능

---

# 17. 최종 설계 요약

RIMAS v2는 기존 개인화 추천을 버리지 않는다.

기존 사용자 취향 기반 추천을 기본 축으로 유지하고,
그 위에 최신 업데이트 음악 추천, 새로운 취향 탐색 추천,
음악 정보 설명, 큐레이터형 응답을 확장한다.

KAG는 사용자 기반 추천 방향과 큐레이션 경로를 결정한다.
RAG는 추천 후보와 설명 근거를 제공한다.
LLM은 추천 후보를 만들지 않고, RAG와 KAG 근거를 바탕으로 자연어 설명만 생성한다.
UI는 추천을 매력적으로 보여주되, 내부 판단 지표는 고객에게 노출하지 않는다.

따라서 본 설계의 핵심은 다음 한 문장으로 정의된다.

"사용자 기반 개인화 추천을 중심으로, DJ 큐레이터가 최신 음악과 새로운 취향을 안전하게 확장해주는 음악 추천 시스템"
