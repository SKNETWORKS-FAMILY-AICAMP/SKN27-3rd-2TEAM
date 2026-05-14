# RIMAS

**RIMAS (Recommendation Intelligence Music Assistant System)**는 Multi-Agent AI 기반 음악 큐레이터 시스템입니다. 사용자의 취향을 분석하고 그래프 탐색(KAG)과 의미 검색(RAG)을 결합하여 개인화된 음악을 추천하며, 자연어 챗봇으로 음악 대화를 지원합니다.

---

## 요구사항 정의서

### 프로젝트 배경 및 목표

기존 음악 스트리밍 서비스의 추천 시스템은 단순 이력 기반 필터링에 의존하여 취향의 다양성과 맥락을 충분히 반영하지 못합니다. RIMAS는 그래프 기반 관계 탐색(KAG), 의미 기반 증거 검색(RAG), LLM 자연어 생성을 결합한 Multi-Agent 구조로 이 한계를 극복합니다.

**목표**: 사용자 취향과 맥락을 이해하는 개인화 음악 추천 + 자연어 대화 기반 음악 큐레이션 서비스 제공

---

### 기능 요구사항 (Functional Requirements)

| ID | 기능 | 설명 |
|----|------|------|
| FR-01 | 개인화 음악 추천 | 사용자 취향 프로파일과 그래프 관계 기반으로 3개 섹션(개인화·탐색·신규) 추천 제공 |
| FR-02 | 자연어 챗봇 대화 | 사용자 자연어 입력을 분석하여 의도에 맞는 음악 추천 및 설명 응답 생성 |
| FR-03 | 음악 상세 정보 조회 | 추천 카드 클릭 시 RAG 증거 기반 음악 상세 정보(장르·분위기·추천 이유) 제공 |
| FR-04 | 세션 히스토리 관리 | 대화 히스토리와 세션 컨텍스트를 Redis에 보관하고 세션 수명 동안 유지 |
| FR-05 | 세션 영속화 | Redis 세션 데이터를 PostgreSQL로 플러시하여 영구 보관 |
| FR-06 | 취향 배지 표시 | 사용자 취향 태그(mood·genre)를 헤더 배지로 시각화 |
| FR-07 | 음악 상세 URL 공유 | `?detail={content_id}` 파라미터로 상세 모달 직접 링크 지원 |

---

### 비기능 요구사항 (Non-Functional Requirements)

| ID | 분류 | 요구사항 |
|----|------|---------|
| NFR-01 | 가용성 | Redis 장애 시에도 추천 흐름을 계속 진행하고 `session_degraded` 플래그로 프론트에 통보 |
| NFR-02 | 멱등성 | `request_id` 기반 중복 요청 차단 — 같은 요청의 재시도는 동일 ID를 재사용하고 백엔드가 409로 차단 |
| NFR-03 | 복원력 | LLM(InputPlanner) 실패 시 rule-based fallback 자동 전환, 추천 흐름 중단 없음 |
| NFR-04 | 안전성 | `prod` 환경에서 필수 환경 변수 누락 시 서버 시작 즉시 실패(fail-fast) |
| NFR-05 | 정보 보호 | 내부 Agent trace·validator trace는 API 응답에 미노출, 외부에 보이지 않음 |
| NFR-06 | 추천 품질 | 추천 결과는 최대 5곡으로 제한하여 집중도 있는 큐레이션 제공 |
| NFR-07 | 성능 | React Query stale-time 및 마운트 단위 requestId로 불필요한 중복 API 호출 방지 |
| NFR-08 | 확장성 | Mock Adapter를 통한 전체 흐름 검증 — Real Neo4j / Elasticsearch 교체 없이 독립 동작 가능 |

---

## 기능 설계서

### 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + TypeScript)             │
│  MainRecommendationPage  │  ChatbotPage  │  MusicDetailModal     │
│  React Query + Zustand   │  useMutation  │  URL param routing    │
└────────────────┬────────────────────────────────────────────────┘
                 │  REST API (axios)
┌────────────────▼────────────────────────────────────────────────┐
│                       Backend (FastAPI)                          │
│  /api/recommendations/main  │  /api/chatbot/respond             │
│  /api/music/detail          │  /api/sessions/{id}/flush         │
└────────────────┬────────────────────────────────────────────────┘
                 │
     ┌───────────┼──────────────┐
     ▼           ▼              ▼
  Redis       PostgreSQL     External
  (세션/캐시)  (영속 데이터)   OpenAI LLM
                             Neo4j (KAG)
                             Elasticsearch (RAG)
```

---

### Agent 파이프라인 설계

Multi-Agent 오케스트레이터가 각 Agent를 순차 실행합니다.

```
사용자 요청
    │
    ▼
