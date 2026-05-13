# KAG/RAG Real Adapter Start Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** KAG Real Adapter의 Neo4j 연결·쿼리 선택·KAG_STATE 매핑을 먼저 구현하고, RAG Real 전환 지점의 기준을 명확히 잡는다.

**Architecture:** 문서상 즉시 수정 가능한 `app/kag/**`를 먼저 구현한다. 사용자가 승인한 범위 안에서 Dispatch Agent의 Mock/Real 선택은 환경변수 기반으로 최소 변경한다.

**Tech Stack:** Python 3.12+, FastAPI app package, pytest, Neo4j Python driver.

---

### Task 1: Real KAG Adapter 단위 구현

**Files:**
- Modify: `app/kag/connection.py`
- Modify: `app/kag/constant.py`
- Modify: `app/kag/adapters/real_kag_adapter.py`
- Test: `tests/test_real_kag_adapter.py`

- [x] **Step 1: Write failing tests**

```python
def test_real_kag_adapter_maps_neo4j_rows_to_kag_state():
    conn = StubNeo4jConnection([...])
    state = RealKagAdapter(conn=conn).build_state("user_001", "indie 추천", {"recent_genres": ["indie"]})
    assert state["recommended_content_ids"] == ["track_001"]
```

- [x] **Step 2: Run test to verify it fails**

Run: `C:\Python314\python.exe -m pytest tests/test_real_kag_adapter.py -v`
Expected: FAIL because RealKagAdapter does not return a KAG_STATE.

- [x] **Step 3: Implement minimal adapter behavior**

Implement deterministic query selection, row mapping, empty-result degraded success, and `RIMAS_NEO4J_*` env fallback in the KAG connection module.

- [x] **Step 4: Run test to verify it passes**

Run: `C:\Python314\python.exe -m pytest tests/test_real_kag_adapter.py -v`
Expected: PASS.

### Task 2: Dispatch 선택 경로 연결

**Files:**
- Modify: `app/agents/kag_dispatch_agent.py`
- Modify: `app/agents/rag_dispatch_agent.py`
- Test: `tests/test_dispatch_adapter_mode.py`

- [x] **Step 1: Write failing tests**

```python
def test_rag_dispatch_uses_real_adapter_when_env_mode_is_real(monkeypatch):
    monkeypatch.setenv("RIMAS_RAG_MODE", "real")
    assert RagDispatchAgent()._adapter.__class__.__name__ == "RealRagAdapter"
```

- [x] **Step 2: Run test to verify it fails**

Run: `C:\Python314\python.exe -m pytest tests/test_dispatch_adapter_mode.py -v`
Expected: FAIL because dispatch agents always default to Mock.

- [x] **Step 3: Implement minimal mode selection**

Add env-based adapter selection. Keep default as mock. Do not silently fallback from real to mock.

- [x] **Step 4: Run test to verify it passes**

Run: `C:\Python314\python.exe -m pytest tests/test_dispatch_adapter_mode.py -v`
Expected: PASS.

### Task 3: Final verification

- [x] **Step 1: Run focused tests**

Run: `C:\Python314\python.exe -m pytest tests/test_real_kag_adapter.py tests/test_dispatch_adapter_mode.py tests/test_mock_kag_adapter.py tests/test_mock_rag_adapter.py tests/test_v4_agent_and_detail_flow.py -v`

- [x] **Step 2: Review diffs**

Run: `git diff -- app/kag app/agents app/rag tests docs/superpowers/plans/2026-05-13-kag-rag-real-adapter-start.md`
