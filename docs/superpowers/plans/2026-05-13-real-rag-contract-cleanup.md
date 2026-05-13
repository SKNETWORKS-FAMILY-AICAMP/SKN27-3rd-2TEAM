# Real RAG Contract Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Real RAG를 `rag_real_adapter.py` 기준으로 Elasticsearch 조회까지 연결하고, RAG 계약과 현재 실패 테스트 3개를 정리한다.

**Architecture:** `RagDispatchAgent`는 `RAG_INPUT_JSON` 생성과 Adapter 선택만 담당한다. Real RAG는 `RealRagAdapter -> ElasticsearchRagRetriever -> RagStateBuilder` 흐름으로 분리하고, KAG 후보 `content_id` 밖 evidence를 생성하지 않는다. 파일 정리는 Real RAG 연결 후 import/test 영향 확인과 사용자 승인 이후에만 진행한다.

**Tech Stack:** Python 3.14 runtime, FastAPI app package, Pydantic v2, Elasticsearch Python client, pytest.

---

## File Structure

- Modify: `app/agents/rag_dispatch_agent.py`
  - Real mode import 경로를 `app.rag.adapters.rag_real_adapter.RealRagAdapter`로 변경한다.

- Modify: `app/config/settings.py`
  - Elasticsearch index와 timeout 설정을 환경변수로 추가한다.

- Create: `app/rag/services/elasticsearch_retriever.py`
  - Elasticsearch client 생성, index 존재 확인, 후보 content_id 필터 검색, hit 정규화를 담당한다.

- Modify: `app/rag/adapters/rag_real_adapter.py`
  - 최종 Real RAG Adapter 구현체로 전환한다.

- Modify: `app/rag/adapters/real_rag_adapter.py`
  - 기존 import 호환 wrapper로만 둔다.

- Modify: `app/schemas/rag_state_schema.py`
  - `status` 허용값을 `success`, `failed`, `fallback`으로 명시한다.

- Modify: `tests/test_dispatch_adapter_mode.py`
  - Real RAG 기준 import 경로를 `rag_real_adapter.py`로 변경한다.

- Create: `tests/test_real_rag_adapter.py`
  - Real RAG mapping, candidate filtering, fallback/failed 상태를 검증한다.

- Modify: `tests/test_main_recommendation_service.py`
  - service tuple 계약을 검증한다.

- Modify: `tests/test_request_lifecycle_routes.py`
  - StubRecommendationService가 `(view_model, False)`를 반환하도록 변경한다.

- Modify: `tests/test_music_detail_api.py`
  - StubMusicDetailService가 `recent_rag_state=None` 인자를 받도록 변경한다.

---

### Task 1: Real RAG Adapter Selection Contract

**Files:**
- Modify: `app/agents/rag_dispatch_agent.py`
- Modify: `tests/test_dispatch_adapter_mode.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_dispatch_adapter_mode.py`, change the Real RAG import to the final design path:

```python
from app.rag.adapters.rag_real_adapter import RealRagAdapter
```

Keep this assertion:

```python
def test_rag_dispatch_uses_real_adapter_when_env_mode_is_real(monkeypatch):
    monkeypatch.setenv("RIMAS_RAG_MODE", "real")

    agent = RagDispatchAgent()

    assert isinstance(agent._adapter, RealRagAdapter)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_dispatch_adapter_mode.py::test_rag_dispatch_uses_real_adapter_when_env_mode_is_real -v
```

Expected: FAIL because `RagDispatchAgent` still imports `app.rag.adapters.real_rag_adapter.RealRagAdapter`.

- [ ] **Step 3: Update dispatch import**

In `app/agents/rag_dispatch_agent.py`, replace:

```python
from app.rag.adapters.real_rag_adapter import RealRagAdapter
```

with:

```python
from app.rag.adapters.rag_real_adapter import RealRagAdapter
```

Keep `_build_default_adapter()` behavior:

