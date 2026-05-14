# Chatbot Taste Feedback Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit chatbot recommendation taste feedback, Redis-first session taste state, DB flush/hydration, and safe UI streaming based on validated `response_state.chatbot_response`.

**Architecture:** Keep existing non-streaming chatbot and recommendation contracts intact. Add focused services for taste events, taste profile persistence, session context hydration, and UI streaming while reusing existing Redis/session/repository patterns. Long-term taste profiles only hydrate `SESSION_CONTEXT`; KAG/RAG still produce recommendation candidates and evidence.

**Tech Stack:** FastAPI, Pydantic, Redis helper wrappers, PostgreSQL SQL constants/repositories, React + Zustand + React Query, pytest.

---

## File Structure

- Modify `app/schemas/session_context_schema.py`: add optional `selected_tracks`.
- Modify `app/contracts/fields.py`: add `SELECTED_TRACKS` session context field.
- Modify `app/cache/redis_keys.py`: add taste event Redis key.
- Modify `app/cache/session_history_cache.py`: support `selected_tracks`, context hydration, and taste event append/read/clear.
- Modify `app/services/session_cache_service.py`: accept `user_id` when loading context.
- Create `app/repositories/taste_profile_repository.py`: DB operations for taste events and profiles.
- Modify `app/repositories/query_constants.py`: SQL constants for taste event/profile persistence and lookup.
- Modify `db/schema.sql`: add `user_taste_events` and `user_taste_profiles`.
- Create `app/services/session_context_hydration_service.py`: build Redis context from DB profile on cache miss.
- Create `app/services/taste_event_service.py`: validate and record `add_to_taste` events.
- Create `app/api/taste_routes.py`: `POST /api/taste/events`.
- Modify `app/main.py`: include taste router.
- Modify `app/services/session_flush_service.py`: flush taste events and upsert taste profile transactionally.
- Modify `app/services/chatbot_service.py`: pass `user_id` into context loading.
- Modify `app/services/main_recommendation_service.py`: pass `user_id` into context loading.
- Modify `app/api/chatbot_routes.py`: add `/respond/stream` endpoint.
- Create `app/services/chatbot_stream_service.py`: validated response-state UI streaming.
- Modify `frontend/src/types/index.ts`: add taste event/flush response types as needed.
- Modify `frontend/src/api/chatbot.ts`: add streaming and clear/flush helpers.
- Create `frontend/src/api/taste.ts`: taste event API client.
- Modify `frontend/src/stores/chatStore.ts`: support streaming placeholder/update/finalize.
- Modify `frontend/src/stores/sessionStore.ts`: ensure `resetSession()` is used after session end.
- Modify `frontend/src/pages/ChatbotPage.tsx`: use streaming send and home navigation confirm.
- Modify `frontend/src/pages/MainRecommendationPage.tsx`: pass taste action props into detail modal.
- Modify `frontend/src/components/recommendation/MusicDetailModal.tsx`: add `내 취향에 추가` button and states.
- Add/update tests in `tests/test_redis_keys.py`, `tests/test_v4_runtime_contracts.py`, `tests/test_taste_event_service.py`, `tests/test_session_flush_service.py`, `tests/test_request_lifecycle_routes.py`, and frontend tests if available.

---

### Task 1: SESSION_CONTEXT Contract And Redis Taste Event Key

**Files:**
- Modify: `app/schemas/session_context_schema.py`
- Modify: `app/contracts/fields.py`
- Modify: `app/cache/redis_keys.py`
- Modify: `app/cache/session_history_cache.py`
- Test: `tests/test_redis_keys.py`
- Test: `tests/test_v4_runtime_contracts.py`

- [ ] **Step 1: Write failing contract tests**

Add tests:

```python
def test_session_context_schema_accepts_selected_tracks():
    from app.schemas.session_context_schema import SessionContextSchema

    ctx = SessionContextSchema(
        session_id="session_001",
        recent_genres=["indie"],
        recent_artists=["Nova Lane"],
        recent_moods=["night"],
        selected_tracks=["track_001"],
    )

    assert ctx.model_dump()["selected_tracks"] == ["track_001"]
```

```python
def test_taste_events_key_contract():
    from app.cache.redis_keys import taste_events_key

    assert taste_events_key("session_001") == "rimas:session:session_001:taste_events"
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_runtime_contracts.py::test_session_context_schema_accepts_selected_tracks tests/test_redis_keys.py::test_taste_events_key_contract -v
```

