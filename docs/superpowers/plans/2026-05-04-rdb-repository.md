# RDB Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** docs의 DB 명세에 맞춰 PostgreSQL DDL, seed, psycopg2 기반 RDB Repository 계층을 만든다.

**Architecture:** DB 접근은 Repository Layer에만 둔다. SQL은 `query_constants.py`에 상수로 분리하고, KAG/RAG 동작 구현은 하지 않으며 JSONB 저장/조회 필드만 다룬다.

**Tech Stack:** Python, pytest, PostgreSQL, psycopg2-compatible DB-API connection.

---

### Task 1: Repository 계약 테스트

**Files:**
- Create: `tests/test_rdb_repositories.py`

- [ ] **Step 1: Write failing tests**

```python
def test_ml_output_repository_fetches_latest_by_user_id():
    connection = FakeConnection(fetchone_result={"user_id": "user_001"})
    repository = MlOutputRepository(connection)
    assert repository.get_latest_by_user_id("user_001") == {"user_id": "user_001"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_rdb_repositories.py -v`
Expected: FAIL because repositories are not implemented.

### Task 2: SQL constants and repositories

**Files:**
- Modify: `app/repositories/query_constants.py`
- Modify: `app/repositories/ml_output_repository.py`
- Modify: `app/repositories/music_catalog_repository.py`
- Modify: `app/repositories/interaction_log_repository.py`

- [ ] **Step 1: Implement SQL constants from docs**
- [ ] **Step 2: Implement repositories using injected psycopg2-compatible connection**
- [ ] **Step 3: Run repository tests**

Run: `pytest tests/test_rdb_repositories.py -v`
Expected: PASS.

### Task 3: PostgreSQL DDL, seed, and settings

**Files:**
- Create: `db/schema.sql`
- Create: `db/seed.sql`
- Modify: `app/config/settings.py`

- [ ] **Step 1: Add docs-defined DDL for required tables**
- [ ] **Step 2: Add docs-defined seed data for users, ml_outputs, music_catalog**
- [ ] **Step 3: Add psycopg2 connection settings without hardcoding credentials**
- [ ] **Step 4: Run all tests**

Run: `pytest -q`
Expected: PASS.