```python
    @staticmethod
    def _build_default_adapter() -> RagAdapter:
        mode = os.getenv("RIMAS_RAG_MODE", "mock").strip().lower()
        if mode == "real":
            return RealRagAdapter()
        return MockRagAdapter()
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_dispatch_adapter_mode.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app/agents/rag_dispatch_agent.py tests/test_dispatch_adapter_mode.py
git commit -m "test: align real rag adapter selection contract"
```

---

### Task 2: Elasticsearch Retriever Boundary

**Files:**
- Modify: `app/config/settings.py`
- Create: `app/rag/services/elasticsearch_retriever.py`
- Create: `tests/test_real_rag_adapter.py`

- [ ] **Step 1: Write failing retriever tests**

Create `tests/test_real_rag_adapter.py` with these tests first:

```python
import pytest

from app.rag.adapters.rag_real_adapter import RealRagAdapter
from app.rag.services.elasticsearch_retriever import ElasticsearchRagHit


class StubRetriever:
    def __init__(self, hits=None, exc=None):
        self.hits = hits or []
        self.exc = exc
        self.calls = []

    def search(self, *, query_text, content_ids, max_evidence_per_track):
        self.calls.append(
            {
                "query_text": query_text,
                "content_ids": content_ids,
                "max_evidence_per_track": max_evidence_per_track,
            }
        )
        if self.exc:
            raise self.exc
        return self.hits


def _rag_input(content_ids=None):
    return {
        "request_id": "req_001",
        "user_id": "user_001",
        "session_id": "session_001",
        "intent_type": "personalized_recommendation",
        "kag_recommended_content_ids": content_ids or ["track_001"],
        "target_section": "personalized_section",
        "query_text": "calm indie night",
        "evidence_need": ["track_description", "recommendation_reason"],
        "retrieval_constraints": {
            "max_evidence_per_track": 2,
            "require_content_id_match": True,
        },
    }


def test_real_rag_adapter_maps_elasticsearch_hits_to_rag_state():
    retriever = StubRetriever(
        hits=[
            ElasticsearchRagHit(
                content_id="track_001",
                title="Midnight Loop",
                artist="Nova Lane",
                album="Night Sketch",
                genre=["indie"],
                mood=["calm"],
                content="A calm indie song for late night listening.",
                score=9.5,
            )
        ]
    )

    result = RealRagAdapter(retriever=retriever).build_state(
        kag_state={"recommended_content_ids": ["track_001"]},
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "success"
    assert result["recommended_content_evidence"][0]["content_id"] == "track_001"
    assert result["recommended_content_evidence"][0]["title"] == "Midnight Loop"
    assert result["retrieval_metadata"]["source"] == "elasticsearch"
    assert retriever.calls[0]["content_ids"] == ["track_001"]


def test_real_rag_adapter_filters_hits_outside_kag_candidates():
    retriever = StubRetriever(
        hits=[
            ElasticsearchRagHit(
                content_id="track_999",
                title="Outside",
                artist="Other",
                album=None,
                genre=[],
                mood=[],
                content="Outside candidate.",
                score=1.0,
            )
        ]
    )

    result = RealRagAdapter(retriever=retriever).build_state(
        kag_state={"recommended_content_ids": ["track_001"]},
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "fallback"
    assert result["recommended_content_evidence"] == []
    assert result["retrieval_metadata"]["reason"] == "no_candidate_matched_evidence"


def test_real_rag_adapter_returns_fallback_without_kag_candidates():
    result = RealRagAdapter(retriever=StubRetriever()).build_state(
        kag_state={"recommended_content_ids": []},
        rag_input_json=_rag_input([]),
    )

    assert result["status"] == "fallback"
    assert result["recommended_content_evidence"] == []
    assert result["retrieval_metadata"]["reason"] == "empty_kag_candidates"


def test_real_rag_adapter_returns_failed_when_retriever_raises():
    result = RealRagAdapter(retriever=StubRetriever(exc=RuntimeError("index missing"))).build_state(
        kag_state={"recommended_content_ids": ["track_001"]},
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "failed"
    assert result["recommended_content_evidence"] == []
    assert result["retrieval_metadata"]["reason"] == "retriever_error"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_real_rag_adapter.py -v
```