InputPlannerAgent
  - 사용자 의도 분류 (primary_goal / mood / genre / era 등)
  - LLM(OpenAI) 우선 → 실패 시 rule-based fallback
    │
    ▼
KagDispatchAgent
  - 그래프 탐색으로 추천 방향 및 후보 content_id 결정
  - KAG_STATE 생성 (route / target_section / recommended_content_ids)
    │
    ▼
ContractValidator
  - KAG_STATE + SESSION_CONTEXT 계약(enum) 검증
  - 타입·필드 위반 시 경고 로그 (흐름은 계속)
    │
    ▼
RagDispatchAgent
  - 후보 content_id에 대한 의미 기반 증거 검색
  - RAG_STATE 생성 (evidence_summary / recommendation_reason)
    │
    ▼
IntentAgent  [챗봇 전용]
  - KAG + RAG 결과 기반 최종 intent 결정
    │
    ▼
RecommendationAgent
  - 최종 추천 후보 선택 (최대 5곡)
  - 랭킹 점수 = max(0.1, 1.0 − (rank−1) × 0.05)
    │
    ▼
ResponseGenerator
  - LLM으로 추천 이유 자연어 응답 생성
  - API 키 없으면 로컬 템플릿 응답 반환
    │
    ▼
ResponseValidator + ProvenanceValidator
  - 응답 품질 검증 (형식 / 출처 일관성)
    │
    ▼
최종 응답 반환
```

---

### 기능별 상세 설계

#### 메인 추천 페이지

| 구성요소 | 설계 |
|---------|------|
| 추천 섹션 | 전체 추천 화면에서는 개인화 추천 / 새로운 취향 탐색 / 신규 발매 3개 섹션을 함께 표시 |
| 카테고리 진입 | 홈 별자리 노드에서 개인화 추천 / 새로운 취향 / 신규 발매를 선택하면 해당 카테고리 섹션만 표시 |
| 취향 배지 | SESSION_CONTEXT의 mood·genre 태그를 헤더에 배지로 표시 |
| 오늘의 테마 | 날짜·취향 기반 테마 메시지 |
| 캐릭터 DJ 배너 | Agent 추천 메시지 표시, 챗봇으로 이동 버튼 |
| 상태 관리 | React Query (staleTime 5분) + `useRequestId()` 훅으로 retry 시 동일 ID 재사용 |
| session_degraded | Redis 장애 시 경고 배너 상단 노출 |

#### 챗봇 페이지

| 구성요소 | 설계 |
|---------|------|
| 메시지 전송 | `useMutation` 기반 — `isPending` 가드로 중복 전송 차단 |
| 낙관적 업데이트 | `appendTurn`으로 서버 응답 전 UI 즉시 반영 |
| 히스토리 로드 | 마운트 1회 `useQuery` — Redis 세션 히스토리 조회 |
| 자동 스크롤 | 메시지 추가마다 하단 자동 스크롤 |
| 관련 추천 카드 | 마지막 챗봇 응답의 `display_recommendations`를 카드로 표시 |
| request_id | 전송마다 `generateRequestId()`로 새 ID 생성 |

#### 음악 상세 모달

| 구성요소 | 설계 |
|---------|------|
| 데이터 소스 우선순위 | 1순위: 최근 RAG_STATE evidence / 2순위: music_catalog / 3순위: minimal metadata |
| URL 연동 | `?detail={content_id}` — pushState로 딥링크·뒤로가기 지원 |
| request_id | `useRequestIdPerKey(contentId)` — 곡 변경 시 새 ID, 같은 곡 retry는 동일 ID |
| view log | `user_id` 있을 때 interaction_logs에 비동기 저장 |

---

### 데이터 설계

#### Redis 세션 구조 (세션당 6개 키)

| 키 | 용도 | TTL |
|----|------|-----|
| `rimas:session:{id}:history` | 대화 히스토리 list (최대 50턴) | 세션 TTL |
| `rimas:session:{id}:context` | SESSION_CONTEXT JSON | 세션 TTL |
| `rimas:session:{id}:latest:kag_state` | 최근 KAG_STATE | 세션 TTL |
| `rimas:session:{id}:latest:rag_state` | 최근 RAG_STATE | 세션 TTL |
| `rimas:session:{id}:latest:response_state` | 최근 RESPONSE_STATE | 세션 TTL |
| `rimas:session:{id}:recommendation:metadata` | 추천 메타데이터 | 세션 TTL |

#### PostgreSQL 주요 테이블

| 테이블 | 용도 |
|--------|------|
| `users` | 사용자 기본 정보 |
| `music_catalog` | 음악 메타데이터 (title, artist, genre, mood, release_date) |
| `interaction_logs` | KAG/RAG/Response state 압축 로그, view log, latency |
| `chat_sessions` | 세션 메타데이터 (flush 시 upsert) |
| `chat_session_turns` | 대화 turn 영속 기록 |

---

### Frontend 아키텍처

```
src/
  pages/        MainRecommendationPage, ChatbotPage
  components/   home/ · recommendation/ · chatbot/ · background/ · mascot/ — 페이지/역할 단위 컴포넌트 분리
  api/          chatbot · recommendation · musicDetailApi — axios 래퍼
  stores/       chatStore (Zustand) · sessionStore — 전역 상태
  hooks/        useRequestId · useRequestIdPerKey — requestId 훅
  utils/        generateRequestId — crypto.randomUUID 기반 ID 생성
  types/        API 응답 TypeScript 타입 (session_degraded 포함)
