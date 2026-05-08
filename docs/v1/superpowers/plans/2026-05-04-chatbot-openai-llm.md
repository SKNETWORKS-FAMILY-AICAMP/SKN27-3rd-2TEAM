# Chatbot OpenAI LLM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chatbot Page에서만 OpenAI 기반 LLM Flow를 사용해 문서 계약의 `ResponseState`를 생성한다.

**Architecture:** `ChatbotService`는 Contract Validation 통과 후 `LlmFlowService`를 호출한다. `LlmFlowService`는 Intent, Curation, Recommendation, Response Generator를 순서대로 실행하며, Response Generator만 OpenAI Provider를 통해 최종 자연어 응답 JSON을 생성한다. KAG/RAG 내부 LLM 사용 가능성은 문서에만 기록하고 이번 구현에서는 Mock/Real Adapter 내부 판단 LLM을 추가하지 않는다.

**Tech Stack:** Python, pytest, OpenAI Python SDK, Streamlit.

---

### Task 1: Scope Documentation

**Files:**
- Modify: `docs/Design.md`

- [ ] **Step 1: Add the KAG/RAG LLM boundary note**

`docs/Design.md`에 다음 기준을 추가한다.

```markdown
## Chatbot LLM 구현 범위 메모

- 이번 구현에서 OpenAI LLM 호출은 Chatbot Flow의 Response Generator에만 연결한다.
- KAG/RAG 구현체 내부에서 LLM을 사용할 수 있는 가능성은 배제하지 않는다.
- 다만 KAG/RAG 판단용 LLM은 별도 입출력 계약, 검증 기준, 실패 처리, provenance 기준이 필요하므로 이번 구현 범위에는 포함하지 않는다.
- Main Recommendation Page는 계속 LLM 없이 동작해야 한다.
```

### Task 2: Test First

**Files:**
- Create: `tests/test_llm_flow_service.py`
- Create: `tests/test_openai_llm_client.py`
- Modify: `tests/test_chatbot_service.py`

- [ ] **Step 1: Write failing tests**

검증할 동작:

- `LlmFlowService.run()`이 Agent 흐름을 실행하고 `ResponseState`를 반환한다.
- `ChatbotService`가 Contract Validation 통과 후 LLM Flow 결과를 사용한다.
- OpenAI API Key가 없으면 provider가 명시적으로 실패한다.
- LLM/provider 실패 시 ChatbotService가 fallback을 반환한다.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
pytest tests/test_llm_flow_service.py tests/test_openai_llm_client.py tests/test_chatbot_service.py -q
```

Expected: 새 클래스/생성자/동작이 없어서 실패한다.

### Task 3: Minimal Implementation

**Files:**
- Create: `app/llm/openai_llm_client.py`
- Create: `app/llm/response_state_schema.py`
- Modify: `requirements.txt`
- Modify: `app/config/settings.py`
- Modify: `app/agents/intent_agent.py`
- Modify: `app/agents/curation_agent.py`
- Modify: `app/agents/recommendation_agent.py`
- Modify: `app/agents/response_generator.py`
- Modify: `app/services/llm_flow_service.py`
- Modify: `app/services/chatbot_service.py`

- [ ] **Step 1: Add env-based OpenAI settings**

`OPENAI_API_KEY`, `RIMAS_LLM_MODEL`, `RIMAS_LLM_TIMEOUT_SECONDS`를 환경 변수에서 읽는다.

- [ ] **Step 2: Implement deterministic planning agents**

Intent/Curation/Recommendation Agent는 RAG/KAG 근거만 사용하고 새 추천을 만들지 않는다.

- [ ] **Step 3: Implement OpenAI response generator**

OpenAI provider는 `ResponseState` JSON만 반환하게 하고, API Key 누락 또는 호출 실패는 예외로 올린다.

- [ ] **Step 4: Wire ChatbotService**

Contract Validation 실패 전에는 LLM Flow를 실행하지 않고, LLM/Response/Provenance 실패 시 fallback으로 전환한다.

### Task 4: Verification

**Files:**
- No production changes unless verification exposes a defect.

- [ ] **Step 1: Run focused tests**

```powershell
pytest tests/test_llm_flow_service.py tests/test_openai_llm_client.py tests/test_chatbot_service.py -q
```

- [ ] **Step 2: Run full tests**

```powershell
pytest -q
```

- [ ] **Step 3: Run compile verification**

```powershell
python -m compileall app tests
```