Expected: FAIL because `ElasticsearchRagHit` does not exist and `rag_real_adapter.py` is not implemented.

- [ ] **Step 3: Add Elasticsearch settings**

In `app/config/settings.py`, extend the Elasticsearch section:

```python
# Elasticsearch
RIMAS_ELASTICSEARCH_URL = os.getenv("RIMAS_ELASTICSEARCH_URL", "http://localhost:9200")
RIMAS_ELASTICSEARCH_INDEX = os.getenv("RIMAS_ELASTICSEARCH_INDEX", "spotify_songs")
RIMAS_ELASTICSEARCH_TIMEOUT = float(os.getenv("RIMAS_ELASTICSEARCH_TIMEOUT_SECONDS", "3"))
```

- [ ] **Step 4: Create retriever boundary**

Create `app/rag/services/elasticsearch_retriever.py`:

```python
from dataclasses import dataclass
from typing import Any

from elasticsearch import Elasticsearch

from app.config import settings


@dataclass(frozen=True)
class ElasticsearchRagHit:
    content_id: str
    title: str
    artist: str
    album: str | None
    genre: list[str]
    mood: list[str]
    content: str
    score: float


class ElasticsearchRagRetriever:
    """Elasticsearch에서 KAG 후보 content_id 범위 안의 RAG evidence를 조회한다."""

    def __init__(self, client=None, index_name: str | None = None):
        self._client = client
        self._index_name = index_name or settings.RIMAS_ELASTICSEARCH_INDEX

    def search(self, *, query_text: str, content_ids: list[str], max_evidence_per_track: int) -> list[ElasticsearchRagHit]:
        if not content_ids:
            return []

        client = self._client or self._build_client()
        if not client.indices.exists(index=self._index_name):
            raise RuntimeError(f"elasticsearch index not found: {self._index_name}")

        response = client.search(
            index=self._index_name,
            body=self._build_query(query_text, content_ids, max_evidence_per_track),
        )
        return self._map_hits(response.get("hits", {}).get("hits", []), set(content_ids))

    @staticmethod
    def _build_client():
        return Elasticsearch(
            settings.RIMAS_ELASTICSEARCH_URL,
            request_timeout=settings.RIMAS_ELASTICSEARCH_TIMEOUT,
        )

    @staticmethod
    def _build_query(query_text: str, content_ids: list[str], max_evidence_per_track: int) -> dict:
        size = max(1, len(content_ids) * max_evidence_per_track)
        return {
            "size": size,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "terms": {
                                "metadata.track_id.keyword": content_ids,
                            }
                        }
                    ],
                    "should": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": [
                                    "content^2",
                                    "text",
                                    "metadata.text",
                                    "metadata.song",
                                    "metadata.track_name",
                                    "metadata.artist",
                                    "metadata.track_artist",
                                    "metadata.genre",
                                    "metadata.emotion",
                                ],
                            }
                        }
                    ],
                    "minimum_should_match": 0,
                }
            },
        }

    def _map_hits(self, hits: list[dict[str, Any]], allowed_ids: set[str]) -> list[ElasticsearchRagHit]:
        mapped = []
        for hit in hits:
            source = hit.get("_source", {})
            metadata = source.get("metadata", {}) or {}
            content_id = self._first_text(
                source.get("content_id"),
                source.get("track_id"),
                metadata.get("content_id"),
                metadata.get("track_id"),
                metadata.get("doc_id"),
            )
            if not content_id or content_id not in allowed_ids:
                continue
            mapped.append(
                ElasticsearchRagHit(
                    content_id=content_id,
                    title=self._first_text(source.get("title"), source.get("song"), source.get("track_name"), metadata.get("title"), metadata.get("song"), metadata.get("track_name")),
                    artist=self._first_text(source.get("artist"), source.get("track_artist"), metadata.get("artist"), metadata.get("track_artist"), metadata.get("Artist(s)")),
                    album=self._first_text(source.get("album"), source.get("track_album_name"), metadata.get("album"), metadata.get("Album"), metadata.get("track_album_name")),
                    genre=self._list_value(source.get("genre"), source.get("playlist_genre"), metadata.get("genre"), metadata.get("Genre"), metadata.get("playlist_genre")),
                    mood=self._list_value(source.get("mood"), source.get("emotion"), metadata.get("mood"), metadata.get("emotion")),
                    content=self._first_text(source.get("content"), source.get("text"), metadata.get("text")),
                    score=float(hit.get("_score") or 0),
                )
            )
        return mapped

    @staticmethod
    def _first_text(*values) -> str:
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    @staticmethod
    def _list_value(*values) -> list[str]:
        for value in values:
            if value is None:
                continue
            if isinstance(value, list):
                return [str(item) for item in value if str(item).strip()]
            text = str(value).strip()
            if text:
                return [text]
        return []
```

