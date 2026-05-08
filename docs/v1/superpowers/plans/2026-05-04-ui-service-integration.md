# UI Service Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Streamlit UI가 Service Layer만 호출해 Main Recommendation Page와 Chatbot Page를 표시하는 MVP 흐름을 만든다.

**Architecture:** UI는 렌더링만 담당하고, Service가 Mock Adapter, Validator, ViewModelService를 조합한다. Mock 데이터는 문서와 `app/json_templates` 계약을 따르며, 내부 상태는 `developer_mode=True`일 때만 노출한다.

**Tech Stack:** Python, pytest, Streamlit.

---

### Task 1: Mock Adapter, Validator, Service Contracts

**Files:**
- Modify: `tests/test_mock_kag_adapter.py`
- Modify: `tests/test_mock_rag_adapter.py`
- Modify: `tests/test_contract_validator.py`
- Modify: `tests/test_response_validator.py`
- Modify: `tests/test_provenance_validator.py`
- Modify: `tests/test_main_recommendation_service.py`
- Modify: `tests/test_chatbot_service.py`
- Modify: `app/adapters/kag_adapter.py`
- Modify: `app/adapters/rag_adapter.py`
- Modify: `app/adapters/mock_kag_adapter.py`
- Modify: `app/adapters/mock_rag_adapter.py`
- Modify: `app/validators/contract_validator.py`
- Modify: `app/validators/response_validator.py`
- Modify: `app/validators/provenance_validator.py`
- Modify: `app/services/view_model_service.py`
- Modify: `app/services/main_recommendation_service.py`
- Modify: `app/services/chatbot_service.py`

- [ ] **Step 1: Write failing contract tests**
- [ ] **Step 2: Run service/adapter/validator tests and confirm failures**
- [ ] **Step 3: Implement minimal deterministic flow**
- [ ] **Step 4: Run tests and confirm pass**

### Task 2: Streamlit UI Components and Pages

**Files:**
- Create: `tests/test_ui_components.py`
- Modify: `app/main.py`
- Modify: `app/pages/main_recommendation_page.py`
- Modify: `app/pages/chatbot_page.py`
- Modify: `app/ui/components/*.py`
- Modify: `app/ui/styles/theme.py`
- Modify: `app/ui/styles/css.py`

- [ ] **Step 1: Write renderer-injected UI component tests**
- [ ] **Step 2: Run UI tests and confirm failures**
- [ ] **Step 3: Implement Streamlit components and pages**
- [ ] **Step 4: Run UI tests and all tests**

### Task 3: Verification

**Files:**
- No code files unless verification exposes a defect.

- [ ] **Step 1: Run `pytest -q`**
- [ ] **Step 2: Run compile verification**
- [ ] **Step 3: Report Streamlit command**