Expected: fail because `selected_tracks` and `taste_events_key` are missing.

- [ ] **Step 3: Implement contract changes**

Update `SessionContextSchema`:

```python
class SessionContextSchema(BaseModel):
    session_id: str
    recent_genres: list[str] = Field(default_factory=list)
    recent_artists: list[str] = Field(default_factory=list)
    recent_moods: list[str] = Field(default_factory=list)
    selected_tracks: list[str] = Field(default_factory=list)
    conversation_summary: str = ""
```

Add `SELECTED_TRACKS = "selected_tracks"` to `SessionContextField`.

Add Redis key:

```python
def taste_events_key(session_id: str) -> str:
    return f"{_session_prefix(session_id)}:taste_events"
```

Update `_empty_context()`:

```python
return {
    "session_id": session_id,
    "recent_genres": [],
    "recent_artists": [],
    "recent_moods": [],
    "selected_tracks": [],
    "conversation_summary": "",
}
```

- [ ] **Step 4: Run tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_runtime_contracts.py tests/test_redis_keys.py -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add app/schemas/session_context_schema.py app/contracts/fields.py app/cache/redis_keys.py app/cache/session_history_cache.py tests/test_v4_runtime_contracts.py tests/test_redis_keys.py
git commit -m "feat: extend session context taste contract"
```

---

### Task 2: DB Schema And Taste Profile Repository

**Files:**
- Modify: `db/schema.sql`
- Modify: `app/repositories/query_constants.py`
- Create: `app/repositories/taste_profile_repository.py`
- Test: `tests/test_v4_infra_contract.py`
- Test: `tests/test_rdb_repositories.py`

- [ ] **Step 1: Write failing schema tests**

Add checks that `db/schema.sql` contains:

```python
assert "CREATE TABLE IF NOT EXISTS user_taste_events" in sql
assert "CREATE TABLE IF NOT EXISTS user_taste_profiles" in sql
assert "idx_user_taste_events_user_created_at" in sql
assert "idx_user_taste_profiles_updated_at" in sql
```

- [ ] **Step 2: Write failing repository tests**

Add fake cursor tests:

```python
def test_taste_profile_repository_saves_event_and_upserts_profile():
    repo = TasteProfileRepository(FakeConnection())
    event = {
        "event_id": "evt_001",
        "user_id": "user_001",
        "session_id": "session_001",
        "content_id": "track_001",
        "event_type": "add_to_taste",
        "source": "music_detail_modal",
        "title": "Midnight Loop",
        "artist": "Nova Lane",
        "genre": ["indie"],
        "mood": ["night"],
        "recommendation_category": "discovery_candidate",
        "created_at": "2026-05-14T00:00:00+00:00",
    }

    repo.insert_event(event)
    repo.upsert_profile(
        user_id="user_001",
        preferred_genres=["indie"],
        preferred_moods=["night"],
        preferred_artists=["Nova Lane"],
        selected_content_ids=["track_001"],
    )

    assert repo._connection.committed
```

- [ ] **Step 3: Run failing tests**

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_infra_contract.py tests/test_rdb_repositories.py -v
```

Expected: fail on missing schema/repository.

- [ ] **Step 4: Implement schema and SQL constants**

Add two tables:

```sql
CREATE TABLE IF NOT EXISTS user_taste_events (
    event_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    session_id VARCHAR(100),
    content_id VARCHAR(140) NOT NULL REFERENCES music_catalog(content_id),
    event_type VARCHAR(64) NOT NULL,
    source VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    genre_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    mood_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    recommendation_category VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_user_taste_events_event_type
        CHECK (event_type IN ('add_to_taste'))
);

CREATE TABLE IF NOT EXISTS user_taste_profiles (
    user_id VARCHAR(64) PRIMARY KEY REFERENCES users(user_id),
    preferred_genres_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    preferred_moods_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    preferred_artists_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    selected_content_ids_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Add indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_user_taste_events_user_created_at
ON user_taste_events(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_taste_events_session_created_at
ON user_taste_events(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_taste_profiles_updated_at
ON user_taste_profiles(updated_at DESC);
```

- [ ] **Step 5: Implement repository**

Use `psycopg2.extras.Json` pattern from `InteractionLogRepository` for JSON fields. Provide:

```python
class TasteProfileRepository(BaseRepository):
    def insert_event(self, event: dict) -> str:
        self._validate_event(event)
        params = self._prepare_event_params(event)
        with self._connection.cursor() as cursor:
            cursor.execute(query_constants.INSERT_USER_TASTE_EVENT, params)
        self._connection.commit()
        return event["event_id"]

    def upsert_profile(
        self,
        *,
        user_id: str,
        preferred_genres: list[str],
        preferred_moods: list[str],
        preferred_artists: list[str],
        selected_content_ids: list[str],
    ) -> str:
        if not user_id:
            raise ValueError("user_id is required")
        params = self._prepare_profile_params(
            user_id=user_id,
            preferred_genres=preferred_genres,
            preferred_moods=preferred_moods,
            preferred_artists=preferred_artists,
            selected_content_ids=selected_content_ids,
        )
        with self._connection.cursor() as cursor:
            cursor.execute(query_constants.UPSERT_USER_TASTE_PROFILE, params)
        self._connection.commit()
        return user_id

    def find_profile(self, user_id: str) -> dict | None:
        if not user_id:
            raise ValueError("user_id is required")
        with self._cursor() as cursor:
            cursor.execute(query_constants.SELECT_USER_TASTE_PROFILE, {"user_id": user_id})
            return cursor.fetchone()
```

- [ ] **Step 6: Run tests**

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_infra_contract.py tests/test_rdb_repositories.py -v
```

Expected: pass.

- [ ] **Step 7: Commit**

```powershell
git add db/schema.sql app/repositories/query_constants.py app/repositories/taste_profile_repository.py tests/test_v4_infra_contract.py tests/test_rdb_repositories.py
git commit -m "feat: add taste profile persistence contract"
```

---

### Task 3: Session Context Hydration From DB Profile

**Files:**
- Create: `app/services/session_context_hydration_service.py`
- Modify: `app/cache/session_history_cache.py`
- Modify: `app/services/session_cache_service.py`
- Modify: `app/services/chatbot_service.py`
- Modify: `app/services/main_recommendation_service.py`
- Test: `tests/test_session_context_hydration.py`
- Test: `tests/test_chatbot_service.py`
- Test: `tests/test_main_recommendation_service.py`

- [ ] **Step 1: Write failing hydration tests**

```python
def test_hydration_builds_context_from_profile():
    class Repo:
        def find_profile(self, user_id):
            return {
                "user_id": user_id,
                "preferred_genres_json": ["indie"],
                "preferred_moods_json": ["night"],
                "preferred_artists_json": ["Nova Lane"],
                "selected_content_ids_json": ["track_001"],
            }

    ctx = SessionContextHydrationService(repository=Repo()).hydrate(
        user_id="user_001",
        session_id="session_001",
    )

    assert ctx["recent_genres"] == ["indie"]
    assert ctx["recent_moods"] == ["night"]
    assert ctx["recent_artists"] == ["Nova Lane"]
    assert ctx["selected_tracks"] == ["track_001"]
```

- [ ] **Step 2: Run failing test**

```powershell
C:\Python314\python.exe -m pytest tests/test_session_context_hydration.py -v
```

Expected: fail because service is missing.

- [ ] **Step 3: Implement hydration service**

```python
class SessionContextHydrationService:
    def __init__(self, repository=None):
        self._repository = repository

    def hydrate(self, user_id: str, session_id: str) -> dict:
        profile = self._repository.find_profile(user_id) if self._repository else None
        if not profile:
            return _empty_context_shape(session_id)
        return {
            "session_id": session_id,
            "recent_genres": list(profile.get("preferred_genres_json") or [])[:5],
            "recent_artists": list(profile.get("preferred_artists_json") or [])[:5],
            "recent_moods": list(profile.get("preferred_moods_json") or [])[:5],
            "selected_tracks": list(profile.get("selected_content_ids_json") or [])[:20],
            "conversation_summary": "",
        }
```

- [ ] **Step 4: Update context loading path**

Change `session_cache_service.load_context(session_id)` to:

```python
def load_context(session_id: str, user_id: str | None = None) -> dict:
    return cache.get_context(session_id, user_id=user_id)