- [ ] **Step 5: Run tests to verify current expected failure changes**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_real_rag_adapter.py -v
```

Expected: FAIL because `RealRagAdapter` still does not implement `build_state`.

- [ ] **Step 6: Commit**

```powershell
git add app/config/settings.py app/rag/services/elasticsearch_retriever.py tests/test_real_rag_adapter.py
git commit -m "test: define real rag retriever contract"
```

---

### Task 3: RealRagAdapter Implementation

**Files:**
- Modify: `app/rag/adapters/rag_real_adapter.py`
- Modify: `app/rag/adapters/real_rag_adapter.py`
- Modify: `app/schemas/rag_state_schema.py`
- Test: `tests/test_real_rag_adapter.py`
- Test: `tests/test_v4_runtime_contracts.py`

- [ ] **Step 1: Make `RagStateSchema.status` explicit**

In `app/schemas/rag_state_schema.py`, replace `status: str` with a literal union:

```python
from typing import Literal

from pydantic import BaseModel, Field
```

```python
class RagStateSchema(BaseModel):
    status: Literal["success", "failed", "fallback"]
    query: str = ""
    normalized_query: str = ""
    recommended_content_evidence: list[RagEvidenceSchema] = Field(default_factory=list)
    recommendation_reason: RecommendationReasonSchema
    retrieval_metadata: dict = Field(default_factory=dict)
    retrieval_trace: dict = Field(default_factory=dict)
```

- [ ] **Step 2: Implement final RealRagAdapter**

Replace `app/rag/adapters/rag_real_adapter.py` with:

```python
import logging

from app.rag.adapters.rag_adapter import RagAdapter
from app.rag.builders.rag_state_builder import RagStateBuilder
from app.rag.services.elasticsearch_retriever import ElasticsearchRagRetriever, ElasticsearchRagHit

logger = logging.getLogger("rimas.rag.real")


