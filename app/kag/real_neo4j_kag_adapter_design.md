# Real Neo4j KAG Adapter 설계서

## 1. 목적

FastAPI 런타임에서 Mock KAG 대신 실제 Neo4j 기반 KAG Query Tool을 호출해 `KAG_STATE`를 생성한다.

이번 설계는 사용자가 제공한 결정사항을 반영한다.

- Neo4j/KAG 스키마는 `neo4j/` 폴더에 구현된 현재 구조를 기준으로 정렬한다.
- 루트 `Dockerfile`과 루트 `docker-compose.yml`을 실행 기준으로 유지한다.
- `neo4j/docker-compose.yml`은 런타임 기준에서 제외하고, 삭제 또는 정리 대상 후보로 둔다.
- Real KAG 연결을 위해 `app/agents` 등 일부 추가 수정은 가능하지만, 수정 전 사용자 확인을 받는다.
- LLM은 KAG 결과를 생성하지 않는다. KAG 결과는 Neo4j/데이터 기반 deterministic 로직으로만 생성한다.

## 2. 확정된 기준

### 2.1 그래프 스키마 기준

설계서 원문의 `Track/User/Situation/Emotion` 중심 스키마보다 현재 `neo4j/` 폴더의 구현 스키마를 우선한다.

현재 기준 중심 노드:

- `MusicCatalog`
- `Genre`
- `SubGenre` 또는 `PlaylistSubGenre`
- `Artist`
- `Mood`
- `ReleaseYear`
- `DimWeather`
- `DimSeason`
- `DimEmotion`
- `DimTimeOfDay`
- `DimEnergyLevel`
- `DimCtx*`

중심 곡 노드는 `Track`이 아니라 `MusicCatalog`로 둔다.

### 2.2 관계 스키마 기준

관계명도 `neo4j/` 폴더의 적재 코드와 실제 생성 관계를 기준으로 맞춘다.

현재 확인된 핵심 관계:

- `HAS_GENRE`
- `HAS_SUBGENRE` 또는 `HAS_PLAYLIST_SUBGENRE`
- `PERFORMED_BY`
- `HAS_MOOD`
- `HAS_TEMPO`
- `RELEASED_IN`
- `HAS_DIM_WEATHER`
- `HAS_DIM_SEASON`
- `HAS_DIM_EMOTION`
- `HAS_DIM_TIME_OF_DAY`
- `HAS_DIM_ENERGY_LEVEL`
- `HAS_DIM_CTX_*`

`app/kag/constant.py`의 `HAS_PLAYLIST_SUBGENRE`와 `neo4j/common/querys.py`의 `HAS_SUBGENRE` 불일치는 구현 계획에서 반드시 정리한다. 정리 방향은 실제 적재 결과와 런타임 쿼리가 같은 관계명을 보도록 맞추는 것이다.

### 2.3 `content_id` 기준

현재 KAG 쿼리 결과의 `track_id`를 KAG/RAG 공통 `content_id`로 사용한다.

따라서 `RealKagAdapter`는 Neo4j row의 `track_id`를 다음 필드에 매핑한다.

- `recommended_content_ids[]`
- `candidate_tracks[].content_id`

별도 content id 매핑 계층은 이번 범위에서 만들지 않는다.

## 3. 수정 범위와 승인 규칙

### 3.1 즉시 수정 가능한 범위

아래 파일은 KAG 연결 구현의 주 작업 범위다.

- `app/kag/connection.py`
- `app/kag/querys.py`
- `app/kag/constant.py`
- `app/kag/adapters/real_kag_adapter.py`
- `app/kag/adapters/__init__.py`
- `app/kag/real_neo4j_kag_adapter_design.md`
- `app/kag/real_neo4j_kag_adapter_smoke.py`

### 3.2 사용자 확인 후 수정 가능한 범위

아래 수정은 설계상 필요하지만, 작업 전에 사용자 확인을 받는다.