```

Update `ChatbotService` and `MainRecommendationService` to pass `user_id`.

- [ ] **Step 5: Run targeted tests**

```powershell
C:\Python314\python.exe -m pytest tests/test_session_context_hydration.py tests/test_chatbot_service.py tests/test_main_recommendation_service.py -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add app/services/session_context_hydration_service.py app/cache/session_history_cache.py app/services/session_cache_service.py app/services/chatbot_service.py app/services/main_recommendation_service.py tests/test_session_context_hydration.py tests/test_chatbot_service.py tests/test_main_recommendation_service.py
git commit -m "feat: hydrate session context from taste profile"
```

---

### Task 4: Taste Event API And Redis Context Update

**Files:**
- Create: `app/services/taste_event_service.py`
- Create: `app/api/taste_routes.py`
- Modify: `app/main.py`
- Modify: `app/cache/session_history_cache.py`
- Modify: `app/services/session_cache_service.py`
- Test: `tests/test_taste_event_service.py`
- Test: `tests/test_request_lifecycle_routes.py`

- [ ] **Step 1: Write failing service test**

```python
def test_taste_event_service_updates_context_and_appends_event():
    cache = StubSessionCache()
    detail_service = StubDetailService(
        {
            "content_id": "track_001",
            "title": "Midnight Loop",
            "artist": "Nova Lane",
            "genre": ["indie"],
            "mood": ["night"],
            "display_reason": "근거",
            "evidence_summary": "근거",
            "source": "rag",
        }
    )

    result = TasteEventService(
        detail_service=detail_service,
        session_cache=cache,
    ).add_to_taste(
        user_id="user_001",
        session_id="session_001",
        content_id="track_001",
        source="music_detail_modal",
    )

    assert result["status"] == "success"
    assert result["session_context"]["recent_genres"] == ["indie"]
    assert result["session_context"]["selected_tracks"] == ["track_001"]
    assert cache.events[0]["event_type"] == "add_to_taste"
```

- [ ] **Step 2: Run failing test**

```powershell
C:\Python314\python.exe -m pytest tests/test_taste_event_service.py -v
```

Expected: fail because service is missing.

- [ ] **Step 3: Implement service**

Implement `add_to_taste()` with explicit validation:

```python
if not user_id:
    raise ValueError("user_id is required")
if not session_id:
    raise ValueError("session_id is required")
if not content_id:
    raise ValueError("content_id is required")