class RealRagAdapter(RagAdapter):
    """Elasticsearch 기반 Real RAG Adapter."""

    def __init__(self, retriever=None):
        self._retriever = retriever or ElasticsearchRagRetriever()

    def build_state(self, kag_state: dict, rag_input_json: dict | None = None) -> dict:
        rag_input_json = rag_input_json or {}
        content_ids = self._candidate_content_ids(kag_state, rag_input_json)
        query_text = str(rag_input_json.get("query_text") or "").strip()
        constraints = rag_input_json.get("retrieval_constraints", {}) or {}
        max_evidence_per_track = int(constraints.get("max_evidence_per_track", 3))

        if not content_ids:
            return self._fallback("empty_kag_candidates", query_text, content_ids)

        try:
            hits = self._retriever.search(
                query_text=query_text,
                content_ids=content_ids,
                max_evidence_per_track=max_evidence_per_track,
            )
        except Exception as exc:
            logger.warning("real_rag_retriever_error", extra={"error": str(exc)})
            return self._failed("retriever_error", query_text, content_ids, str(exc))

        evidence = self._build_evidence(hits, set(content_ids))
        if not evidence:
            return self._fallback("no_candidate_matched_evidence", query_text, content_ids)

        return RagStateBuilder.build(
            context_type=str(kag_state.get("recommendation_goal", {}).get("primary_goal", "")),
            base_context=query_text,
            source_type="elasticsearch",
            evidence=evidence,
            reason_summary="Elasticsearch evidence 기반으로 KAG 후보의 추천 근거를 구성했습니다.",
            reason_items=["KAG 후보 content_id 범위 안에서만 검색 근거를 사용했습니다."],
            query=query_text,
            normalized_query=query_text,
            retrieval_metadata={
                "source": "elasticsearch",
                "candidate_count": len(content_ids),
                "evidence_count": len(evidence),
            },
            retrieval_trace={
                "retrieval_strategy": "elasticsearch_candidate_filtered",
                "require_content_id_match": True,
                "filtered_content_ids": content_ids,
            },
        )

    @staticmethod
    def _candidate_content_ids(kag_state: dict, rag_input_json: dict) -> list[str]:
        raw_ids = rag_input_json.get("kag_recommended_content_ids") or kag_state.get("recommended_content_ids", [])
        return [str(content_id) for content_id in raw_ids if str(content_id).strip()]

    @staticmethod
    def _build_evidence(hits: list[ElasticsearchRagHit], allowed_ids: set[str]) -> list[dict]:
        evidence = []
        for hit in hits:
            if hit.content_id not in allowed_ids:
                continue
            evidence.append(
                {
                    "content_id": hit.content_id,
                    "title": hit.title,
                    "artist": hit.artist,
                    "album": hit.album,
                    "genre": hit.genre,
                    "mood": hit.mood,
                    "evidence_summary": hit.content,
                    "recommendation_category": "personalized_match",
                    "retrieval_score": hit.score,
                }
            )
        return evidence

    @staticmethod
    def _fallback(reason: str, query_text: str, content_ids: list[str]) -> dict:
        state = RagStateBuilder.failure(reason)
        state["status"] = "fallback"
        state["query"] = query_text
        state["normalized_query"] = query_text
        state["retrieval_metadata"] = {
            "source": "elasticsearch",
            "reason": reason,
            "candidate_count": len(content_ids),
            "evidence_count": 0,
        }
        state["retrieval_trace"] = {
            "retrieval_strategy": "elasticsearch_candidate_filtered",
            "require_content_id_match": True,
            "filtered_content_ids": content_ids,
        }
        return state

    @staticmethod
    def _failed(reason: str, query_text: str, content_ids: list[str], error: str) -> dict:
        state = RagStateBuilder.failure(reason)
        state["status"] = "failed"
        state["query"] = query_text
        state["normalized_query"] = query_text
        state["retrieval_metadata"] = {
            "source": "elasticsearch",
            "reason": reason,
            "candidate_count": len(content_ids),
            "evidence_count": 0,
        }
        state["retrieval_trace"] = {
            "retrieval_strategy": "elasticsearch_candidate_filtered",
            "require_content_id_match": True,
            "filtered_content_ids": content_ids,
            "error": error,
        }
        return state
```

- [ ] **Step 3: Keep legacy import compatible**

Replace `app/rag/adapters/real_rag_adapter.py` with:

```python
from app.rag.adapters.rag_real_adapter import RealRagAdapter

__all__ = ["RealRagAdapter"]
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_real_rag_adapter.py tests/test_dispatch_adapter_mode.py tests/test_v4_runtime_contracts.py::test_rag_state_schema_preserves_optional_retrieval_fields -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app/rag/adapters/rag_real_adapter.py app/rag/adapters/real_rag_adapter.py app/schemas/rag_state_schema.py tests/test_real_rag_adapter.py
git commit -m "feat: connect real rag adapter to elasticsearch retriever"
```

---

### Task 4: Fix Current Contract Test Failures

**Files:**
- Modify: `tests/test_main_recommendation_service.py`
- Modify: `tests/test_request_lifecycle_routes.py`
- Modify: `tests/test_music_detail_api.py`

- [ ] **Step 1: Fix main recommendation service test contract**

In `tests/test_main_recommendation_service.py`, replace:

```python
    view_model = MainRecommendationService(orchestrator=StubOrchestrator()).get_page_view_model(
        "user_001", "session_abc"
    )
```

with:

```python
    view_model, session_degraded = MainRecommendationService(orchestrator=StubOrchestrator()).get_page_view_model(
        "user_001", "session_abc"
    )