```

**상태 관리 전략**
- API 서버 상태: React Query (`useQuery` / `useMutation`)
- 챗봇 히스토리: Zustand chatStore (`appendTurn`으로 낙관적 업데이트)
- 입력값: 지역 `useState` — 타이핑마다 전역 재렌더 방지

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.12+, FastAPI |
| Frontend | React, TypeScript, Vite |
| Cache | Redis |
| Database | PostgreSQL |
| LLM | OpenAI GPT-4.1-mini (optional) |
| Graph DB | Neo4j (Real KAG — 미구현) |
| Search | Elasticsearch (Real RAG — 미구현) |
| 상태 관리 | React Query, Zustand |
| 컨테이너 | Docker Compose |

---

## Runtime Flow

### Main Recommendation

```text
React Main Page
-> GET /api/recommendations/main?user_id=&session_id=&request_id=
-> Redis health check (session_degraded 플래그)
-> Session Context (Redis)
-> OrchestratorAgent.run_recommendation
   -> InputPlannerAgent (LLM optional → rule-based fallback)
   -> KagDispatchAgent  -> KAG_STATE
   -> RagDispatchAgent  -> RAG_STATE
-> ViewModelBuilder (personalized / discovery / new_release 섹션)
-> latest_state_cache.save_latest_states (Redis)
-> Response: { status, session_degraded, page_type, view_model }
```

### Chatbot

```text
React Chatbot Page
-> POST /api/chatbot/respond
-> Redis health check (session_degraded 플래그)
-> Session Context (Redis)
-> OrchestratorAgent.run_chatbot
   -> InputPlannerAgent (LLM optional → rule-based fallback)
   -> KagDispatchAgent  -> KAG_STATE
   -> ContractValidator
   -> RagDispatchAgent  -> RAG_STATE
   -> IntentAgent
   -> RecommendationAgent (최대 5곡 선택)
   -> ResponseGenerator (LLM)
   -> ResponseValidator + ProvenanceValidator
-> session_history_cache.append_turn (Redis)
-> latest_state_cache.save_latest_states (Redis)
-> LoggingService → interaction_logs (PostgreSQL)
-> Response: { status, session_degraded, response_state, latency_ms }
```

### Music Detail

```text
Recommendation Card Click
-> GET /api/music/detail/{content_id}?user_id=&session_id=&request_id=
-> latest_state_cache.get_latest_rag_state (Redis, session_id 있을 때)
-> MusicDetailService.get_detail(recent_rag_state)
   1순위: latest RAG_STATE evidence
   2순위: music_catalog fallback
   3순위: minimal metadata
