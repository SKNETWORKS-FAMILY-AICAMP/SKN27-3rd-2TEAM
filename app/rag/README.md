# RAG 기능정의서

## 1. 목적

RAG는 KAG_STATE가 결정한 추천 방향에 맞춰 추천 후보, 추천 근거, 음악 정보 설명 근거를 제공하는 계층이다.
RAG_STATE는 UI 표시, Recommendation Agent 선택, Response Generator 응답, Provenance Validation의 기준으로 사용된다.

본 문서는 `docs/Design.md`, `docs/Service Flow 설계.md`, `docs/Agent Prompt 상세 설계.md`, `docs/JSON Schema  Pydantic Schem.md`, `docs/Chatbot LLM 구현 범위.md`에 정의된 RAG 책임과 제한 사항을 기준으로 한다.

## 2. 책임 범위

RAG는 다음 책임을 가진다.

- 추천 후보 제공
- 추천 근거 제공
- 음악 정보 설명 근거 제공
- LLM 응답의 provenance 기준 제공
- 기존 유저 기반 추천 후보 제공
- 신규 업데이트 추천 후보 제공
- 새 취향 탐색 후보 제공
- 곡, 아티스트, 장르, 분위기 등 음악 정보 근거 제공

RAG는 KAG가 결정한 추천 방향을 실행 가능한 후보와 evidence로 변환한다.

## 3. 입력

RAG Adapter의 현재 인터페이스는 다음 입력을 받는다.

```python
build_state(kag_state)
```

입력 의미는 다음과 같다.

- `kag_state`: 추천 목표, 큐레이션 전략, 콘텐츠 요구사항, 라우팅 정보를 포함한 KAG_STATE

## 4. 출력

RAG는 RAG_STATE를 반환한다.
RAG_STATE는 문서상 다음 정보를 포함한다.

- `status`
- `recommendation_context`
- `recommended_content_evidence`
- `recommendation_reason`
- `information_evidence`
- `recommendation_scripts`

`recommended_content_evidence`의 `content_id`, `title`, `artist`, `genre`, `recommendation_category`, `evidence_summary`는 이후 추천 카드와 응답 검증의 기준이 된다.

## 5. 다른 계층과의 관계

Service Layer는 KAG_STATE 생성 후 RAG Adapter를 호출하고 RAG_STATE를 수신한다.
Recommendation Agent는 RAG_STATE의 `recommended_content_evidence` 안에서만 UI와 응답에 사용할 후보를 선택한다.
Response Generator는 RAG_STATE와 selected recommendations를 기반으로 자연어 응답을 생성한다.
Provenance Validator는 응답의 `used_content_ids`, title, artist, display reason이 RAG_STATE 근거와 일치하는지 검증한다.
UI는 Service Layer가 만든 View Model만 표시하며 RAG_STATE 원본을 고객 화면에 노출하지 않는다.

MockRagAdapter와 RealRagAdapter는 동일한 인터페이스를 유지해야 한다.
구현체 교체 시 Service Layer 코드는 변경되지 않아야 한다.

## 6. 제한 사항

RAG는 다음을 하지 않는다.

- 사용자 전략 결정
- UI 라우팅 결정
- KAG_STATE 수정
- ML Output 수정
- 최종 자연어 응답 생성
- 존재하지 않는 음악 후보 생성
- RAG_STATE에 없는 content_id, title, artist, genre 임의 생성
- JSON 계약 임의 변경
- UI 렌더링
- 고객 응답에 raw JSON 또는 내부 판단 지표 노출

RAG_STATE가 실패하거나 계약 검증에 실패하면 LLM 실행은 차단되고 fallback 흐름으로 전환되어야 한다.

## 7. 검증 기준

RAG 결과는 Contract Validator 검증을 통과해야 한다.
ResponseState의 `used_content_ids`는 RAG_STATE의 `recommended_content_evidence.content_id` 안에 있어야 한다.
`display_recommendations.title`과 `display_recommendations.artist`는 RAG_STATE 값과 일치해야 한다.
RAG_STATE에 없는 추천이나 근거 없는 설명이 생성되면 Provenance Validation 실패 대상이다.
RAG_STATE는 ML Output, KAG_STATE와 함께 interaction log에 저장될 수 있다.

## 8. 참고 문서

- `docs/Design.md`
- `docs/Service Flow 설계.md`
- `docs/Agent Prompt 상세 설계.md`
- `docs/JSON Schema  Pydantic Schem.md`
- `docs/Chatbot LLM 구현 범위.md`