```

Add after the call:

```python
    assert isinstance(session_degraded, bool)
```

- [ ] **Step 2: Fix recommendation route stub contract**

In `tests/test_request_lifecycle_routes.py`, replace `StubRecommendationService.get_page_view_model` return with:

```python
    def get_page_view_model(self, user_id, session_id):
        self.calls.append((user_id, session_id))
        return {"personalized": [], "new_release": [], "discovery": []}, False
```

- [ ] **Step 3: Fix music detail stub contract**

In `tests/test_music_detail_api.py`, replace:

```python
            def get_detail(self, content_id):
```

with:

```python
            def get_detail(self, content_id, recent_rag_state=None):
```

- [ ] **Step 4: Run the three failing tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_main_recommendation_service.py::test_main_recommendation_service_returns_page_view_model tests/test_music_detail_api.py::test_music_detail_api_uses_injected_detail_service tests/test_request_lifecycle_routes.py::test_recommendation_route_finishes_request_id_after_success -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_main_recommendation_service.py tests/test_request_lifecycle_routes.py tests/test_music_detail_api.py
git commit -m "test: align service stubs with runtime contracts"
```

---

### Task 5: Full Verification and Cleanup Report

**Files:**
- No source deletion in this task without user approval.
- Read-only inspection for cleanup candidates.

- [ ] **Step 1: Run Real RAG and runtime contract suite**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_real_rag_adapter.py tests/test_dispatch_adapter_mode.py tests/test_mock_rag_adapter.py tests/test_v4_agent_and_detail_flow.py tests/test_v4_runtime_contracts.py -v
```

Expected: PASS.

- [ ] **Step 2: Run all backend tests**

Run:

```powershell
C:\Python314\python.exe -m pytest -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```powershell
npm run build
```

Working directory: `C:\dev\Project\SKN27-3rd-2TEAM\frontend`

Expected: PASS.

- [ ] **Step 4: Inspect cleanup candidates**

Run:

```powershell
rg -n "from app.rag.adapters.real_rag_adapter|from app.rag.adapters.rag_mock_adapter|app.rag.services.retrieval|app.rag.services.embedding|app.rag.services.indexing|base_repostiory|sql_repostiory|loader2|csv-row" app tests docs README.md
```

Expected: Output identifies whether candidate files are still imported or only documented.

- [ ] **Step 5: Prepare cleanup approval list**

Report these groups to the user:

```text
자동 생성물 삭제 가능:
- __pycache__/
- .pytest_cache/
- frontend/dist/

사용자 승인 후 삭제 후보:
- neo4j/docker-compose.yml

Real RAG 연결 후 legacy 후보:
- app/rag/adapters/real_rag_adapter.py
- app/rag/adapters/rag_mock_adapter.py
- app/rag/services/retrieval.py
- app/rag/services/embedding.py
- app/rag/services/indexing.py
- app/rag/main-test.py
- app/rag/rag_architecture.html
- app/rag/output.md
- app/rag/musicCatalogRepository/base_repostiory.py
- app/rag/musicCatalogRepository/sql_repostiory.py
- app/rag/musicCatalogRepository/loader2.py
- app/rag/musicCatalogRepository/csv-row.py
```

- [ ] **Step 6: Commit verification-only docs if changed**

If this task produces only a user-facing report and no file changes, do not commit.

If a cleanup report file is added after user approval, run:

```powershell
git add docs/superpowers/reports/<report-file>.md
git commit -m "docs: report real rag cleanup candidates"
```

---

## Self-Review

- Spec coverage: Real RAG Adapter path, Elasticsearch retriever boundary, KAG candidate filtering, `failed/fallback` contract, current three failing tests, and cleanup approval gate are covered.
- Placeholder scan: No `TBD`, incomplete implementation slots, or undefined file paths are required for execution.
- Type consistency: `RealRagAdapter.build_state(kag_state, rag_input_json)` matches `RagAdapter`; `ElasticsearchRagHit` fields match evidence mapping; service contracts match current route usage.
