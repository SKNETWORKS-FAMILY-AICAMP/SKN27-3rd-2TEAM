# RIMAS WBS v2 (1주 압축형)
# 기준: Design.md + JSON Schema + DB + Service Flow + Agent Prompt

---

# 0. 전체 전략

구현 순서 원칙:

1. 계약 먼저 (Schema)
2. 데이터 먼저 (DB + Mock)
3. 흐름 먼저 (Service)
4. 검증 먼저 (Validator)
5. 그 다음 LLM
6. 마지막 UI

절대 금지:
- UI 먼저 만들기
- LLM 먼저 붙이기
- Schema 없이 구현하기

---

# Day 1: 기반 구조 + Schema + DB

## 목표
- 프로젝트 골격 완성
- JSON 계약 고정
- DB 연결 가능 상태

---

## 작업

### 1. 폴더 구조 생성

/app
/services
/adapters
/agents
/validators
/repositories
/schemas
/contracts
/config
/tests

---

### 2. Pydantic Schema 구현

파일:

schemas/
- ml_output_schema.py
- kag_state_schema.py
- rag_state_schema.py
- intent_result_schema.py
- curation_plan_schema.py
- selected_recommendation_schema.py
- response_state_schema.py
- interaction_log_schema.py

---

### 3. DB 연결

- PostgreSQL Docker 실행
- psycopg2 또는 asyncpg 설정
- connection pool 구성

---

### 4. 테이블 생성

- users
- ml_outputs
- music_catalog
- interaction_logs

---

## 산출물

- DB 정상 연결
- Schema import 가능
- 테이블 생성 완료

---

# Day 2: Repository + Mock 데이터

## 목표
- 데이터 조회/저장 가능
- Mock 기반 실행 가능

---

## 작업

### 1. query_constants.py 작성

- SELECT_LATEST_ML_OUTPUT_BY_USER_ID
- INSERT_INTERACTION_LOG
- SELECT_MUSIC_BY_CATEGORY

---

### 2. Repository 구현

- ml_output_repository.py
- music_catalog_repository.py
- interaction_log_repository.py

---

### 3. Seed 데이터 삽입

- users
- ml_outputs
- music_catalog

---

### 4. Repository 테스트

- user_id로 ML 조회
- 카테고리별 음악 조회
- 로그 저장 테스트

---

## 산출물

- Mock 데이터 기반 조회 가능
- 로그 저장 가능

---

# Day 3: Adapter + Validator

## 목표
- KAG / RAG Mock 완성
- Validation 시스템 구축

---

## 작업

### 1. MockKagAdapter 구현

입력:
- user_id
- ml_output
- user_input

출력:
- KagState

---

### 2. MockRagAdapter 구현

입력:
- kag_state

출력:
- RagState

---

### 3. Contract Validator 구현

- validate_ml_output
- validate_kag
- validate_rag

---

### 4. Response Validator 구현

- response 구조 검증

---

### 5. Provenance Validator 구현

- RAG 없는 content_id 차단
- title/artist 일치 검증

---

## 산출물

- KAG/RAG Mock 정상 동작
- Validation 실패 시 차단 가능

---

# Day 4: Service Layer

## 목표
- 전체 흐름 동작

---

## 작업

### 1. MainRecommendationService 구현

- ML 조회
- KAG 호출
- RAG 호출
- ViewModel 생성
- 로그 저장

---

### 2. ChatbotService 구현

- ML 조회
- KAG 호출
- RAG 호출
- LLM Flow 연결 준비

---

### 3. LlmFlowService skeleton

- Intent → Curation → Recommendation → Response

---

### 4. Fallback 로직 구현

---

## 산출물

- LLM 없이도 Main 페이지 동작
- Chatbot 기본 흐름 준비 완료

---

# Day 5: Agent + LLM

## 목표
- 실제 LLM 응답 생성

---

## 작업

### 1. Prompt 상수화

agents/prompts/
- intent_prompt.py
- curation_prompt.py
- recommendation_prompt.py
- response_prompt.py

---

### 2. Agent 구현

- intent_agent.py
- curation_agent.py
- recommendation_agent.py
- response_generator.py

---

### 3. LlmFlowService 연결

- 실제 호출 연결 (OpenAI / Ollama 등)

---

### 4. Validator 연결

- Response Validator
- Provenance Validator

---

## 산출물

- Chatbot 응답 생성 가능
- Validation 적용 완료

---

# Day 6: UI (Streamlit)

## 목표
- 실제 사용자 화면 구현

---

## 작업

### 1. Main Recommendation Page

- personalized section
- new release section
- discovery section

---

### 2. Chatbot Page

- chat input
- response 출력
- 추천 카드 연결

---

### 3. Navigation

- main → chatbot 이동

---

### 4. Developer Debug Panel

- developer_mode=True 시 표시

---

## 산출물

- 전체 UI 동작

---

# Day 7: 통합 테스트 + 안정화

## 목표
- 전체 시스템 검증

---

## 작업

### 1. 통합 테스트

- 추천 정상 출력
- Chatbot 정상 응답

---

### 2. 실패 시나리오 테스트

- ML 없음
- KAG 실패
- RAG 실패
- Validation 실패

---

### 3. 로그 확인

- DB 저장 확인
- latency 확인

---

### 4. 버그 수정

---

## 산출물

- 데모 가능 상태

---

# 8. 실무적 선택지

[방안 01: LLM 최소 사용]
- 특징: Main은 LLM 없음, Chatbot만 사용
- 장점: 안정성 높음
- 단점: 자연어 다양성 제한
- 추천: MVP에 최적

[방안 02: 모든 응답 LLM]
- 특징: Main도 LLM 사용
- 장점: 자연스러움
- 단점: 비용 + 불안정
- 비추천

[방안 03: Hybrid]
- 특징: 일부만 LLM
- 추천: 추후 확장

👉 최종 선택: 방안 01

---

# 9. 완료 기준

1. Main 페이지 추천 정상
2. Chatbot 응답 정상
3. RAG 기반 추천만 출력
4. Validation 실패 시 차단
5. fallback 정상 동작
6. DB 저장 정상
7. UI 정상 출력
8. Mock → Real 전환 가능 구조 유지

---

# 10. 최종 핵심

이 프로젝트의 성공 기준:

"추천을 잘하는 게 아니라, 잘못된 추천을 절대 안 하는 구조"

- Schema로 제한
- Validator로 차단
- RAG로 근거 고정
- LLM은 설명만