- `app/agents/kag_dispatch_agent.py`
  - Real Adapter 선택 경로 추가
  - `KAG_INPUT_JSON` 검증 추가
  - Adapter Router 성격의 분기 추가
- 루트 `docker-compose.yml`
  - Neo4j 적재용 one-shot loader 서비스 추가 여부
  - Neo4j 관련 볼륨/마운트 정리
- 루트 `Dockerfile`
  - 백엔드 런타임 의존성 조정이 필요한 경우
- `neo4j/**`
  - `neo4j/docker-compose.yml` 삭제
  - 런타임과 중복되는 연결 코드 삭제
  - 적재 스크립트 이동 또는 정리
- `docs/**`
  - 현재 구현 기준을 공식 설계서에 반영하는 경우
- `tests/**`
  - 자동화 테스트 추가가 필요한 경우

### 3.3 destructive 작업 규칙

파일 삭제, 폴더 이동, 볼륨 삭제, 데이터 초기화는 모두 별도 확인 후 진행한다.

특히 `neo4j/data/*.csv`는 적재 원천 데이터일 수 있으므로 삭제 대상이 아니다. 삭제 후보는 우선 `neo4j/docker-compose.yml`처럼 루트 compose와 충돌하는 실행 구성 파일로 한정한다.

## 4. 현재 문제 판단

### 4.1 Neo4j 컨테이너는 정상이나 데이터가 비어 있음

루트 compose의 Neo4j 컨테이너는 healthy 상태이고 Bolt 연결도 가능하다.

하지만 실제 조회 결과는 비어 있다.

```cypher
MATCH (n) RETURN labels(n), count(*);
MATCH ()-[r]->() RETURN type(r), count(*);
```

현재 상태에서는 RealKagAdapter가 연결되어도 추천 후보를 만들 수 없다. 데이터 적재 전략이 선행되어야 한다.

### 4.2 앱 연결 설정 불일치

루트 compose는 다음 환경변수를 제공한다.

- `RIMAS_NEO4J_URI`
- `RIMAS_NEO4J_USER`
- `RIMAS_NEO4J_PASSWORD`

현재 `app/kag/connection.py`는 다음 환경변수를 읽는다.

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

백엔드 컨테이너에서 실제 연결하려면 `app/kag/connection.py`가 `RIMAS_NEO4J_*`를 우선 읽어야 한다.

### 4.3 Neo4j 연결 모듈 책임 오염

`app/kag/connection.py`는 Neo4j 연결 모듈인데 `psycopg`를 import한다.

이 import는 Neo4j 연결 책임과 무관하므로 제거한다. PostgreSQL 의존성은 KAG Neo4j 연결 모듈에 두지 않는다.

### 4.4 RealKagAdapter 미완성

현재 `RealKagAdapter.build_state()`는 `user_id` 검증만 수행하고 Neo4j 쿼리 실행, 결과 매핑, `KAG_STATE` 반환을 하지 않는다.

구현 목표는 `KagQueryTools`와 `Neo4j_Connection`을 사용해 `KAG_STATE`를 반환하는 것이다.

### 4.5 기본 런타임은 MockKagAdapter

현재 `KagDispatchAgent` 기본값은 `MockKagAdapter`다.

실제 Neo4j 연결을 사용하려면 Real Adapter 선택 경로가 필요하다. 이 수정은 `app/agents/kag_dispatch_agent.py`에 걸리므로 사용자 확인 후 진행한다.

### 4.6 KAG_INPUT_JSON 검증 미흡

설계서상 KAG Dispatch Agent는 `KAG_INPUT_JSON` 검증 후 Adapter Router를 실행해야 한다.

현재는 `kag_input_json.query_context.normalized_query`만 일부 사용한다. `KagInputSchema` 검증 추가는 `app/agents` 수정에 해당하므로 사용자 확인 후 진행한다.

## 5. 목표 아키텍처

최종 목표 흐름은 다음과 같다.

