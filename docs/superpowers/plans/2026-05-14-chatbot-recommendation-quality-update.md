# Chatbot Recommendation Quality Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 사용자의 부정 취향, 요청 곡 수, 중복 추천, 빈 메인 섹션, raw 추천 이유 노출 문제를 한 번의 품질 업데이트로 해결한다.

**Architecture:** 기존 KAG/RAG/Recommendation/ResponseGenerator 흐름은 유지한다. 부정 취향은 Redis session context와 PostgreSQL에 저장하고, 추천 후보 필터와 최종 응답 검증에서 다시 방어한다. 추천 이유는 deterministic draft를 먼저 만들고 LLM 후처리는 validator 통과 시에만 사용한다.

**Tech Stack:** FastAPI, Pydantic, Redis cache helpers, PostgreSQL repositories, pytest, OpenAI JSON response client.

---

## File Structure

- Modify `db/schema.sql`: `user_negative_preferences` table and index 추가.
- Modify `app/repositories/query_constants.py`: 부정 취향 upsert/select SQL, fallback 추천 SQL 추가.
- Create `app/repositories/negative_preference_repository.py`: PostgreSQL 부정 취향 저장/조회.
- Create `app/services/negative_preference_service.py`: Redis context와 DB 저장 사이의 부정 취향 병합 orchestration.
- Modify `app/schemas/session_context_schema.py`: `disliked_artists`, `disliked_tracks` 추가.
- Modify `app/schemas/intent_state_schema.py`: `requested_count`, `disliked_artists`, `disliked_tracks` 추가.
- Modify `app/schemas/kag_input_schema.py`: `excluded_artists`, `excluded_tracks` constraints 추가.
- Modify `app/cache/session_history_cache.py`: empty/update context에 부정 취향 반영.
- Modify `app/services/session_context_hydration_service.py`: DB 부정 취향 hydrate.
- Modify `app/prompts/input_planner_prompt.py`: LLM planner 출력 schema 확장.
- Modify `app/agents/input_planner_agent.py`: 요청 수/부정 취향 rule parsing 및 KAG_INPUT 전달.
- Modify `app/agents/intent_agent.py`: `requested_count` pass-through.
- Modify `app/agents/kag_dispatch_agent.py`: `max_candidates`를 adapter limit으로 전달.
- Modify `app/kag/adapters/mock_kag_adapter.py`: excluded_nodes 기록 및 mock 후보 제한.
- Modify `app/kag/adapters/real_kag_adapter.py`: excluded_nodes 기록 및 row 후처리 필터.
- Modify `app/rag/adapters/mock_rag_adapter.py`: mock pool 확장, excluded_nodes 필터.
- Modify `app/rag/adapters/rag_real_adapter.py`: excluded_nodes 필터, category 결정, release_type 전달.
- Modify `app/rag/services/elasticsearch_retriever.py`: `release_type` hit 필드 추가.
- Modify `app/agents/recommendation_agent.py`: requested_count, dedup, dislike filter, display reason draft.
- Create `app/validators/display_reason_validator.py`: LLM display_reason 검증.
- Modify `app/agents/response_generator.py`: LLM display_reason 후처리 규칙과 local fallback 정제.
- Modify `app/services/main_recommendation_service.py`: 섹션 dedup, fallback 채우기.
- Modify `app/repositories/music_catalog_repository.py`: fallback new_release/discovery 조회.

---

### Task 1: Negative Preference Persistence Contract

**Files:**
- Modify: `db/schema.sql`
- Modify: `app/repositories/query_constants.py`
- Create: `app/repositories/negative_preference_repository.py`
- Test: `tests/test_negative_preference_repository.py`
- Test: `tests/test_v4_infra_contract.py`

- [ ] **Step 1: Write failing schema test**

Add to `tests/test_v4_infra_contract.py`:

```python
def test_schema_contains_user_negative_preferences_table():
    sql = Path("db/schema.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS user_negative_preferences" in sql
    assert "disliked_artists_json JSONB NOT NULL DEFAULT '[]'::JSONB" in sql
    assert "disliked_tracks_json JSONB NOT NULL DEFAULT '[]'::JSONB" in sql
    assert "idx_user_negative_preferences_updated_at" in sql
```

- [ ] **Step 2: Write failing repository test**

Create `tests/test_negative_preference_repository.py`:

