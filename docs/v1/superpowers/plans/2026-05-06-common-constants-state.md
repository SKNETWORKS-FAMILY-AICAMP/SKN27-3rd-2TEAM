# Common Constants State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 공통 계약 상수와 기본 state를 `app/common`으로 모아 레이어별 중복 import를 줄인다.

**Architecture:** SQL 쿼리 상수는 문서상 Repository Layer 책임이므로 `app/repositories/query_constants.py`에 유지한다. UI 색상/스타일 상수는 UI Layer 책임이므로 `app/ui/styles/theme.py`에 유지한다. 공통 status, category label, 기본 ML/fallback/session state만 `app/common`에서 제공한다.

**Tech Stack:** Python, pytest, Streamlit session_state, 기존 RIMAS 서비스/에이전트 구조

---

### Task 1: Common Package

**Files:**
- Create: `app/common/__init__.py`
- Create: `app/common/constants.py`
- Create: `app/common/default_state.py`
- Create: `app/common/labels.py`
- Modify: `app/main.py`
- Modify: `app/services/*.py`
- Modify: `app/agents/*.py`
- Modify: `app/validators/contract_validator.py`
- Test: `tests/test_common_constants.py`

- [ ] **Step 1: Write the failing test**

Add a test that imports `app.common` modules and verifies the documented defaults.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_common_constants.py -v`
Expected: FAIL because `app.common` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create the `app/common` package and move only common constants/state there. Update imports.

- [ ] **Step 4: Run focused tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_common_constants.py -v`
Expected: PASS.

### Task 2: Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/Design.md`
- Modify: `docs/Service Flow 설계.md`

- [ ] **Step 1: Update architecture docs**

Document `app/common` responsibility and explicitly state that SQL constants and UI theme remain in their current layers.

- [ ] **Step 2: Run full tests**

Run: `.\.venv\Scripts\python.exe -m pytest -v`
Expected: PASS.
