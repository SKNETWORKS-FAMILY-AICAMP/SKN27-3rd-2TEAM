# Real RAG Contract Cleanup Design

## 1. 목적

이번 작업의 목적은 RIMAS v4 설계 기준에 맞춰 Real RAG 검색 연결 범위, Runtime Contract, 실패 테스트 정리 기준, 불필요/후보 파일 정리 기준을 확정하는 것이다.

작업 순서는 다음으로 고정한다.

1. Real RAG 검색 연결
2. 계약 정리
3. 현재 실패 테스트 3개 정리
4. 불필요/후보 파일 정리

Elasticsearch 인덱스 생성, 대량 적재, reindex 파이프라인은 이번 범위에서 제외한다. 해당 작업은 Real RAG 조회 경로가 안정화된 뒤 별도 단계로 진행한다.

## 2. 현재 상태 요약

현재 프로젝트는 Mock KAG/RAG 기반 추천 흐름, InputPlanner 기반 `KAG_INPUT_JSON` 생성, `RAG_INPUT_JSON` 생성, Redis latest state 저장, Music Detail recent RAG 조회 일부를 포함한다.

하지만 다음 문제로 인해 설계 완료 상태로 볼 수 없다.

- `RIMAS_RAG_MODE=real` 선택 시 설계서 기준 파일은 `app/rag/adapters/rag_real_adapter.py`인데, 현재 구현은 `app/rag/adapters/real_rag_adapter.py`를 import한다.
- `app/rag/adapters/real_rag_adapter.py`는 `NotImplementedError` 상태다.
- `app/rag/adapters/rag_real_adapter.py`는 최종 기준 파일로 문서화되어 있으나 실제 Adapter 구현체가 아니다.
- `app/rag/services/retrieval.py`는 Elasticsearch URL, 인증 정보, index name이 하드코딩되어 있고 import 시점에 client를 만든다.
- `pytest -v` 기준 77개 중 3개 테스트가 실패한다.
- `app/rag/**` 아래 실험/후보 파일과 최종 런타임 파일이 혼재한다.

## 3. 확정 범위

이번 설계의 Real RAG 범위는 Elasticsearch에 이미 존재하는 `spotify_songs` 인덱스를 조회하여 KAG 후보 `content_id`에 대한 evidence를 생성하는 데까지다.

이번 범위에 포함한다.

- `RIMAS_RAG_MODE=real` 선택 경로를 `app/rag/adapters/rag_real_adapter.py` 기준으로 정리
- Elasticsearch 조회 전용 client/retriever 경계 정의
- `RAG_INPUT_JSON.kag_recommended_content_ids` 기반 content_id 필터링
- KAG 후보 밖 content_id 제거
- 검색 결과를 `RAG_STATE.recommended_content_evidence`로 매핑
- 검색 실패, index 없음, evidence 없음 상태를 명시적 `failed` 또는 `fallback` 상태로 반환
- Mock 전환을 자동으로 수행하지 않음
- 현재 실패 테스트 3개를 최종 계약 기준으로 통과시키는 방향 확정
- Real RAG 연결 이후 import 영향이 없는 후보 파일 정리 기준 확정

이번 범위에서 제외한다.

- Elasticsearch index 생성
- CSV/JSON 대량 적재
- embedding 생성 배치
- reindex alias 전략
- 검색 품질 튜닝
- LangGraph 기반 전체 RAG workflow 연결
- LLM을 이용한 RAG evidence 생성

## 4. 추천 아키텍처

Real RAG는 얇은 Adapter와 전용 Elasticsearch 조회 계층으로 나눈다.

```text
RagDispatchAgent
-> RAG_INPUT_JSON 생성
-> RIMAS_RAG_MODE 기준 Adapter 선택
-> RealRagAdapter
-> ElasticsearchRagRetriever
-> RagStateBuilder
-> RAG_STATE 반환
```

`RagDispatchAgent`는 검색을 직접 수행하지 않는다. Adapter 선택과 `RAG_INPUT_JSON` 전달까지만 담당한다.

`RealRagAdapter`는 Elasticsearch 세부 쿼리를 직접 하드코딩하지 않는다. 입력 검증, retriever 호출, evidence 매핑, 실패 상태 반환을 담당한다.

`ElasticsearchRagRetriever`는 Elasticsearch 연결, index 존재 확인, 검색 요청, hit 정규화를 담당한다.

## 5. 파일 기준

최종 기준 파일은 다음과 같다.

- `app/agents/rag_dispatch_agent.py`
  - `RIMAS_RAG_MODE`에 따라 Mock/Real Adapter를 선택한다.
  - Real 선택 시 `app.rag.adapters.rag_real_adapter.RealRagAdapter`를 사용한다.

- `app/rag/adapters/rag_real_adapter.py`
  - 최종 Real RAG Adapter 구현체다.
  - `RagAdapter` 인터페이스를 구현한다.
  - `build_state(kag_state, rag_input_json)`을 제공한다.

