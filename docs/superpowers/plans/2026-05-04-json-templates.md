# JSON Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** docs의 JSON Schema 문서에 맞춰 앱에서 참조할 수 있는 기본 JSON 템플릿 파일을 만든다.

**Architecture:** `app/json_templates/`를 새로 만들고, 각 계약은 독립 JSON 파일로 분리한다. 기존 `app/contracts` 빈 파일은 건드리지 않으며 KAG/RAG 실행 로직은 구현하지 않는다.

**Tech Stack:** JSON, Python standard library unittest.

---

### Task 1: Template Contract Tests

**Files:**
- Create: `tests/test_json_templates.py`

- [ ] **Step 1: Write failing tests for required template files and fields**
- [ ] **Step 2: Run `python -m unittest tests.test_json_templates -v` and confirm missing files fail**

### Task 2: JSON Template Files

**Files:**
- Create: `app/json_templates/ml_output_template.json`
- Create: `app/json_templates/kag_state_template.json`
- Create: `app/json_templates/rag_state_template.json`
- Create: `app/json_templates/intent_result_template.json`
- Create: `app/json_templates/curation_plan_template.json`
- Create: `app/json_templates/selected_recommendations_template.json`
- Create: `app/json_templates/response_state_template.json`
- Create: `app/json_templates/interaction_log_template.json`

- [ ] **Step 1: Add docs-defined JSON shapes**
- [ ] **Step 2: Run template tests**
- [ ] **Step 3: Run compile verification**