-> (user_id 있을 때) interaction_logs view log 저장
-> Response: { status, music_detail }
```

### Session Flush

```text
POST /api/sessions/{session_id}/flush?user_id=&flush_logs=false
-> session_history_cache.get_history (Redis)
-> PostgreSQL: chat_sessions upsert + chat_session_turns insert
-> (flush_logs=true, local/dev 환경만) interaction_logs DELETE WHERE session_id=?
-> session_history_cache.clear_session (Redis history + context)
-> latest_state_cache.clear_latest_states (Redis latest kag/rag/response/metadata)
-> Response: { session_id, flushed, logs_deleted }
```

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |
| GET | `/api/recommendations/main` | 메인 추천 페이지 뷰모델 |
| POST | `/api/chatbot/respond` | 챗봇 메시지 처리 |
| GET | `/api/sessions/{session_id}/history` | Redis 세션 히스토리 |
| POST | `/api/sessions/{session_id}/flush` | Redis → PostgreSQL 플러시 |
| DELETE | `/api/sessions/{session_id}` | Redis 세션 삭제 |
| GET | `/api/music/detail/{content_id}` | 음악 상세 뷰모델 |

---

## 구현 현황

### 완료

| 구분 | 내용 |
|------|------|
| Agent 흐름 | Orchestrator → InputPlanner → KAG → RAG → Intent → Recommendation → ResponseGenerator → Validators |
| Mock Adapter | MockKagAdapter, MockRagAdapter (고정 데이터, Real 연결 전 전체 흐름 검증용) |
| Redis 세션 | 히스토리, 컨텍스트, latest KAG/RAG/RESPONSE state, 추천 메타데이터 |
| Session flush | Redis → PostgreSQL, 완료 후 6개 Redis 키 전체 삭제 |
| flush_logs | `flush_logs=true` — local/dev 전용, session_id 기준 interaction_logs 삭제 |
| session_degraded | Redis 장애 시 응답 wrapper 최상위에 플래그 포함, 추천 흐름은 계속 진행 |
| Music Detail | latest RAG_STATE 연결 (session_id), view log 저장 (user_id) |
| LLM Planner | optional OpenAI 의도 분류, 실패 시 rule-based fallback |
| 스키마 확장 | KAG_STATE optional 필드 5개, RAG_STATE optional 필드 4개 |
| Contract Validator | KAG/RAG/session_context 계약 검증 + optional 타입 검증 |
| prod fail-fast | 필수 env 누락 시 서버 시작 즉시 실패 |
| 정책 문서 | `docs/policies/` (RecommendationPolicy, RankingPolicy, PromptPolicy) |
| Frontend | 홈 별자리 네비게이션, React 메인 추천 페이지, 카테고리별 추천 화면, 챗봇 페이지, 음악 상세 모달 |
| Frontend request_id | `generateRequestId` 유틸, `useRequestId` / `useRequestIdPerKey` 훅, 전 API에 request_id 전달, `session_degraded` 배너 표시 |

### 미구현 (stub)

| 구분 | 내용 |
|------|------|
| Real KAG Adapter | Neo4j 기반 그래프 탐색 (`NotImplementedError`) |
| Real RAG Adapter | Elasticsearch 기반 하이브리드 검색 (`NotImplementedError`) |

---

## 실행

`.env.example`을 기준으로 로컬 `.env`를 만든 뒤 실행합니다.

```env
RIMAS_DB_NAME=rimas
RIMAS_DB_USER=rimas
RIMAS_DB_PASSWORD=change_me_postgres_password
RIMAS_NEO4J_USER=neo4j
RIMAS_NEO4J_PASSWORD=change_me_neo4j_password
OPENAI_API_KEY=
RIMAS_KAG_MODE=real
RIMAS_RAG_MODE=real
RIMAS_ELASTICSEARCH_INDEX=spotify_songs
```

`.env`는 Git에 커밋하지 않습니다. `OPENAI_API_KEY`가 비어 있으면 챗봇 응답 생성은 로컬 fallback 문구를 사용합니다.

```powershell
docker compose down -v
docker compose up --build
```

서비스 확인:

```
Frontend:                   http://localhost:5173
Backend health:             http://localhost:8000/health
Main Recommendation API:    http://localhost:8000/api/recommendations/main?user_id=user_001&session_id=session_001
Neo4j Browser:              http://localhost:7474
Elasticsearch:              http://localhost:9200
```

---

## 주요 폴더

```text
app/
  agents/          Orchestrator, InputPlanner, KAG/RAG Dispatch, Intent, Recommendation, Response
  api/             FastAPI routes (chatbot, recommendation, session, music)
  cache/           Redis 클라이언트, 세션 히스토리, latest state 캐시
  config/          settings.py (환경 변수, prod fail-fast)
  kag/adapters/    KAG adapter (Mock / Real stub)
  llm/             OpenAI LLM 클라이언트
  policies/        추천·랭킹 정책 (Python)
  prompts/         LLM 프롬프트 (InputPlanner)
  rag/adapters/    RAG adapter (Mock / Real stub)
  repositories/    PostgreSQL query constants, 카탈로그·로그 레포지토리
  services/        비즈니스 서비스 (chatbot, recommendation, flush, logging, detail)
  validators/      Contract, Response, Provenance Validator

frontend/
  src/api/         API clients (chatbot, recommendation, musicDetail)
  src/components/  UI components (home, chatbot, recommendation, background, mascot)
  src/hooks/       useRequestId 훅
  src/pages/       MainRecommendationPage, ChatbotPage
  src/stores/      Zustand stores (chat, session)
  src/utils/       generateRequestId 유틸

docs/
  policies/        RecommendationPolicy, RankingPolicy, PromptPolicy
  rimas_v_4_integrated_design_updated_final_.md
```

---

## 정책 문서

- [RecommendationPolicy](docs/policies/RecommendationPolicy.md) — 카테고리 우선순위, 최대 추천 수
- [RankingPolicy](docs/policies/RankingPolicy.md) — 점수 계산 공식
- [PromptPolicy](docs/policies/PromptPolicy.md) — LLM 적용 범위, enum 검증, fallback 정책
