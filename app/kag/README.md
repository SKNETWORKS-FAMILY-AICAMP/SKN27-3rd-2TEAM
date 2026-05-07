# KAG 기능정의서

## 1. 목적

KAG는 사용자 상태, 사용자 입력, ML Output을 기반으로 추천 방향과 큐레이션 경로를 결정하는 계층이다.
KAG_STATE는 이후 RAG, Agent, LLM Flow가 참고하는 의사결정 기준으로 사용된다.

본 문서는 `docs/Design.md`, `docs/Service Flow 설계.md`, `docs/Agent Prompt 상세 설계.md`, `docs/JSON Schema  Pydantic Schem.md`, `docs/Chatbot LLM 구현 범위.md`에 정의된 KAG 책임과 제한 사항을 기준으로 한다.

## 2. 책임 범위

KAG는 다음 책임을 가진다.

- 사용자 기반 추천 방향 결정
- 기존 개인화 추천, 최신곡 추천, 새 취향 탐색, 추천 이유 질문, 음악 정보 질문 등의 응답 방향 구분
- 큐레이션 의도와 전략 결정
- 콘텐츠 요구사항 정의
- UI 라우팅 기준 제공
- RAG가 사용할 추천 목표와 콘텐츠 요구조건 제공

KAG는 추천 결과 자체가 아니라 추천을 어떤 방향으로 구성할지 결정한다.

## 3. 입력

KAG Adapter의 현재 인터페이스는 다음 입력을 받는다.

```python
build_state(user_id, user_input, ml_output)
```

입력 의미는 다음과 같다.

- `user_id`: 추천 대상 사용자 식별자
- `user_input`: 챗봇 또는 페이지 흐름에서 전달되는 사용자 입력
- `ml_output`: 사용자 취향, 행동, 추천 프로필을 포함한 ML Output

## 4. 출력

KAG는 KAG_STATE를 반환한다.
KAG_STATE는 문서상 다음 정보를 포함한다.

- `status`
- `user`
- `recommendation_goal`
- `user_context`
- `curation_intent`
- `curation_strategy`
- `content_requirements`
- `routing`
- `selected_path`

KAG_STATE 구조는 JSON 계약과 Contract Validator 검증 대상이다.

## 5. 다른 계층과의 관계

Service Layer는 KAG Adapter를 호출하고 KAG_STATE를 수신한다.
RAG는 KAG_STATE가 결정한 방향을 기반으로 추천 후보와 설명 근거를 제공한다.
Agent와 LLM Flow는 KAG_STATE를 참고하되, KAG_STATE를 임의로 변경하지 않는다.
UI는 Service Layer가 만든 View Model만 표시하며 KAG_STATE 원본을 고객 화면에 노출하지 않는다.

MockKagAdapter와 RealKagAdapter는 동일한 인터페이스를 유지해야 한다.
구현체 교체 시 Service Layer 코드는 변경되지 않아야 한다.

## 6. 제한 사항

KAG는 다음을 하지 않는다.

- 실제 음악 후보 생성
- 추천 이유 문장 생성
- 최종 자연어 응답 생성
- RAG_STATE 수정
- ML Output 수정
- UI 렌더링
- LLM 역할 수행
- JSON 계약 임의 변경
- 고객 응답에 내부 전략명, `selected_path`, raw JSON 노출

KAG_STATE가 실패하거나 계약 검증에 실패하면 RAG와 LLM 실행은 차단되고 fallback 흐름으로 전환되어야 한다.

## 7. 검증 기준

KAG 결과는 Contract Validator 검증을 통과해야 한다.
KAG_STATE에 없는 route, strategy, action을 Agent나 LLM이 사용하는 경우 Provenance Validation 실패 대상이다.
KAG_STATE는 ML Output, RAG_STATE와 함께 interaction log에 저장될 수 있다.

## 8. 참고 문서

- `docs/Design.md`
- `docs/Service Flow 설계.md`
- `docs/Agent Prompt 상세 설계.md`
- `docs/JSON Schema  Pydantic Schem.md`
- `docs/Chatbot LLM 구현 범위.md`
