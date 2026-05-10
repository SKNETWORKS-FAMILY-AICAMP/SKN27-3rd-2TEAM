# RIMAS

RIMAS는 Spotify 음악 메타데이터와 그래프 기반 관계 탐색을 활용하는 Multi-Agent 음악 큐레이터 시스템입니다. v4 기준 구현 문서는 `docs/rimas_v_4_integrated_design_updated_final_.md`이며, 이 문서를 현재 구현 기준으로 봅니다.

## 핵심 원칙

- UI는 추천을 생성하지 않고 API 응답만 표시합니다.
- LLM은 추천 후보를 만들지 않고, `selected_recommendations`와 RAG evidence 기반 자연어 응답만 생성합니다.
- `OPENAI_API_KEY`가 없으면 챗봇은 임시 로컬 응답을 반환합니다. 나중에 env를 채우면 OpenAI 경로로 동작합니다.
- PostgreSQL은 최소 canonical metadata와 영속 로그를 담당합니다.
- Redis는 세션 컨텍스트와 대화 히스토리 캐시를 담당합니다.
- Neo4j는 KAG graph traversal 담당입니다.
- Elasticsearch는 RAG evidence retrieval 담당입니다.
- 내부 trace와 validator trace는 고객 응답에 노출하지 않습니다.

## Runtime Flow

### Main Recommendation

```text
React Main Page
-> GET /api/recommendations/main
-> Request Lifecycle Cache
-> Session Context
-> Orchestrator Agent
-> Input Planner Agent
-> KAG Dispatch Agent
-> RAG Dispatch Agent
-> Recommendation Agent
-> CompactStateBuilder
-> React Recommendation Cards
```

### Music Detail

```text
Recommendation Card Click
-> URL query detail=<content_id>
-> GET /api/music/detail/{content_id}
-> MusicDetailService
-> Music Detail ViewModel
-> React MusicDetailModal
```

### Chatbot

```text
React Chatbot Page
-> POST /api/chatbot/respond
-> Session Context
-> Orchestrator Agent
-> Input Planner / KAG / RAG / Recommendation
-> Response Generator
-> Response Validator
-> Provenance Validator
-> Redis Session History Save
-> PostgreSQL interaction_logs Save
```

## PostgreSQL Schema

v4 PostgreSQL은 minimal canonical storage 중심입니다.

필수 테이블:

- `users`
- `music_catalog`
- `interaction_logs`
- `chat_sessions`
- `chat_session_turns`
- `detail_view_logs`

제거된 v3/ML 테이블:

- `ml_outputs`
- `kkbox_user_features`
- `user_music_profiles`
- `spotify_lyrics`
- `spotify_emotions`

`interaction_logs`는 full state가 아니라 compact state만 저장합니다.

- `request_id`
- `compact_kag_state_json`
- `compact_rag_state_json`
- `compact_response_state_json`
- `validation_status`
- `latency_ms`
- `error_type`

## 실행 순서

스키마가 변경되었으므로 처음 실행하거나 DB 구조를 다시 맞출 때는 volume을 삭제합니다.

```powershell
docker compose down -v
docker compose up --build
```

백그라운드 실행:

```powershell
docker compose up --build -d
docker compose logs -f backend frontend
```

서비스 확인:

```text
Frontend: http://localhost:5173
Backend health: http://localhost:8000/health
Main Recommendation API: http://localhost:8000/api/recommendations/main?user_id=user_001&session_id=session_001
Music Detail API: http://localhost:8000/api/music/detail/track_001
Neo4j Browser: http://localhost:7474
Elasticsearch: http://localhost:9200
```

챗봇 OpenAI 연결을 사용하려면 실행 전에 환경변수를 지정합니다.

```powershell
$env:OPENAI_API_KEY="your_api_key"
docker compose up --build
```

`OPENAI_API_KEY`가 없으면 임시 로컬 응답이 반환됩니다.

## 로컬 검증

백엔드 테스트:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

프론트 빌드:

```powershell
cd frontend
npm run build
```

Docker Compose 설정 검증:

```powershell
docker compose config --quiet
```

## 주요 폴더

```text
app/
  api/                 FastAPI routes
  agents/              Orchestrator, Input Planner, KAG/RAG Dispatch, Recommendation, Response
  cache/               Redis session cache
  common/              constants, labels, default state
  config/              runtime settings
  contracts/           field contracts
  kag/adapters/        KAG adapter boundary
  rag/adapters/        RAG adapter boundary
  repositories/        PostgreSQL repository/query constants
  schemas/             Runtime Contract schemas
  services/            application services and state builders
  validators/          Contract, Response, Provenance validators

frontend/
  src/api/             API clients
  src/components/      UI components
  src/pages/           MainRecommendationPage, ChatbotPage
  src/stores/          Zustand stores
  src/types/           TypeScript contracts

db/
  schema.sql           v4 PostgreSQL schema
  seed.sql             minimal users/music_catalog seed
  init/                docker-entrypoint seed script

docs/
  rimas_v_4_integrated_design_updated_final_.md
```

## DB 파일 정리 기준

현재 `db` 폴더에서 유지해야 하는 파일:

- `db/schema.sql`
- `db/seed.sql`
- `db/init/03-load-source-data.sh`

v4 PostgreSQL schema에서 사용하지 않는 `db/load/*.sql` 파일은 제거 대상입니다. Elasticsearch 인덱싱용 로더가 필요해지면 별도 `infra/elasticsearch` 또는 전용 indexer 경로로 새로 정의합니다.
