# UI Service Integration Design

## 목적

`docs/Design.md`와 `docs/WBS v2.md`의 Day 4~6 범위에 맞춰 Streamlit UI가 Service Layer만 호출하는 실행 가능한 MVP 흐름을 만든다.

## 범위

- Main Recommendation Page 출력
- Chatbot Page 출력
- Main/Chatbot 페이지 이동
- `developer_mode=True`일 때만 Developer Debug Panel 출력
- MainRecommendationService, ChatbotService, ViewModelService의 최소 실행 흐름
- MockKagAdapter, MockRagAdapter, Contract/Response/Provenance Validator의 최소 계약 검증

## 제외 범위

- UI에서 SQL 직접 실행
- UI에서 LLM 직접 호출
- UI에서 ML Output, KAG_STATE, RAG_STATE 원본 수정
- RAG_STATE에 없는 추천 생성
- RealKagAdapter, RealRagAdapter 실제 외부 연동
- 문서에 없는 신규 화면 또는 신규 추천 정책

## 아키텍처

UI는 `app/main.py`에서 Streamlit 앱을 시작하고, `app/pages`의 페이지 렌더 함수를 호출한다. 각 페이지는 `app/ui/components`의 작은 컴포넌트를 조합한다.

Service Layer는 UI가 사용할 View Model을 반환한다. UI는 View Model을 표시만 하며, 데이터 조회와 KAG/RAG/검증 흐름은 Service Layer 아래에서 처리한다.

Mock Adapter는 문서의 JSON 계약과 `app/json_templates`의 형태를 따르는 결정적 데이터를 반환한다. Validator는 필수 필드와 provenance 제약을 확인하고, 실패 시 Service가 fallback View Model을 반환할 수 있게 한다.

## 데이터 흐름

Main Recommendation Page:

```text
Streamlit Page
-> MainRecommendationService.get_page_view_model(user_id)
-> ML Output 조회 또는 template 기반 fallback
-> MockKagAdapter
-> MockRagAdapter
-> Contract Validation
-> ViewModelService
-> UI 출력
```

Chatbot Page:

```text
Streamlit Page
-> ChatbotService.submit_message(user_id, user_input)
-> ML Output 조회 또는 template 기반 fallback
-> MockKagAdapter
-> MockRagAdapter
-> Response State 생성
-> Response/Provenance Validation
-> ViewModelService
-> UI 출력
```

## UI 구성

Main Recommendation Page는 문서의 구성만 포함한다.

- Top Taste Header
- Character DJ Banner
- Personalized Recommendation Section
- New Release Section
- Discovery Section
- Personalized Guide Section
- Chatbot Page 이동 버튼
- Developer Debug Panel

Chatbot Page는 문서의 구성만 포함한다.

- Chat Header
- Chat History
- User Input
- Curator Response Area
- Related Recommendation Cards
- Developer Debug Panel

## 오류 처리

ML Output이 없거나 KAG/RAG/Validation이 실패하면 Service Layer가 fallback 상태를 만든다. UI는 실패 원인을 고객 화면에 내부 코드명으로 노출하지 않는다. `developer_mode=True`인 경우에만 debug panel에 내부 상태를 표시한다.

## 테스트

- Service 테스트는 UI 없이 View Model 형태와 fallback 동작을 검증한다.
- Adapter 테스트는 문서 필수 필드와 추천 카테고리를 검증한다.
- Validator 테스트는 RAG에 없는 추천이 차단되는지 검증한다.
- UI 컴포넌트 테스트는 Streamlit 직접 실행 대신 렌더러 인터페이스를 주입해 호출 계약을 검증한다.