```

Use `MusicDetailService.get_detail(content_id, recent_rag_state)` for metadata. Merge arrays with existing `_merge_recent` behavior. Create event id with `uuid4`.

- [ ] **Step 4: Implement route**

```python
@router.post("/events")
def add_taste_event(req: TasteEventRequest):
    try:
        return _service.add_to_taste(
            user_id=req.user_id,
            session_id=req.session_id,
            content_id=req.content_id,
            source=req.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

Include router in `app/main.py`:

```python
app.include_router(taste_router, prefix="/api/taste", tags=["taste"])
```

- [ ] **Step 5: Run tests**

```powershell
C:\Python314\python.exe -m pytest tests/test_taste_event_service.py tests/test_request_lifecycle_routes.py -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add app/services/taste_event_service.py app/api/taste_routes.py app/main.py app/cache/session_history_cache.py app/services/session_cache_service.py tests/test_taste_event_service.py tests/test_request_lifecycle_routes.py
git commit -m "feat: add taste event api"
```

---

### Task 5: Flush Taste Events And Profile Summary

**Files:**
- Modify: `app/services/session_flush_service.py`
- Modify: `app/cache/session_history_cache.py`
- Test: `tests/test_session_flush_service.py`
- Test: `tests/test_service_query_policy.py`

- [ ] **Step 1: Write failing flush tests**

```python
def test_flush_writes_taste_events_and_profile_before_clearing_cache(monkeypatch):
    cache = StubCache(
        history=[{"user_input": "hi", "chatbot_response": "hello", "created_at": "2026-05-14T00:00:00+00:00"}],
        taste_events=[
            {
                "event_id": "evt_001",
                "user_id": "user_001",
                "session_id": "session_001",
                "content_id": "track_001",
                "event_type": "add_to_taste",
                "source": "music_detail_modal",
                "title": "Midnight Loop",
                "artist": "Nova Lane",
                "genre": ["indie"],
                "mood": ["night"],
                "recommendation_category": "discovery_candidate",
                "created_at": "2026-05-14T00:00:00+00:00",
            }
        ],
    )

    result = flush_session("session_001", "user_001")

    assert result["flushed"] == 1
    assert result["taste_events_flushed"] == 1
```

- [ ] **Step 2: Run failing test**

```powershell
C:\Python314\python.exe -m pytest tests/test_session_flush_service.py -v
```

Expected: fail because taste event flush is missing.

- [ ] **Step 3: Implement cache helpers**

Add:

```python
def append_taste_event(session_id: str, event: dict) -> None:
    key = taste_events_key(session_id)
    redis_client.cache_lpush(key, event, ttl=REDIS_SESSION_TTL)


def get_taste_events(session_id: str) -> list[dict]:
    key = taste_events_key(session_id)
    items = redis_client.cache_lrange(key, 0, _MAX_HISTORY - 1)
    return list(reversed(items))


def clear_taste_events(session_id: str) -> None:
    redis_client.cache_delete(taste_events_key(session_id))
```

- [ ] **Step 4: Extend flush transaction**

Inside `_write_to_db`, insert taste events and upsert profile after chat turns. Build summary lists from event genre/mood/artist/content_id using stable de-duplication:

```python
def _unique(values: list[str], limit: int) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result[:limit]
```

- [ ] **Step 5: Run tests**

```powershell
C:\Python314\python.exe -m pytest tests/test_session_flush_service.py tests/test_service_query_policy.py -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add app/services/session_flush_service.py app/cache/session_history_cache.py tests/test_session_flush_service.py tests/test_service_query_policy.py
git commit -m "feat: flush taste events with sessions"
```

---

### Task 6: Safe UI Streaming Endpoint

**Files:**
- Create: `app/services/chatbot_stream_service.py`
- Modify: `app/api/chatbot_routes.py`
- Test: `tests/test_chatbot_stream_service.py`
- Test: `tests/test_request_lifecycle_routes.py`

- [ ] **Step 1: Write failing stream service test**

```python
def test_stream_service_chunks_validated_response_after_service_result():
    service = ChatbotStreamService(
        chatbot_service=StubChatbotService(
            {
                "status": "success",
                "response_state": {
                    "status": "success",
                    "response_type": "curator_recommendation",
                    "chatbot_response": "안녕하세요 추천입니다.",
                    "display_recommendations": [],
                    "used_content_ids": [],
                },
                "latency_ms": 12.3,
            }
        )
    )

    events = list(service.stream_response("user_001", "session_001", "추천해줘"))

    assert events[0]["event"] == "delta"
    assert "".join(e["data"]["text"] for e in events if e["event"] == "delta") == "안녕하세요 추천입니다."
    assert events[-2]["event"] == "final"
    assert events[-1]["event"] == "done"
```

- [ ] **Step 2: Run failing test**

```powershell
C:\Python314\python.exe -m pytest tests/test_chatbot_stream_service.py -v
```

Expected: fail because service is missing.

- [ ] **Step 3: Implement stream service**

Generate event dicts first; route formats them as SSE.

```python
def _chunk_text(text: str, chunk_size: int = 12) -> list[str]:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
```

Do not stream before `ChatbotService.submit_message()` returns validated final state.

- [ ] **Step 4: Add route**

Use FastAPI `StreamingResponse`:

```python
return StreamingResponse(
    _to_sse(
        _stream_service.stream_response(
            user_id=req.user_id,
            session_id=req.session_id,
            user_input=req.user_input,
        )
    ),
    media_type="text/event-stream",
)
```

Format:

```python
yield f"event: {event['event']}\n"
yield f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
```

- [ ] **Step 5: Run tests**

```powershell
C:\Python314\python.exe -m pytest tests/test_chatbot_stream_service.py tests/test_request_lifecycle_routes.py tests/test_chatbot_service.py -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add app/services/chatbot_stream_service.py app/api/chatbot_routes.py tests/test_chatbot_stream_service.py tests/test_request_lifecycle_routes.py
git commit -m "feat: add safe chatbot ui streaming"
```

---

### Task 7: Frontend Taste Button, Session-End Confirm, And Streaming Send

**Files:**
- Modify: `frontend/src/api/chatbot.ts`
- Create: `frontend/src/api/taste.ts`
- Modify: `frontend/src/stores/chatStore.ts`
- Modify: `frontend/src/pages/ChatbotPage.tsx`
- Modify: `frontend/src/pages/MainRecommendationPage.tsx`
- Modify: `frontend/src/components/recommendation/MusicDetailModal.tsx`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add API clients**

Add `addToTaste()`:

```ts
export async function addToTaste(params: {
  userId: string;
  sessionId: string;
  contentId: string;
  requestId: string;
}) {
  const res = await apiClient.post("/api/taste/events", {
    user_id: params.userId,
    session_id: params.sessionId,
    content_id: params.contentId,
    event_type: "add_to_taste",
    source: "music_detail_modal",
    request_id: params.requestId,
  });
  return res.data;
}
```

Add `sendChatMessageStream()` using `fetch()` and `ReadableStream` parsing for SSE. Keep existing `sendChatMessage()` intact.

- [ ] **Step 2: Extend chat store**

Add actions:

```ts
appendUserTurn(userInput: string): void;
appendAssistantPlaceholder(userInput: string): void;
appendAssistantDelta(delta: string): void;
finalizeAssistantTurn(displayRecommendations: ChatDisplayRecommendation[]): void;
replaceLastAssistantMessage(message: string): void;
```

Preserve existing `appendTurn()` for non-streaming callers.

- [ ] **Step 3: Add taste button to modal**

`MusicDetailModal` props:

```ts
onAddToTaste?: (contentId: string) => Promise<void>;
isTasteSaving?: boolean;
isTasteAdded?: boolean;
```

Button text:

- default: `내 취향에 추가`
- saving: `추가 중...`
- added: `취향에 추가됨`

- [ ] **Step 4: Wire modal action**

In `MainRecommendationPage`, call `addToTaste()` with current `userId`, `sessionId`, `detailContentId`, generated request id. Track added ids in component state to prevent repeat adds per page lifetime.

- [ ] **Step 5: Add home navigation confirm**

In `App.tsx` or `ChatbotPage` navigation boundary, when current page is `chatbot` and target is `home`, show confirm modal with:

- `저장하고 종료`
- `저장하지 않고 이동`
- `취소`

`저장하고 종료`: call `flushSession(sessionId, userId)`, clear chat store, reset session, navigate home.  
`저장하지 않고 이동`: call `clearSession(sessionId)`, clear chat store, reset session, navigate home.  
`취소`: close modal.

- [ ] **Step 6: Run frontend checks**

```powershell
cd frontend
npm run build
```

Expected: build succeeds.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/api/chatbot.ts frontend/src/api/taste.ts frontend/src/stores/chatStore.ts frontend/src/pages/ChatbotPage.tsx frontend/src/pages/MainRecommendationPage.tsx frontend/src/components/recommendation/MusicDetailModal.tsx frontend/src/types/index.ts frontend/src/App.tsx
git commit -m "feat: add taste feedback streaming ui"
```

---

### Task 8: End-To-End Verification

**Files:**
- No new files unless tests reveal focused gaps.

- [ ] **Step 1: Run backend targeted suite**

```powershell
C:\Python314\python.exe -m pytest tests/test_v4_runtime_contracts.py tests/test_redis_keys.py tests/test_taste_event_service.py tests/test_session_context_hydration.py tests/test_session_flush_service.py tests/test_chatbot_stream_service.py tests/test_request_lifecycle_routes.py tests/test_chatbot_service.py tests/test_main_recommendation_service.py -v
```

Expected: pass.

- [ ] **Step 2: Run frontend build**

```powershell
cd frontend
npm run build
```

Expected: pass.

- [ ] **Step 3: Optional local manual smoke**

Start backend/frontend only if requested or already part of the active dev workflow. Smoke flow:

1. Open chatbot.
2. Send message.
3. Confirm assistant text appears incrementally.
4. Open recommendation detail.
5. Click `내 취향에 추가`.
6. Navigate home.
7. Choose `저장하고 종료`.
8. Confirm new `sessionId` is generated.

- [ ] **Step 4: Commit verification-only fixes**

If verification requires small fixes, commit them:

```powershell
git status --short
git add app tests frontend/src
git commit -m "fix: stabilize taste feedback streaming flow"
```

---

## Self-Review

Spec coverage:

- `내 취향에 추가`: Task 4 and Task 7.
- Redis taste events and context update: Task 1, Task 4, Task 5.
- DB event/profile persistence: Task 2 and Task 5.
- Next-session profile hydration: Task 3.
- Home navigation save/discard/cancel: Task 7.
- Safe UI streaming from validated `response_state.chatbot_response`: Task 6 and Task 7.
- Existing `/api/chatbot/respond` compatibility: Task 6 and Task 8.

Placeholder scan:

- No `TBD`, `TODO`, or open implementation placeholders are intentionally left.

Type consistency:

- Redis key name: `taste_events_key(session_id)`.
- Event type: `add_to_taste`.
- Session field: `selected_tracks`.
- DB tables: `user_taste_events`, `user_taste_profiles`.
- Stream events: `delta`, `final`, `done`, `error`.