- `app/rag/adapters/mock_rag_adapter.py`
  - 기존 Mock RAG Adapter 기준 파일로 유지한다.

- `app/rag/adapters/real_rag_adapter.py`
  - 기존 import 호환이 필요하면 얇은 compatibility wrapper로만 둔다.
  - Real 연결 완료 후 직접 import가 사라지면 삭제 후보로 분류한다.

- `app/rag/services/elasticsearch_retriever.py`
  - 새 조회 전용 경계로 둔다.
  - 환경변수 기반 설정을 사용한다.
  - import 시점에 네트워크 연결을 만들지 않는다.

기존 `app/rag/services/retrieval.py`는 이번 설계 기준의 직접 사용 대상이 아니다. 연결 완료 후 삭제 또는 legacy 후보로 분류한다.

## 6. 설정 기준

Real RAG 조회 설정은 환경변수에서 읽는다.

- `RIMAS_ELASTICSEARCH_URL`
  - 기본값: `http://localhost:9200`
  - Docker Compose backend에서는 `http://elasticsearch:9200`을 사용한다.

- `RIMAS_ELASTICSEARCH_INDEX`
  - 기본값: `spotify_songs`

- `RIMAS_ELASTICSEARCH_TIMEOUT_SECONDS`
  - 기본값: `3`

현재 Docker Compose의 Elasticsearch는 `xpack.security.enabled=false`이므로 이번 설계에서는 기본 인증을 요구하지 않는다. 인증이 필요한 운영 구성은 별도 설정 확장 단계에서 다룬다.

## 7. 검색 규칙

Real RAG 검색은 반드시 `RAG_INPUT_JSON.kag_recommended_content_ids`를 기준으로 제한한다.

규칙은 다음과 같다.

- `kag_recommended_content_ids`가 비어 있으면 Elasticsearch를 호출하지 않고 `status="fallback"`을 반환한다.
- Elasticsearch query는 `content_id` 후보 범위와 `query_text`를 함께 사용한다.
- `require_content_id_match=true`일 때 KAG 후보 밖 hit는 모두 제거한다.
- `max_evidence_per_track`는 track별 evidence 개수 제한으로 사용한다.
- 최종 evidence 전체 개수는 KAG 후보 수와 track별 제한을 넘지 않는다.
- 검색 결과가 0개이면 `status="fallback"`과 빈 evidence를 반환한다.

검색 필드 후보는 인덱스의 실제 문서 구조 차이를 고려해 유연하게 매핑한다.

- content text: `content`, `text`, `metadata.text`
- content id: `content_id`, `track_id`, `metadata.content_id`, `metadata.track_id`, `metadata.doc_id`
- title: `title`, `song`, `track_name`, `metadata.title`, `metadata.song`, `metadata.track_name`
- artist: `artist`, `track_artist`, `metadata.artist`, `metadata.track_artist`, `metadata.Artist(s)`
- genre: `genre`, `playlist_genre`, `metadata.genre`, `metadata.Genre`, `metadata.playlist_genre`
- mood: `mood`, `emotion`, `metadata.mood`, `metadata.emotion`
- album: `album`, `track_album_name`, `metadata.album`, `metadata.Album`, `metadata.track_album_name`

## 8. RAG_STATE 계약

Real RAG 성공 응답은 기존 `RagStateBuilder.build()` 형태를 따른다.

성공 기준:

```json
{
  "status": "success",
  "recommended_content_evidence": [
    {
      "content_id": "track_001",
      "title": "Song Title",
      "artist": "Artist",
      "genre": ["indie"],
      "mood": ["calm"],
      "evidence_summary": "검색된 설명과 메타데이터를 기반으로 구성한 추천 근거"
    }
  ],
  "recommendation_reason": {
    "summary": "Elasticsearch evidence 기반 추천 근거 요약",
    "reason_items": ["후보 곡의 장르, 분위기, 설명이 사용자 질의와 연결됨"]
  },
  "retrieval_metadata": {
    "source": "elasticsearch",
    "index": "spotify_songs",
    "candidate_count": 3,
    "evidence_count": 3
  },
  "retrieval_trace": {
    "retrieval_strategy": "elasticsearch_candidate_filtered",
    "require_content_id_match": true,
    "filtered_content_ids": ["track_001", "track_002"]
  }
}
```

실패 또는 저하 응답은 다음 기준을 따른다.

- Elasticsearch 연결 실패: `status="failed"`
- index 없음: `status="failed"`
- KAG 후보 없음: `status="fallback"`
- 검색 결과 없음: `status="fallback"`
- hit 매핑 결과가 계약을 만족하지 못함: `status="fallback"`

실패/저하 응답도 `recommended_content_evidence`, `recommendation_reason`, `retrieval_metadata`, `retrieval_trace` 필드를 항상 포함한다.

## 9. 오류 처리

Real RAG는 조용히 Mock으로 전환하지 않는다.

오류 처리 규칙:

- Elasticsearch 연결 예외는 Adapter 내부에서 잡고 `failed` RAG_STATE로 반환한다.
- 검색 결과 없음은 예외가 아니라 `fallback` RAG_STATE로 반환한다.
- 잘못된 `rag_input_json`은 `failed` RAG_STATE로 반환한다.
- 로그에는 오류 원인을 남기되 API 응답에는 내부 stack trace를 노출하지 않는다.

상위 Orchestrator는 기존 정책대로 `rag_state.status == "error"`만 실패로 보는 구조라면 `failed/fallback` 처리 정책을 계약 정리 단계에서 명확히 고친다.

## 10. 계약 정리 기준

계약 정리는 구현 직후 다음 기준으로 진행한다.

- `RagDispatchAgent`의 Real import 경로는 설계서와 일치해야 한다.
- `RagInputSchema.retrieval_constraints.require_content_id_match`는 Real RAG에서 강제 적용되어야 한다.
- `RagStateSchema.status` 허용값은 `success`, `failed`, `fallback`을 포함해야 한다.
- Main Recommendation service 반환 계약은 하나로 고정한다.
  - 권장 계약: service는 `(view_model, session_degraded)`를 반환한다.
  - route와 tests는 이 계약에 맞춰 정리한다.
- Music Detail service 계약은 `get_detail(content_id, recent_rag_state=None)`로 고정한다.
  - route dependency override 테스트도 이 시그니처를 따른다.

## 11. 실패 테스트 3개 정리 기준

현재 실패 테스트는 다음 계약 불일치에서 발생한다.

1. `test_main_recommendation_service_returns_page_view_model`
   - service 반환값이 tuple인데 테스트는 dict를 기대한다.
   - 최종 계약은 `(view_model, session_degraded)`로 고정한다.
   - 테스트는 tuple을 풀어 `view_model`과 `session_degraded`를 검증한다.

2. `test_music_detail_api_uses_injected_detail_service`
   - route는 `recent_rag_state` keyword를 넘기는데 Stub은 받지 않는다.
   - 최종 service 인터페이스는 `get_detail(content_id, recent_rag_state=None)`로 고정한다.
   - Stub 테스트도 동일 시그니처를 따른다.

3. `test_recommendation_route_finishes_request_id_after_success`
   - route는 tuple 반환을 기대하는데 Stub은 dict를 반환한다.
   - Stub service는 `(view_model, False)`를 반환하도록 정리한다.

테스트를 코드에 맞추는 것이 아니라, 위 계약을 문서화한 뒤 테스트와 구현을 같은 계약으로 맞춘다.

## 12. 불필요/후보 파일 정리 기준

삭제 또는 정리 후보는 다음 순서로 처리한다.

1. 자동 생성물
   - `__pycache__/`
   - `.pytest_cache/`
   - `frontend/dist/`

2. 설계서상 런타임 제외 파일
   - `neo4j/docker-compose.yml`

3. Real RAG 연결 후 import 영향 확인 대상
   - `app/rag/adapters/real_rag_adapter.py`
   - `app/rag/adapters/rag_mock_adapter.py`
   - `app/rag/services/retrieval.py`
   - `app/rag/services/embedding.py`
   - `app/rag/services/indexing.py`
   - `app/rag/main-test.py`
   - `app/rag/rag_architecture.html`
   - `app/rag/output.md`
   - `app/rag/musicCatalogRepository/base_repostiory.py`
   - `app/rag/musicCatalogRepository/sql_repostiory.py`
   - `app/rag/musicCatalogRepository/loader2.py`
   - `app/rag/musicCatalogRepository/csv-row.py`

원천 데이터로 볼 수 있는 CSV/JSON 파일은 삭제하지 않는다.

## 13. 검증 기준

구현 완료 후 최소 검증은 다음이다.

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_agent_and_detail_flow.py tests/test_dispatch_adapter_mode.py tests/test_mock_rag_adapter.py tests/test_request_lifecycle_routes.py tests/test_main_recommendation_service.py tests/test_music_detail_api.py -v
C:\Python314\python.exe -m pytest -v
```

프론트엔드 영향이 있으면 다음도 실행한다.

```powershell
npm run build
```

Real Elasticsearch 통합 검증은 로컬 Elasticsearch에 `spotify_songs` 인덱스가 존재할 때만 수행한다. 인덱스가 없을 때는 `failed` 상태 반환을 검증하고, 인덱스 생성은 후속 단계로 넘긴다.

## 14. 승인된 결정

- 이번 Real RAG 범위는 실제 Elasticsearch 검색 연결까지다.
- Elasticsearch 인덱스 생성/대량 적재/reindex는 후속 단계로 미룬다.
- 최종 Real RAG Adapter 기준 파일은 `app/rag/adapters/rag_real_adapter.py`다.
- `RAG_INPUT_JSON.kag_recommended_content_ids` 밖의 content_id는 evidence에 포함하지 않는다.
- Real RAG 실패 시 자동 Mock 전환은 하지 않는다.
- 계약 정리, 실패 테스트 3개, 불필요/후보 파일 정리는 Real RAG 기준 확정 후 순서대로 진행한다.