```python
from app.repositories.negative_preference_repository import NegativePreferenceRepository


class FakeCursor:
    def __init__(self, row=None):
        self.row = row
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, row=None):
        self.cursor_obj = FakeCursor(row=row)
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True


def test_negative_preference_repository_upserts_and_reads_profile():
    conn = FakeConnection(
        row={
            "user_id": "user_001",
            "disliked_artists_json": ["Billie Eilish"],
            "disliked_tracks_json": ["track_999"],
        }
    )
    repo = NegativePreferenceRepository(conn)

    repo.upsert(
        user_id="user_001",
        disliked_artists=["Billie Eilish"],
        disliked_tracks=["track_999"],
    )
    profile = repo.find_by_user_id("user_001")

    assert conn.committed
    assert profile["disliked_artists_json"] == ["Billie Eilish"]
    assert profile["disliked_tracks_json"] == ["track_999"]
```

- [ ] **Step 3: Run failing tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_infra_contract.py::test_schema_contains_user_negative_preferences_table tests/test_negative_preference_repository.py -v
```

Expected: fail because table and repository do not exist.

- [ ] **Step 4: Implement schema and repository**

Add to `db/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS user_negative_preferences (
    user_id VARCHAR(64) PRIMARY KEY REFERENCES users(user_id),
    disliked_artists_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    disliked_tracks_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_negative_preferences_updated_at
ON user_negative_preferences(updated_at DESC);
```

Add SQL constants:

```python
UPSERT_USER_NEGATIVE_PREFERENCES = """
INSERT INTO user_negative_preferences (
    user_id,
    disliked_artists_json,
    disliked_tracks_json,
    updated_at
) VALUES (
    %(user_id)s,
    %(disliked_artists_json)s,
    %(disliked_tracks_json)s,
    NOW()
)
ON CONFLICT (user_id) DO UPDATE SET
    disliked_artists_json = EXCLUDED.disliked_artists_json,
    disliked_tracks_json = EXCLUDED.disliked_tracks_json,
    updated_at = NOW();
"""

SELECT_USER_NEGATIVE_PREFERENCES = """
SELECT
    user_id,
    disliked_artists_json,
    disliked_tracks_json,
    updated_at
FROM user_negative_preferences
WHERE user_id = %(user_id)s;
"""
```

Create repository:

```python
from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class NegativePreferenceRepository(BaseRepository):
    def __init__(self, connection):
        self._connection = connection

    def upsert(self, *, user_id: str, disliked_artists: list[str], disliked_tracks: list[str]) -> str:
        if not user_id:
            raise ValueError("user_id is required")
        with self._connection.cursor() as cursor:
            cursor.execute(
                query_constants.UPSERT_USER_NEGATIVE_PREFERENCES,
                {
                    "user_id": user_id,
                    "disliked_artists_json": disliked_artists,
                    "disliked_tracks_json": disliked_tracks,
                },
            )
        self._connection.commit()
        return user_id

    def find_by_user_id(self, user_id: str) -> dict | None:
        if not user_id:
            raise ValueError("user_id is required")
        with self._cursor() as cursor:
            cursor.execute(query_constants.SELECT_USER_NEGATIVE_PREFERENCES, {"user_id": user_id})
            return cursor.fetchone()
```

- [ ] **Step 5: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_infra_contract.py tests/test_negative_preference_repository.py -v
```

Expected: pass.

---

### Task 2: Session Context And Hydration Contract

**Files:**
- Modify: `app/schemas/session_context_schema.py`
- Modify: `app/cache/session_history_cache.py`
- Modify: `app/services/session_context_hydration_service.py`
- Create: `app/services/negative_preference_service.py`
- Test: `tests/test_v4_runtime_contracts.py`
- Test: `tests/test_session_context_hydration.py`

- [ ] **Step 1: Write failing contract tests**

Add to `tests/test_v4_runtime_contracts.py`:

```python
def test_session_context_schema_accepts_negative_preferences():
    from app.schemas.session_context_schema import SessionContextSchema

    ctx = SessionContextSchema(
        session_id="session_001",
        disliked_artists=["Billie Eilish"],
        disliked_tracks=["track_999"],
    )

    assert ctx.disliked_artists == ["Billie Eilish"]
    assert ctx.disliked_tracks == ["track_999"]
```

Add to `tests/test_session_context_hydration.py`:

```python
def test_hydration_merges_negative_preferences():
    class TasteRepo:
        def find_profile(self, user_id):
            return None

    class NegativeRepo:
        def find_by_user_id(self, user_id):
            return {
                "user_id": user_id,
                "disliked_artists_json": ["Billie Eilish"],
                "disliked_tracks_json": ["track_999"],
            }

    service = SessionContextHydrationService(
        repository=TasteRepo(),
        negative_repository=NegativeRepo(),
    )

    ctx = service.hydrate(user_id="user_001", session_id="session_001")

    assert ctx["disliked_artists"] == ["Billie Eilish"]
    assert ctx["disliked_tracks"] == ["track_999"]
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_runtime_contracts.py::test_session_context_schema_accepts_negative_preferences tests/test_session_context_hydration.py::test_hydration_merges_negative_preferences -v
```

Expected: fail because fields and constructor dependency are missing.

- [ ] **Step 3: Implement context fields and hydration**

Update `SessionContextSchema`:

```python
disliked_artists: list[str] = Field(default_factory=list)
disliked_tracks: list[str] = Field(default_factory=list)
```

Update `_empty_context()` and `_empty_context_shape()`:

```python
"disliked_artists": [],
"disliked_tracks": [],
```

Update `SessionContextHydrationService.__init__`:

```python
def __init__(self, repository=None, negative_repository=None):
    self._repository = repository
    self._negative_repository = negative_repository
```

Merge negative profile:

```python
negative_profile = (
    self._negative_repository.find_by_user_id(user_id)
    if self._negative_repository
    else None
)
context["disliked_artists"] = list((negative_profile or {}).get("disliked_artists_json") or [])[:50]
context["disliked_tracks"] = list((negative_profile or {}).get("disliked_tracks_json") or [])[:50]
```

- [ ] **Step 4: Implement negative preference service**

Create `app/services/negative_preference_service.py`:

```python
class NegativePreferenceService:
    def __init__(self, repository=None):
        self._repository = repository

    def merge_and_save(
        self,
        *,
        user_id: str,
        existing_artists: list[str],
        existing_tracks: list[str],
        new_artists: list[str],
        new_tracks: list[str],
    ) -> dict:
        disliked_artists = _merge_unique(new_artists, existing_artists, limit=50)
        disliked_tracks = _merge_unique(new_tracks, existing_tracks, limit=50)
        if self._repository and (new_artists or new_tracks):
            self._repository.upsert(
                user_id=user_id,
                disliked_artists=disliked_artists,
                disliked_tracks=disliked_tracks,
            )
        return {
            "disliked_artists": disliked_artists,
            "disliked_tracks": disliked_tracks,
        }


def _merge_unique(new_items: list[str], existing_items: list[str], limit: int) -> list[str]:
    merged = []
    seen = set()
    for value in list(new_items) + list(existing_items):
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            merged.append(text)
    return merged[:limit]
```

- [ ] **Step 5: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_runtime_contracts.py tests/test_session_context_hydration.py -v
```

Expected: pass.

---

### Task 3: Input Planner Requested Count And Negative Extraction

**Files:**
- Modify: `app/schemas/intent_state_schema.py`
- Modify: `app/schemas/kag_input_schema.py`
- Modify: `app/prompts/input_planner_prompt.py`
- Modify: `app/agents/input_planner_agent.py`
- Modify: `app/agents/intent_agent.py`
- Test: `tests/test_v4_agent_and_detail_flow.py`
- Test: `tests/test_chatbot_service.py`

- [ ] **Step 1: Write failing planner tests**

Add tests:

```python
def test_input_planner_extracts_requested_count_from_korean_number():
    result = InputPlannerAgent().run(
        user_id="user_001",
        session_id="session_001",
        request_id="req_001",
        user_input="잔잔한 곡 두 곡 추천해줘",
        session_context={},
    )

    assert result["intent_state"]["requested_count"] == 2
    assert result["kag_input_json"]["constraints"]["max_candidates"] == 2
```

```python
def test_input_planner_extracts_disliked_artist_and_excludes_existing_context():
    result = InputPlannerAgent().run(
        user_id="user_001",
        session_id="session_001",
        request_id="req_001",
        user_input="Billie Eilish 싫어 추천하지 마",
        session_context={"disliked_artists": ["Adele"], "disliked_tracks": []},
    )

    assert "Billie Eilish" in result["intent_state"]["disliked_artists"]
    assert result["kag_input_json"]["constraints"]["excluded_artists"] == ["Billie Eilish", "Adele"]
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_agent_and_detail_flow.py::test_input_planner_extracts_requested_count_from_korean_number tests/test_v4_agent_and_detail_flow.py::test_input_planner_extracts_disliked_artist_and_excludes_existing_context -v
```

Expected: fail because fields are missing.

- [ ] **Step 3: Extend schemas**

Update `IntentStateSchema`:

```python
requested_count: int | None = Field(default=None, ge=1)
disliked_artists: list[str] = Field(default_factory=list)
disliked_tracks: list[str] = Field(default_factory=list)
```

Update `KagInputConstraintsSchema`:

```python
excluded_artists: list[str] = Field(default_factory=list)
excluded_tracks: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Implement parser rules**

Add helper methods to `InputPlannerAgent`:

```python
def _detect_requested_count(self, text: str) -> int | None:
    patterns = {
        1: ("1곡", "한 곡", "하나"),
        2: ("2곡", "두 곡", "둘"),
        3: ("3곡", "세 곡", "셋"),
    }
    compact = text.replace(" ", "")
    for count, tokens in patterns.items():
        if any(token.replace(" ", "") in compact for token in tokens):
            return count
    return None
```

```python
def _detect_negative_preferences(self, text: str) -> dict:
    negative_markers = ("싫어", "싫다", "별로", "듣기 싫어", "추천하지 마", "빼줘", "제외")
    if not any(marker in text for marker in negative_markers):
        return {"disliked_artists": [], "disliked_tracks": []}
    candidate = text
    for marker in negative_markers:
        candidate = candidate.split(marker)[0]
    candidate = candidate.strip(" ,.!?를은이가")
    return {
        "disliked_artists": [candidate] if candidate else [],
        "disliked_tracks": [],
    }
```

Use these values in `IntentStateSchema` and `KagInputSchema.constraints`.

- [ ] **Step 5: Pass through intent result**

Update `IntentAgent.run()` to return:

```python
"requested_count": (intent_state or {}).get("requested_count"),
"disliked_artists": (intent_state or {}).get("disliked_artists", []),
"disliked_tracks": (intent_state or {}).get("disliked_tracks", []),
```

- [ ] **Step 6: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_agent_and_detail_flow.py tests/test_chatbot_service.py -v
```

Expected: pass.

---

### Task 4: KAG/RAG Exclusion And Requested Candidate Limit

**Files:**
- Modify: `app/agents/kag_dispatch_agent.py`
- Modify: `app/kag/adapters/mock_kag_adapter.py`
- Modify: `app/kag/adapters/real_kag_adapter.py`
- Modify: `app/rag/adapters/mock_rag_adapter.py`
- Modify: `app/rag/adapters/rag_real_adapter.py`
- Modify: `app/rag/services/elasticsearch_retriever.py`
- Test: `tests/test_mock_kag_adapter.py`
- Test: `tests/test_real_kag_adapter.py`
- Test: `tests/test_mock_rag_adapter.py`
- Test: `tests/test_real_rag_adapter.py`

- [ ] **Step 1: Write failing adapter tests**

Add tests asserting:

```python
def test_mock_kag_adapter_records_excluded_nodes():
    state = MockKagAdapter().build_state(
        "user_001",
        "추천",
        {"disliked_artists": ["Nova Lane"], "disliked_tracks": ["track_003"]},
        limit=2,
    )

    assert {"type": "artist", "value": "Nova Lane"} in state["excluded_nodes"]
    assert {"type": "track", "value": "track_003"} in state["excluded_nodes"]
    assert len(state["recommended_content_ids"]) <= 2
```

```python
def test_real_rag_adapter_filters_excluded_artist():
    retriever = StubRetriever(
        hits=[
            ElasticsearchRagHit(
                content_id="track_001",
                title="Bad Fit",
                artist="Billie Eilish",
                album=None,
                genre=["pop"],
                mood=["night"],
                content="raw evidence",
                score=1.0,
                release_type="existing_catalog",
            )
        ]
    )
    result = RealRagAdapter(retriever=retriever).build_state(
        kag_state={
            "recommended_content_ids": ["track_001"],
            "excluded_nodes": [{"type": "artist", "value": "Billie Eilish"}],
        },
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "fallback"
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_mock_kag_adapter.py tests/test_real_rag_adapter.py -v
```

Expected: fail because signatures and release_type field are missing.

- [ ] **Step 3: Implement KAG limit and exclusions**

Update `KagDispatchAgent.run()`:

```python
constraints = (kag_input_json or {}).get("constraints", {})
limit = int(constraints.get("max_candidates", 10))
kag_state = self._adapter.build_state(user_id, normalized_input, session_context, limit=limit)
```

Update mock/real adapters to accept `limit` and build:

```python
excluded_nodes = _build_excluded_nodes(session_context)
```

Filter candidate tracks:

```python
if track["content_id"] in excluded_tracks:
    continue
if track.get("artist") in excluded_artists:
    continue
```

- [ ] **Step 4: Implement RAG defensive filter and release_type**

Update `ElasticsearchRagHit`:

```python
release_type: str = "existing_catalog"
```

Map release type from source/metadata.

In RAG adapters, build excluded sets from `kag_state["excluded_nodes"]` and skip matching evidence.

Determine category:

```python
if hit.release_type == "new_release":
    category = "new_release"
elif target_section == "discovery_section":
    category = "discovery_candidate"
elif target_section == "new_release_section":
    category = "new_release"
else:
    category = "personalized_match"
```

- [ ] **Step 5: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_mock_kag_adapter.py tests/test_real_kag_adapter.py tests/test_mock_rag_adapter.py tests/test_real_rag_adapter.py -v
```

Expected: pass.

---

### Task 5: Recommendation Selection, Dedup, Requested Count, Display Draft

**Files:**
- Modify: `app/agents/recommendation_agent.py`
- Test: `tests/test_v4_agent_and_detail_flow.py`
- Test: `tests/test_response_generator_fallback.py`

- [ ] **Step 1: Write failing recommendation tests**

Add tests:

```python
def test_recommendation_agent_deduplicates_content_id_and_respects_requested_count():
    evidence = [
        {"content_id": "track_001", "title": "A", "artist": "X", "genre": ["indie"], "mood": ["calm"], "recommendation_category": "personalized_match", "evidence_summary": "raw one"},
        {"content_id": "track_001", "title": "A", "artist": "X", "genre": ["indie"], "mood": ["calm"], "recommendation_category": "personalized_match", "evidence_summary": "raw two"},
        {"content_id": "track_002", "title": "B", "artist": "Y", "genre": ["rnb"], "mood": ["night"], "recommendation_category": "personalized_match", "evidence_summary": "raw three"},
    ]

    result = RecommendationAgent().run(
        intent_result={"intent_type": "personalized_recommendation", "requested_count": 1},
        rag_state={"recommended_content_evidence": evidence},
    )

    assert len(result["selected_recommendations"]) == 1
    assert result["selected_recommendations"][0]["content_id"] == "track_001"
```

```python
def test_recommendation_agent_does_not_copy_raw_evidence_to_display_reason():
    raw = "lyrics lyrics lyrics raw document"
    result = RecommendationAgent().run(
        intent_result={"intent_type": "personalized_recommendation"},
        rag_state={"recommended_content_evidence": [
            {"content_id": "track_001", "title": "A", "artist": "X", "genre": ["indie"], "mood": ["calm"], "recommendation_category": "personalized_match", "evidence_summary": raw}
        ]},
    )

    assert result["selected_recommendations"][0]["display_reason"] != raw
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_agent_and_detail_flow.py::test_recommendation_agent_deduplicates_content_id_and_respects_requested_count tests/test_v4_agent_and_detail_flow.py::test_recommendation_agent_does_not_copy_raw_evidence_to_display_reason -v
```

Expected: second test fails because raw evidence is copied.

- [ ] **Step 3: Implement selection changes**

Update `RecommendationAgent.run()` to pass requested count:

```python
requested_count = intent_result.get("requested_count")
selected = self._select(intent_type, evidence, requested_count=requested_count)
```

Clamp count:

```python
def _target_count(self, requested_count):
    if requested_count is None:
        return MAX_SELECTED_RECOMMENDATIONS
    return max(1, min(int(requested_count), MAX_SELECTED_RECOMMENDATIONS))
```

Add display reason helper:

```python
def build_display_reason(item: dict) -> str:
    genres = item.get("genre") or []
    moods = item.get("mood") or []
    genre_text = ", ".join(genres[:2]) if genres else "현재 취향"
    mood_text = ", ".join(moods[:2]) if moods else "듣기 좋은 분위기"
    category = item.get("recommendation_category")
    if category == "new_release":
        return f"최근 업데이트된 곡 중 {genre_text} 성향과 {mood_text} 분위기를 함께 볼 수 있는 곡입니다."
    if category == "discovery_candidate":
        return f"{mood_text} 흐름을 유지하면서 {genre_text} 쪽으로 취향을 넓혀볼 수 있는 곡입니다."
    return f"{genre_text} 취향과 {mood_text} 분위기에 맞춰 고른 곡입니다."
```

- [ ] **Step 4: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_agent_and_detail_flow.py tests/test_response_generator_fallback.py -v
```

Expected: pass.

---

### Task 6: Display Reason LLM Postprocess And Validator

**Files:**
- Create: `app/validators/display_reason_validator.py`
- Modify: `app/agents/response_generator.py`
- Test: `tests/test_display_reason_validator.py`
- Test: `tests/test_response_generator_fallback.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_display_reason_validator.py`:

```python
from app.validators.display_reason_validator import DisplayReasonValidator


def test_display_reason_validator_rejects_raw_evidence_copy():
    result = DisplayReasonValidator().validate(
        display_reason="raw lyrics line raw lyrics line",
        source_item={"evidence_summary": "raw lyrics line raw lyrics line", "title": "Song", "artist": "Artist"},
    )

    assert not result["passed"]


def test_display_reason_validator_accepts_short_metadata_based_reason():
    result = DisplayReasonValidator().validate(
        display_reason="indie 취향과 calm 분위기에 맞춰 고른 곡입니다.",
        source_item={"evidence_summary": "very long raw document", "title": "Song", "artist": "Artist"},
    )

    assert result["passed"]
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_display_reason_validator.py -v
```

Expected: fail because validator does not exist.

- [ ] **Step 3: Implement validator**

Create:

```python
class DisplayReasonValidator:
    def validate(self, display_reason: str, source_item: dict) -> dict:
        reason = (display_reason or "").strip()
        if not reason:
            return {"passed": False, "errors": ["display_reason is empty"]}
        if len(reason) > 160:
            return {"passed": False, "errors": ["display_reason is too long"]}

        raw = str(source_item.get("evidence_summary") or "").strip()
        if raw and reason == raw:
            return {"passed": False, "errors": ["display_reason copies evidence_summary"]}
        if raw and len(raw) >= 20 and raw[:40] in reason:
            return {"passed": False, "errors": ["display_reason includes raw evidence"]}

        return {"passed": True, "errors": []}
```

- [ ] **Step 4: Update response generator fallback path**

In `ResponseGenerator._build_local_response()`, keep selected `display_reason` if validator passes. Otherwise rebuild using `build_display_reason()`.

LLM postprocess must not alter `content_id`, `title`, `artist`. If the LLM response fails existing response/provenance validation later, orchestrator fallback applies.

- [ ] **Step 5: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_display_reason_validator.py tests/test_response_generator_fallback.py -v
```

Expected: pass.

---

### Task 7: Main Recommendation Section Dedup And Fallback

**Files:**
- Modify: `app/repositories/query_constants.py`
- Modify: `app/repositories/music_catalog_repository.py`
- Modify: `app/services/main_recommendation_service.py`
- Test: `tests/test_main_recommendation_service.py`
- Test: `tests/test_rdb_repositories.py`

- [ ] **Step 1: Write failing service test**

Add to `tests/test_main_recommendation_service.py`:

```python
def test_main_recommendation_service_deduplicates_and_fills_sections(monkeypatch):
    class StubRepo:
        def find_fallback_new_releases(self, limit, excluded_content_ids, excluded_artists):
            return [{"content_id": "new_001", "title": "New", "artist": "Fresh", "album": "", "genres": ["indie"], "moods": ["bright"], "evidence_summary": "new"}]

        def find_fallback_discovery(self, limit, preferred_genres, excluded_content_ids, excluded_artists):
            return [{"content_id": "disc_001", "title": "Discover", "artist": "Wide", "album": "", "genres": ["ambient"], "moods": ["calm"], "evidence_summary": "discover"}]

    view_model = MainRecommendationService._build_view_model(
        user_id="user_001",
        session_context={"disliked_artists": [], "disliked_tracks": [], "recent_genres": ["indie"], "recent_moods": []},
        kag_state={},
        rag_state={"recommended_content_evidence": [
            {"content_id": "track_001", "title": "Same", "artist": "A", "genre": ["indie"], "mood": ["calm"], "recommendation_category": "personalized_match", "evidence_summary": "raw"},
            {"content_id": "track_001", "title": "Same", "artist": "A", "genre": ["indie"], "mood": ["calm"], "recommendation_category": "personalized_match", "evidence_summary": "raw"},
        ]},
        latency_ms=1.0,
        catalog_repository=StubRepo(),
    )

    assert len(view_model["personalized"]) == 1
    assert view_model["new_release"]
    assert view_model["discovery"]
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_main_recommendation_service.py::test_main_recommendation_service_deduplicates_and_fills_sections -v
```

Expected: fail because repository injection/fallback is missing.

- [ ] **Step 3: Add fallback SQL and repository methods**

Add constants:

```python
SELECT_FALLBACK_NEW_RELEASES = """
SELECT *
FROM music_catalog
WHERE release_type = 'new_release'
  AND NOT (content_id = ANY(%(excluded_content_ids)s))
  AND NOT (artist = ANY(%(excluded_artists)s))
ORDER BY created_at DESC, content_id ASC
LIMIT %(limit)s;
"""

SELECT_FALLBACK_DISCOVERY = """
SELECT *
FROM music_catalog
WHERE recommendation_category = 'discovery_candidate'
  AND NOT (content_id = ANY(%(excluded_content_ids)s))
  AND NOT (artist = ANY(%(excluded_artists)s))
ORDER BY created_at DESC, content_id ASC
LIMIT %(limit)s;
"""
```

Add repository methods:

```python
def find_fallback_new_releases(self, limit, excluded_content_ids, excluded_artists):
    return self._fetch_all(query_constants.SELECT_FALLBACK_NEW_RELEASES, {
        "limit": limit,
        "excluded_content_ids": excluded_content_ids or [],
        "excluded_artists": excluded_artists or [],
    })

def find_fallback_discovery(self, limit, preferred_genres, excluded_content_ids, excluded_artists):
    return self._fetch_all(query_constants.SELECT_FALLBACK_DISCOVERY, {
        "limit": limit,
        "preferred_genres": preferred_genres or [],
        "excluded_content_ids": excluded_content_ids or [],
        "excluded_artists": excluded_artists or [],
    })
```

- [ ] **Step 4: Implement service dedup and fallback**

Update `_build_view_model()` to accept optional `catalog_repository=None`.

Build `used_content_ids` set globally across sections. Skip duplicates and disliked items.

If `groups["new_release"]` is empty and repository exists, fill from `find_fallback_new_releases()`.

If `groups["discovery"]` is empty and repository exists, fill from `find_fallback_discovery()`.

- [ ] **Step 5: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_main_recommendation_service.py tests/test_rdb_repositories.py -v
```

Expected: pass.

---

### Task 8: Orchestrator And Chatbot Service Negative Preference Save

**Files:**
- Modify: `app/agents/orchestrator_agent.py`
- Modify: `app/services/chatbot_service.py`
- Modify: `app/services/session_cache_service.py`
- Modify: `app/cache/session_history_cache.py`
- Test: `tests/test_chatbot_service.py`

- [ ] **Step 1: Write failing service test**

Add:

```python
def test_chatbot_service_saves_new_negative_preferences_to_context(monkeypatch):
    saved = {}

    class StubOrchestrator:
        def run_chatbot(self, user_id, session_id, user_input, session_context):
            return {
                "status": "success",
                "response_type": "curator_recommendation",
                "chatbot_response": "반영했습니다.",
                "display_recommendations": [],
                "used_content_ids": [],
                "_meta": {
                    "kag_state": {},
                    "rag_state": {},
                    "latency_ms": 1.0,
                    "new_dislikes": {"disliked_artists": ["Billie Eilish"], "disliked_tracks": []},
                },
            }

    def fake_save_turn_and_update_context(**kwargs):
        saved.update(kwargs)
        return {}

    monkeypatch.setattr("app.services.chatbot_service.session_cache_service.save_turn_and_update_context", fake_save_turn_and_update_context)

    ChatbotService(orchestrator=StubOrchestrator()).submit_message("user_001", "session_001", "Billie Eilish 싫어")

    assert saved["new_dislikes"]["disliked_artists"] == ["Billie Eilish"]
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_chatbot_service.py::test_chatbot_service_saves_new_negative_preferences_to_context -v
```

Expected: fail because `new_dislikes` is not passed.

- [ ] **Step 3: Wire metadata through orchestrator**

In `OrchestratorAgent.run_chatbot()`, include:

```python
"new_dislikes": {
    "disliked_artists": intent_state.get("disliked_artists", []),
    "disliked_tracks": intent_state.get("disliked_tracks", []),
}
```

inside `_meta`.

- [ ] **Step 4: Update context save path**

Update `ChatbotService.submit_message()`:

```python
new_dislikes = meta.get("new_dislikes", {"disliked_artists": [], "disliked_tracks": []})
```

Pass to `save_turn_and_update_context()`.

Update `session_cache_service.save_turn_and_update_context()` and `session_history_cache.update_context_from_turn()` to accept `new_dislikes`.

Merge into context:

```python
ctx["disliked_artists"] = _merge_recent(ctx.get("disliked_artists", []), new_dislikes.get("disliked_artists", []), limit=50)
ctx["disliked_tracks"] = _merge_recent(ctx.get("disliked_tracks", []), new_dislikes.get("disliked_tracks", []), limit=50)
```

- [ ] **Step 5: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_chatbot_service.py tests/test_session_context_hydration.py -v
```

Expected: pass.

---

### Task 9: Policy Documents And Final Verification

**Files:**
- Modify: `docs/policies/RecommendationPolicy.md`
- Modify: `docs/policies/RankingPolicy.md`
- Modify: `docs/policies/PromptPolicy.md`
- Test: targeted pytest suite

- [ ] **Step 1: Update RecommendationPolicy**

Add rules:

```markdown
- disliked track은 최종 추천에서 제외한다.
- disliked artist는 최종 추천에서 제외한다.
- 같은 content_id는 최종 추천에서 한 번만 노출한다.
- requested_count가 있으면 최종 추천 개수에 반영한다.
```

- [ ] **Step 2: Update RankingPolicy**

Add rules:

```markdown
- excluded candidate는 ranking 대상에 들어가기 전에 제거한다.
- dedup은 최종 slice 전에 수행한다.
- section fallback은 기존 content_id와 중복되면 안 된다.
```

- [ ] **Step 3: Update PromptPolicy**

Add rules:

```markdown
- LLM은 display_reason의 곡, 아티스트, content_id를 변경하지 않는다.
- LLM은 raw evidence_summary, lyrics, Elasticsearch document를 그대로 복사하지 않는다.
- LLM display_reason 결과는 validator 통과 시에만 사용자 응답에 사용한다.
```

- [ ] **Step 4: Run targeted backend suite**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_runtime_contracts.py tests/test_v4_infra_contract.py tests/test_negative_preference_repository.py tests/test_session_context_hydration.py tests/test_v4_agent_and_detail_flow.py tests/test_mock_kag_adapter.py tests/test_real_kag_adapter.py tests/test_mock_rag_adapter.py tests/test_real_rag_adapter.py tests/test_main_recommendation_service.py tests/test_response_generator_fallback.py tests/test_display_reason_validator.py tests/test_chatbot_service.py -v
```

Expected: pass.

- [ ] **Step 5: Run broader regression suite**

Run:

```powershell
C:\Python314\python.exe -m pytest tests -v
```

Expected: pass. If external services are unavailable, record exact failed tests and whether failures are environment-bound.

---

## Self-Review

Spec coverage:

- 부정 취향 영구 저장: Task 1, Task 2, Task 8.
- 추천 제외: Task 3, Task 4, Task 5.
- 중복 content_id 제거: Task 5, Task 7.
- 요청 곡 수 반영: Task 3, Task 5.
- 빈 new_release/discovery 섹션 fallback: Task 7.
- raw evidence 추천 이유 노출 방지: Task 5, Task 6.
- 정책 문서 갱신: Task 9.

Placeholder scan:

- No `TBD`, `TODO`, or open placeholders are intentionally left.

Type consistency:

- `disliked_artists`, `disliked_tracks` are `list[str]`.
- `requested_count` is `int | None`.
- KAG constraints use `excluded_artists`, `excluded_tracks`.
- KAG trace uses `excluded_nodes`.
- DB persistence uses `user_negative_preferences`.
