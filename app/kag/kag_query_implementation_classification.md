# KAG Query 구현 분류 (Tool 기반 재정의)

## 문서 목적
- 기존 `app/kag/querys.py` 실행 함수 제약을 기준으로 분류하지 않고,
- **신규 쿼리 호출 함수(= Tool 함수) 구축**을 전제로 재분류한다.
- 외부 Agent가 Tool 함수를 호출해 쿼리를 실행하는 구조를 기준으로 한다.

## 고정 원칙
- 쿼리 문자열과 파라미터 템플릿은 `constant`에서 관리한다.
- Tool 함수는 `constant`에서 템플릿을 조회해 바인딩 후 실행한다.
- 즉, 실행 로직과 쿼리 템플릿 정의를 분리하는 구조는 유지한다.
- 시나리오 태그(날씨·감정·상황 등)는 Neo4j `Label*` 노드 `name`과 맞는 **영문 저장 토큰**을 쓴다. 한글 발화는 `constant.resolve_scenario_param`과 `KAG_SCENARIO_ALIAS_KO_TO_KEY`로 치환한다. 감정 매칭은 `HAS_LABEL_EMOTION` / `LabelEmotion`이다.

---

## 1) 목표 아키텍처 (요약)

- `constant`:
  - query_key별 Cypher 템플릿
  - query_key별 파라미터 템플릿/검증 규칙
- `tool 함수 레이어`:
  - 입력 정규화
  - `constant` 템플릿 조회
  - 파라미터 바인딩
  - Neo4j 실행
  - 공통 응답 포맷 반환
- `외부 Agent`:
  - intent/query_type 결정
  - 해당 Tool 함수 호출
  - 결과를 응답/후속 흐름에 연결

---

## 2) Query Type 재분류 (신규 Tool 구축 기준)

### A. 1차 구축 대상 (MVP 우선)
- `Q_SEARCH_001 / MUSIC_BASIC_INFO_LOOKUP`
- `Q_SEARCH_003 / MUSIC_CONDITION_SEARCH`
- `Q_SEARCH_009 / ARTIST_MUSIC_LOOKUP`
- `Q_SEARCH_011 / TEMPORAL_MUSIC_LOOKUP`
- `Q_REC_001 / GENRE_BASED_RECOMMENDATION`
- `Q_REC_002 / MOOD_BASED_RECOMMENDATION`
- `Q_REC_003 / SITUATION_BASED_RECOMMENDATION`
- `Q_REC_004 / WEATHER_BASED_RECOMMENDATION`
- `Q_REC_006 / POPULARITY_BASED_RECOMMENDATION`
- `Q_REC_008 / HYBRID_CONTEXT_RECOMMENDATION`

선정 이유:
- 단일/복합 필터형 조회가 중심이라 템플릿화와 파라미터 검증 구조에 적합
- `music_catalog.csv`, `music_catalog_scenarios.csv` 기반 데이터 활용도가 높음

### B. 2차 구축 대상 (그래프 관계 확장)
- `Q_SEARCH_002 / MUSIC_RELATION_INFO_LOOKUP`
- `Q_SEARCH_004 / SIMILAR_MUSIC_LOOKUP`
- `Q_SEARCH_006 / CONNECTED_NODE_MUSIC_LOOKUP`
- `Q_SEARCH_007 / MUSIC_COMMON_FEATURE_LOOKUP`
- `Q_SEARCH_014 / RELATION_TYPE_LOOKUP`
- `Q_REC_005 / SIMILAR_SONG_RECOMMENDATION`

선정 이유:
- 관계/패턴 탐색 쿼리로서 성능 튜닝, 제한 조건, 결과 후처리 정책이 필요

### C. 3차 구축 대상 (집계/경로/운영성 고려)
- `Q_SEARCH_005 / MUSIC_STAT_LOOKUP`
- `Q_SEARCH_008 / MUSIC_PATH_LOOKUP`
- `Q_SEARCH_010 / CATEGORY_TOP_MUSIC_LOOKUP`
- `Q_SEARCH_012 / COMPOSITE_CONDITION_SEARCH`
- `Q_SEARCH_013 / HIGH_CONNECTION_MUSIC_LOOKUP`
- `Q_REC_007 / DIVERSITY_RECOMMENDATION`

선정 이유:
- 경로 탐색/집계/다양성 제어는 쿼리 비용과 응답 정책을 함께 설계해야 안정적 운영 가능

---

## 3) Tool 함수 표준 규격 (권장)

- 함수명: `tool_<query_type_snake_case>`
- 입력:
  - `query_context`: 사용자 질의에서 추출된 파라미터
  - `constraints`: limit, depth, filter 옵션
- 내부 처리:
  - `constant`에서 `query_key` 템플릿 조회
  - 파라미터 기본값 적용 + 타입 정규화
  - 필수 파라미터 검증
  - Neo4j 실행
- 출력:
  - `query_type`
  - `result_count`
  - `items`
  - `debug.query_key` (운영 추적용)

---

## 4) 소작업 단위 제안

- 1단계: `constant`에 query_key/파라미터 템플릿 스키마 정의
- 2단계: 1차 구축 대상 Query Type의 Tool 함수 구현
- 3단계: 외부 Agent가 query_type별 Tool 함수를 호출하도록 라우팅 연결
- 4단계: 2차/3차 대상 순차 확대 + 성능/결과 품질 튜닝

---

## 5) 결정 사항 요약

- 기존 `querys.py` 함수 재사용은 필수가 아니다.
- 신규 Tool 함수 세트를 기준으로 재구축한다.
- 단, **`constant`에서 쿼리/파라미터 템플릿을 받아오는 방식은 유지**한다.