```text
InputPlannerAgent
  -> KAG_INPUT_JSON
  -> KagDispatchAgent
    -> KAG_INPUT_JSON 검증
    -> Adapter 선택
      -> MockKagAdapter 또는 RealKagAdapter
        -> Neo4j_Connection
        -> KagQueryTools
        -> KAG_STATE
```

`RealKagAdapter`는 다음 책임만 가진다.

1. 입력값 검증
2. `user_input`, `session_context`, 추후 전달될 `KAG_INPUT_JSON`에서 쿼리 조건 추출
3. deterministic 쿼리 선택
4. `KagQueryTools` 실행
5. Neo4j row를 `KAG_STATE`로 매핑

LLM 호출은 하지 않는다.

## 6. Adapter 쿼리 선택 규칙

LLM 기반 Tool 자동 선택기는 이번 범위에 포함하지 않는다.

1차 구현은 deterministic 규칙을 사용한다.

우선순위:

1. 복수 조건이 있으면 `tool_q_rec_008_hybrid_context_recommendation`
2. `genre`가 있으면 `tool_q_rec_001_genre_based_recommendation`
3. `mood`가 있으면 `tool_q_rec_002_mood_based_recommendation`
4. `situation`이 있으면 `tool_q_rec_003_situation_based_recommendation`
5. `weather`가 있으면 `tool_q_rec_004_weather_based_recommendation`
6. 조건이 없으면 `tool_q_rec_006_popularity_based_recommendation`

조건 추출 소스:

- `session_context.recent_moods`
- `session_context.preferred_genres`
- `user_input`의 단순 키워드
- 추후 `KAG_INPUT_JSON.query_context.genre_candidates`
- 추후 `KAG_INPUT_JSON.query_context.mood_candidates`
- 추후 `KAG_INPUT_JSON.query_context.situation_candidates`

`KAG_INPUT_JSON` 전체 전달은 `KagDispatchAgent` 수정이 필요하므로 별도 승인 후 확장한다.

## 7. KAG_STATE 매핑

`RealKagAdapter` 반환값은 기존 `KagStateSchema`와 호환되어야 한다.

필수 구조:

```python
{
    "status": "success",
    "recommendation_goal": {"primary_goal": "..."},
    "recommended_content_ids": [...],
    "recommendation_category": "...",
    "route": "...",
    "target_section": "...",
    "traversal_reason": "...",
    "matched_nodes": [...],
    "excluded_nodes": [],
    "candidate_tracks": [...],
    "diversity_metadata": {...},
}
```

Neo4j row 변환 규칙:

- `track_id`를 `content_id`로 사용한다.
- `recommended_content_ids`에는 중복 제거된 `track_id`를 순서대로 넣는다.
- `candidate_tracks[].content_id`에도 같은 값을 넣는다.
- row에 `track_name`, `track_artist`, `genre`, `subgenre`, `popularity`, `recommendation_score`, `matched_*`가 있으면 보존한다.
- `limit`은 기본 10, 최대 50으로 제한한다.

결과가 비어 있으면 실패가 아닌 degraded success로 반환한다.

```python
{
    "status": "success",
    "recommended_content_ids": [],
    "candidate_tracks": [],
    "traversal_reason": "neo4j traversal returned no candidates",
    "diversity_metadata": {"source": "neo4j", "degraded": True},
}
```

단, Neo4j 연결 실패나 쿼리 실행 오류는 삼키지 않고 상위 `KagDispatchAgent`가 error state로 처리하게 한다.

## 8. LLM 금지 규칙 상세

LLM은 KAG 결과 생성에 참여하지 않는다.

금지:

- LLM이 `content_id` 생성
- LLM이 `title` 생성
- LLM이 `artist` 생성
- LLM이 `KAG_STATE` 생성
- LLM이 `recommendation_category` 변경
- LLM이 Neo4j 결과를 대체
- LLM이 없는 곡을 후보로 생성

허용:

- InputPlannerAgent 단계에서 사용자 입력을 정규화
- mood, genre, situation 후보 추출
- `KAG_INPUT_JSON` 초안 생성 보조
- ResponseGenerator 단계에서 이미 선택된 추천 결과를 자연어로 설명

RealKagAdapter는 LLM 클라이언트를 import하지 않는다.

## 9. Neo4j 데이터 적재 방안

현재 DB가 비어 있으므로 데이터 적재가 필요하다.

### 9.1 권장안: one-shot loader 분리

루트 compose 기준 Neo4j 컨테이너를 유지하고, 별도 one-shot loader로 CSV를 적재한다.

특징:

- 앱 런타임과 데이터 적재 책임을 분리한다.
- 백엔드 시작 시 대량 적재를 수행하지 않는다.
- 재실행 가능하도록 idempotent `MERGE` 기반 쿼리를 사용한다.
- 루트 compose에 loader 서비스를 추가하려면 사용자 확인을 받는다.

### 9.2 대안: 수동 smoke 적재

초기 개발 단계에서는 `app/kag` 내부 smoke 스크립트로 소량 샘플 적재를 수행할 수 있다.

특징:

- 루트 compose 수정 없이 빠르게 연결 검증 가능
- 운영/팀 실행 절차로는 부적합
- 전체 데이터 적재 자동화는 별도 작업 필요

### 9.3 비추천: 백엔드 시작 시 자동 적재

백엔드 앱 시작 시 Neo4j 대량 적재를 수행하지 않는다.

이유:

- 앱 런타임과 데이터 초기화 책임이 섞인다.
- 컨테이너 재시작마다 긴 적재 작업이 발생할 수 있다.
- 장애 원인 분리가 어려워진다.

## 10. Docker 기준

루트 `Dockerfile`과 루트 `docker-compose.yml`을 기준으로 한다.

`neo4j/docker-compose.yml`은 런타임 기준에서 제외한다. 삭제는 사용자 확인 후 진행한다.

Neo4j 연결 설정은 루트 compose가 제공하는 `RIMAS_NEO4J_*`를 앱 KAG 연결 계층이 읽도록 맞춘다.

`neo4j/` 폴더의 데이터 적재/실행 관련 파일은 정리 대상이지만, 삭제 전 다음을 분리한다.

- 보존 대상: 원천 CSV, 현재 스키마 기준 문서, 재사용 가능한 적재 쿼리
- 삭제 후보: 루트 compose와 충돌하는 `neo4j/docker-compose.yml`
- 이동 후보: 적재 스크립트, 공통 적재 유틸리티

## 11. 구현 단계 초안

구현 계획은 별도 문서로 작성한다.

현재 설계 기준 작업 순서:

1. `app/kag/connection.py`에서 `RIMAS_NEO4J_*` 우선 연결을 구현하고 `psycopg` import 제거
2. `app/kag/constant.py`와 `app/kag/querys.py`의 관계명을 실제 적재 기준으로 정렬
3. `RealKagAdapter`에 deterministic 쿼리 선택과 KAG_STATE 매핑 구현
4. `app/kag/real_neo4j_kag_adapter_smoke.py`로 연결/쿼리/Adapter smoke 검증
5. Neo4j 데이터 적재 방안 중 one-shot loader 또는 수동 smoke 적재 선택
6. 사용자 확인 후 `KagDispatchAgent`에 Real 선택 경로와 `KAG_INPUT_JSON` 검증 추가
7. 사용자 확인 후 `neo4j/docker-compose.yml` 등 충돌 파일 정리

## 12. 이번 설계에서 제외하는 것

이번 설계 문서 갱신만으로는 다음 작업을 실행하지 않는다.

- 파일 삭제
- Docker volume 삭제
- Neo4j 데이터 초기화
- 루트 compose 수정
- `app/agents` 수정
- `docs` 공식 설계서 수정
- 테스트 파일 추가
- LLM 기반 KAG Tool 선택기 구현
- RAG/Elasticsearch 연동

위 작업은 구현 계획 작성 후 사용자 확인을 받고 진행한다.
