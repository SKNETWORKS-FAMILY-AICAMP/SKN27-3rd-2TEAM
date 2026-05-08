# RIMAS Service Flow 설계 v1
# 방안 02: Page별 Service 분리

---

# 1. 전체 구조

Service는 2개로 분리한다.

1. MainRecommendationService
2. ChatbotService

공통 내부 모듈:
- app.common.constants
- app.common.default_state
- app.common.labels
- MlOutputRepository
- KagAdapter
- RagAdapter
- ContractValidator
- LlmFlowService
- ResponseValidator
- ProvenanceValidator
- InteractionLogRepository

공통 모듈 사용 규칙:
- Service, Validator, Agent가 공유하는 계약 상수와 기본 state는 app.common을 통해 참조한다.
- SQL 쿼리는 Repository Layer의 query_constants.py를 유지한다.
- UI theme 값은 UI Layer의 styles/theme.py를 유지한다.

---

# 2. MainRecommendationService

## 2.1 역할

- 사용자 진입 시 추천 카드 생성
- 개인화 추천 + 신규곡 + 새 취향 구성
- LLM 호출 없이 UI ViewModel 생성 가능 (핵심 포인트)

---

## 2.2 함수 시그니처

def get_main_recommendation(user_id: str) -> dict

---

## 2.3 전체 흐름

STEP 1. ML Output 조회
STEP 2. ML Output Validation
STEP 3. KAG_STATE 생성
STEP 4. KAG_STATE Validation
STEP 5. RAG_STATE 생성
STEP 6. RAG_STATE Validation
STEP 7. ViewModel 생성
STEP 8. interaction_logs 저장
STEP 9. UI 반환

---

## 2.4 상세 흐름

### STEP 1. ML Output 조회

ml_output = ml_repository.get_latest_by_user_id(user_id)

예외:
- 없으면 fallback

---

### STEP 2. ML Output Validation

if ml_output is None:
    return fallback_response("ML_OUTPUT_NOT_FOUND")

---

### STEP 3. KAG_STATE 생성

kag_state = kag_adapter.get_kag_state(
    user_id=user_id,
    ml_output=ml_output,
    user_input=None
)

---

### STEP 4. Contract Validation

contract_validator.validate_kag(kag_state)

실패 시:
- fallback
- 로그 저장

---

### STEP 5. RAG_STATE 생성

rag_state = rag_adapter.get_rag_state(
    kag_state=kag_state
)

---

### STEP 6. Contract Validation

contract_validator.validate_rag(rag_state)

실패 시:
- fallback

---

### STEP 7. ViewModel 생성

view_model = {
    "personalized": [],
    "new_release": [],
    "discovery": []
}

for item in rag_state.recommended_content_evidence:
    if item.recommendation_category == "personalized_match":
        view_model["personalized"].append(item)
    elif item.recommendation_category == "new_release":
        view_model["new_release"].append(item)
    elif item.recommendation_category == "discovery_candidate":
        view_model["discovery"].append(item)

---

### STEP 8. interaction_logs 저장

interaction_log_repository.save({
    "user_id": user_id,
    "page_type": "main_recommendation_page",
    "status": "success",
    "ml_output_json": ml_output,
    "kag_state_json": kag_state,
    "rag_state_json": rag_state,
    "response_state_json": None
})

---

### STEP 9. 반환

return view_model

---

# 3. ChatbotService

## 3.1 역할

- 사용자 질문 처리
- LLM 기반 큐레이터 응답 생성
- 추천 이유 / 정보 설명 처리

---

## 3.2 함수 시그니처

def get_chatbot_response(user_id: str, user_input: str) -> dict

---

## 3.3 전체 흐름

STEP 1. ML Output 조회
STEP 2. KAG_STATE 생성
STEP 3. RAG_STATE 생성
STEP 4. Contract Validation
STEP 5. LLM Flow 실행
STEP 6. Response Validation
STEP 7. Provenance Validation
STEP 8. interaction_logs 저장
STEP 9. 응답 반환

---

## 3.4 상세 흐름

### STEP 1. ML Output 조회

ml_output = ml_repository.get_latest_by_user_id(user_id)

없으면:
- fallback

---

### STEP 2. KAG_STATE 생성

kag_state = kag_adapter.get_kag_state(
    user_id=user_id,
    ml_output=ml_output,
    user_input=user_input
)

---

### STEP 3. RAG_STATE 생성

rag_state = rag_adapter.get_rag_state(
    kag_state=kag_state
)

---

### STEP 4. Contract Validation

contract_validator.validate_kag(kag_state)
contract_validator.validate_rag(rag_state)

실패 시:
- fallback

---

### STEP 5. LLM Flow 실행

response_state = llm_flow_service.run(
    user_input=user_input,
    ml_output=ml_output,
    kag_state=kag_state,
    rag_state=rag_state
)

---

# 4. LlmFlowService

## 4.1 함수 시그니처

def run(user_input, ml_output, kag_state, rag_state) -> dict

---

## 4.2 내부 흐름

STEP 1. Intent Agent
STEP 2. Curation Agent
STEP 3. Recommendation Agent
STEP 4. Response Generator

---

### STEP 1. Intent Agent

intent_result = intent_agent.run(user_input)

---

### STEP 2. Curation Agent

curation_plan = curation_agent.run(
    intent_result=intent_result,
    kag_state=kag_state,
    rag_state=rag_state
)

---

### STEP 3. Recommendation Agent

selected_recommendations = recommendation_agent.run(
    curation_plan=curation_plan,
    rag_state=rag_state
)

---

### STEP 4. Response Generator

response_state = response_generator.run(
    user_input=user_input,
    ml_output=ml_output,
    kag_state=kag_state,
    rag_state=rag_state,
    curation_plan=curation_plan,
    selected_recommendations=selected_recommendations
)

return response_state

---

# 5. ChatbotService (계속)

### STEP 6. Response Validation

response_validator.validate(response_state)

실패 시:
- fallback

---

### STEP 7. Provenance Validation

provenance_validator.validate(
    response_state=response_state,
    rag_state=rag_state
)

실패 시:
- fallback

---

### STEP 8. interaction_logs 저장

interaction_log_repository.save({
    "user_id": user_id,
    "user_input": user_input,
    "page_type": "chatbot_page",
    "status": response_state.status,
    "response_type": response_state.response_type,
    "ml_output_json": ml_output,
    "kag_state_json": kag_state,
    "rag_state_json": rag_state,
    "response_state_json": response_state
})

---

### STEP 9. 반환

return response_state

---

# 6. Fallback 처리 규칙

def fallback_response(error_type: str) -> dict:

    return {
        "status": "error",
        "response_type": "fallback",
        "chatbot_response": "지금은 추천을 준비하는 데 문제가 있어서 기본 안내만 제공할게요.",
        "display_recommendations": [],
        "used_content_ids": []
    }

---

# 7. 핵심 구현 포인트

1. Main Page는 LLM 없이도 동작해야 한다
2. Chatbot만 LLM 사용
3. Validation 실패 시 LLM 실행 금지
4. RAG 기반 추천만 허용
5. 모든 흐름은 Service Layer에서만 제어

---

# 8. 구현 우선순위

1순위:
- MainRecommendationService
- ChatbotService 기본 흐름

2순위:
- LlmFlowService

3순위:
- Validator

4순위:
- Repository 연결

---

# 9. 완료 기준

- Main 페이지 추천 정상 출력
- Chatbot 응답 정상 생성
- fallback 정상 동작
- Validation 실패 시 차단
- DB 저장 정상
