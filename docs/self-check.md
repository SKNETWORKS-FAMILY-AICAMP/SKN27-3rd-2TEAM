# 프로젝트 폴더 및 파일 구조 점검

작성 기준: 현재 저장소 `c:\dev\Project\SKN27-3rd-2TEAM`의 실제 파일 구조 기준  
주의: 요청의 `front` 폴더는 현재 존재하지 않으며, 프론트엔드 구현은 `frontend/` 폴더에 있습니다.

## 1. 루트 구조

```text
SKN27-3rd-2TEAM/
├── app/                    # FastAPI 백엔드 애플리케이션
├── data/                   # 적재/가공 데이터 보관
├── db/                     # PostgreSQL 스키마, 시드, 초기화 스크립트
├── docs/                   # 구현 기준 설계 문서
├── frontend/               # React + TypeScript + Vite 프론트엔드
├── neo4j/                  # Neo4j 그래프 데이터 적재 구성
├── seed/                   # 시드 관련 예약 폴더
├── tests/                  # 백엔드 계약/서비스/검증 테스트
├── .dockerignore           # Docker 빌드 컨텍스트 제외 규칙
├── .gitignore              # Git 추적 제외 규칙
├── docker-compose.yml      # 전체 서비스 컨테이너 오케스트레이션
├── Dockerfile              # 백엔드 Docker 이미지 정의
├── pytest.ini              # pytest 설정
├── README.md               # 프로젝트 실행 및 구조 안내
├── requirements.txt        # 백엔드 Python 의존성
└── self-check.md           # 프로젝트 구조 점검 문서
```

### 제외 또는 생성물 성격 폴더

- `.git/`: Git 저장소 메타데이터입니다.
- `.venv/`: 로컬 Python 가상환경입니다.
- `.pytest_cache/`: pytest 실행 캐시입니다.

## 2. 주요 폴더 역할

### `app/`

FastAPI 기반 백엔드 애플리케이션입니다. API 라우터, Agent 흐름, 서비스 계층, 저장소 계층, Runtime Contract 스키마, Validator, LLM 클라이언트, KAG/RAG Adapter 경계를 포함합니다.

```text
app/
├── api/                    # HTTP API 라우터
├── agents/                 # Orchestrator 및 Agent 계층
├── cache/                  # Redis 기반 세션/히스토리 캐시
├── common/                 # 공통 상수, 라벨, 기본 상태
├── config/                 # 런타임 설정
├── contracts/              # 필드 계약 상수
├── json_templates/         # Runtime State JSON 템플릿
├── kag/                    # KAG Adapter 경계
├── llm/                    # LLM 클라이언트 및 응답 스키마
├── rag/                    # RAG Adapter 및 State Builder
├── repositories/           # PostgreSQL 접근 계층
├── schemas/                # Runtime Contract / API 스키마
├── services/               # 애플리케이션 서비스 계층
├── validators/             # 계약/응답/출처 검증기
└── main.py                 # FastAPI 앱 진입점
```

#### `app/api/`

- `__init__.py`: API 패키지 초기화 파일입니다.
- `chatbot_routes.py`: 챗봇 응답 API 라우터입니다.
- `music_detail_routes.py`: 음악 상세 조회 API 라우터입니다.
- `recommendation_routes.py`: 메인 추천 API 라우터입니다.
- `session_routes.py`: 세션 히스토리 조회 및 세션 flush API 라우터입니다.

#### `app/agents/`

- `base_agent.py`: Agent 공통 기반 클래스 또는 인터페이스 역할입니다.
- `input_planner_agent.py`: 사용자 입력을 KAG/RAG 처리 입력으로 계획하는 Agent입니다.
- `intent_agent.py`: 사용자 의도 판별을 담당하는 Agent입니다.
- `kag_dispatch_agent.py`: KAG Adapter 호출 흐름을 담당하는 Dispatch Agent입니다.
- `orchestrator_agent.py`: 전체 Agent 실행 흐름을 조율하는 Orchestrator입니다.
- `rag_dispatch_agent.py`: RAG Adapter 호출 흐름을 담당하는 Dispatch Agent입니다.
- `recommendation_agent.py`: 추천 후보 생성 또는 추천 상태 구성을 담당하는 Agent입니다.
- `response_generator.py`: 최종 챗봇 응답 생성을 담당하는 Agent입니다.
- `validator_controller.py`: 응답 검증 흐름을 조율하는 컨트롤러입니다.

#### `app/cache/`

- `__init__.py`: 캐시 패키지 초기화 파일입니다.
- `redis_client.py`: Redis 연결 클라이언트 생성/관리 모듈입니다.
- `session_history_cache.py`: 세션 대화 이력 캐시 접근 모듈입니다.

#### `app/common/`

- `__init__.py`: 공통 패키지 초기화 파일입니다.
- `constants.py`: 전역 공통 상수 모듈입니다.
- `default_state.py`: 기본 Runtime State 값을 정의하는 모듈입니다.
- `labels.py`: UI 또는 응답에서 사용하는 라벨 정의 모듈입니다.

#### `app/config/`

- `settings.py`: 환경변수와 런타임 설정을 관리하는 모듈입니다.

#### `app/contracts/`

- `__init__.py`: 계약 패키지 초기화 파일입니다.
- `fields.py`: Runtime Contract에서 반복 사용하는 필드명 상수 모듈입니다.

#### `app/json_templates/`

- `intent_result_template.json`: Intent 결과 상태 템플릿입니다.
- `interaction_log_template.json`: 상호작용 로그 저장 구조 템플릿입니다.
- `kag_state_template.json`: KAG 상태 템플릿입니다.
- `rag_state_template.json`: RAG 상태 템플릿입니다.
- `response_state_template.json`: 응답 상태 템플릿입니다.
- `selected_recommendations_template.json`: 선택된 추천 결과 템플릿입니다.

#### `app/kag/`

- `__init__.py`: KAG 패키지 초기화 파일입니다.
- `adapters/kag_adapter.py`: KAG Adapter 인터페이스 또는 공통 계약입니다.
- `adapters/mock_kag_adapter.py`: 테스트/로컬용 Mock KAG Adapter입니다.
- `adapters/real_kag_adapter.py`: Neo4j 등 실제 KAG 연동용 Adapter입니다.
- `adapters/__init__.py`: KAG Adapter 패키지 초기화 파일입니다.

#### `app/llm/`

- `openai_llm_client.py`: OpenAI LLM 호출 클라이언트입니다.
- `response_state_schema.py`: LLM 응답 상태 관련 스키마 모듈입니다.

#### `app/rag/`

- `__init__.py`: RAG 패키지 초기화 파일입니다.
- `adapters/rag_adapter.py`: RAG Adapter 인터페이스 또는 공통 계약입니다.
- `adapters/mock_rag_adapter.py`: 테스트/로컬용 Mock RAG Adapter입니다.
- `adapters/real_rag_adapter.py`: 구현 이전에 만들어진 임시 Real RAG Adapter이며, 연결 완료 후 폐기 후보입니다.
- `adapters/rag_mock_adapter.py`: 신규 RAG 설계 기준 Mock Adapter 후보 파일입니다.
- `adapters/rag_real_adapter.py`: 최종 Real RAG Adapter 기준 파일입니다.
- `adapters/description.md`: Adapter 계층의 책임과 교체 지점을 설명합니다.
- `builders/rag_state_builder.py`: RAG 검색 결과를 Runtime State로 구성하는 Builder입니다.
- `ragStateBuilder/schema.py`: RAG 요청, 내부 상태, 출력 계약을 정의합니다.
- `ragStateBuilder/nodes.py`: RAG workflow node 후보 구현입니다.
- `ragStateBuilder/edges.py`: RAG workflow 분기 조건 후보 구현입니다.
- `ragStateBuilder/builder.py`: 경량 RAG graph compile/invoke 후보 구현입니다.
- `ragStateBuilder/description.md`: RAG State Builder 계층 설명 문서입니다.
- `contractValidator/base_validator.py`: RAG 최소 계약 검증기 공통 기반 후보입니다.
- `contractValidator/format_validator.py`: RAG 출력 필수 필드/형식 검증 후보입니다.
- `contractValidator/logic_validator.py`: KAG 후보 content_id 범위 검증 후보입니다.
- `contractValidator/hallucination_validator.py`: 현재 MVP 필수 범위가 아니며, 최종 응답/출처 검증은 공통 validator가 담당합니다.
- `contractValidator/description.md`: RAG 최소 계약 검증 계층 설명 문서입니다.
- `musicCatalogRepository/base_repostiory.py`: RAG 음악 카탈로그 저장소 공통 경계 후보입니다.
- `musicCatalogRepository/sql_repostiory.py`: Elasticsearch/SQL 연동 저장소 후보 구현입니다.
- `musicCatalogRepository/loader.py`: RAG 카탈로그 데이터 로더 후보입니다.
- `musicCatalogRepository/loader2.py`: RAG 카탈로그 데이터 로더 후보입니다.
- `musicCatalogRepository/loader_lyrics.py`: RAG 가사 데이터 로더 후보입니다.
- `musicCatalogRepository/description.md`: RAG 저장소 계층 설명 문서입니다.
- `services/retrieval.py`: Elasticsearch lexical/semantic/hybrid 검색 후보 구현입니다.
- `services/embedding.py`: Ollama embedding 생성 후보 구현입니다.
- `services/indexing.py`: RAG indexing workflow 후보 구현입니다.
- `services/rag_generation.py`: 검색 근거 기반 생성 단계 후보 파일입니다.
- `services/description.md`: RAG service 계층 설명 문서입니다.
- `common/elasticsearch_vector.py`: Elasticsearch vector 검색 보조 후보 모듈입니다.
- `common/custom_pgvector.py`: pgvector 기반 검색 보조 후보 모듈입니다.
- `data/spotify_songs.csv`: RAG 개발/검증용 Spotify CSV 데이터입니다.
- `data/embedded_data_part111.json`: RAG 개발/검증용 embedding JSON 데이터입니다.
- `design.md`: RAG 구현 순서와 계층별 책임을 정리한 설계 문서입니다.
- `output.md`: RAG 출력 예시 문서입니다.

현재 RAG 신규 파일은 실제 Dispatch 연결 완료 상태로 보지 않습니다. 최종 Adapter 기준은 `rag_real_adapter.py`이며, `real_rag_adapter.py`는 임시 파일/폐기 후보로 분류합니다. `retrieval.py`, `indexing.py`, `embedding.py`는 Real RAG 연결 후보 구현입니다.

RAG Dispatch Adapter 선택 기준은 `RIMAS_RAG_MODE` 환경변수입니다. 기본값은 `mock`이고, `RIMAS_RAG_MODE=real`일 때만 Real RAG Adapter를 사용합니다. Real RAG 실패 시 조용히 Mock으로 전환하지 않고 `fallback` 또는 `failed` 상태를 명시해야 합니다.

`musicCatalogRepository`의 `*_repostiory.py` 오타 파일명은 Real RAG 연결 완료 후 import 영향 범위를 확인한 뒤 한 번에 정리합니다.

#### `app/repositories/`

- `base_repository.py`: 저장소 공통 기반 클래스 또는 DB 접근 공통 로직입니다.
- `interaction_log_repository.py`: 사용자 상호작용 로그 저장소입니다.
- `music_catalog_repository.py`: 음악 카탈로그 조회 저장소입니다.
- `query_constants.py`: SQL 쿼리 상수 모듈입니다.
- `spotify_audio_feature_repository.py`: Spotify 오디오 피처 조회 저장소입니다.
- `spotify_emotion_repository.py`: Spotify 감정 데이터 조회 저장소입니다.
- `spotify_lyrics_repository.py`: Spotify 가사 데이터 조회 저장소입니다.
- `spotify_track_repository.py`: Spotify 트랙 메타데이터 조회 저장소입니다.

#### `app/schemas/`

- `intent_state_schema.py`: Intent 상태 스키마입니다.
- `kag_input_schema.py`: KAG 입력 계약 스키마입니다.
- `kag_state_schema.py`: KAG 상태 계약 스키마입니다.
- `music_detail_schema.py`: 음악 상세 ViewModel/API 스키마입니다.
- `rag_input_schema.py`: RAG 입력 계약 스키마입니다.
- `rag_state_schema.py`: RAG 상태 계약 스키마입니다.
- `response_state_schema.py`: 응답 상태 계약 스키마입니다.
- `session_context_schema.py`: 세션 컨텍스트 계약 스키마입니다.

#### `app/services/`

- `chatbot_service.py`: 챗봇 응답 유스케이스 서비스입니다.
- `compact_state_builder.py`: 내부 Full State를 API 전송용 Compact State로 축약하는 서비스입니다.
- `logging_service.py`: 로그 기록 관련 서비스입니다.
- `main_recommendation_service.py`: 메인 추천 화면용 추천 유스케이스 서비스입니다.
- `music_detail_service.py`: 음악 상세 조회 유스케이스 서비스입니다.
- `request_lifecycle_cache.py`: 요청 단위 중복 호출/상태 관리를 위한 캐시 서비스입니다.
- `session_cache_service.py`: 세션 캐시 관리 서비스입니다.
- `session_flush_service.py`: 세션 캐시 또는 히스토리 flush 서비스입니다.

#### `app/validators/`

- `base_validator.py`: Validator 공통 기반 모듈입니다.
- `contract_validator.py`: Runtime Contract 구조 검증기입니다.
- `provenance_validator.py`: 응답 출처/근거 검증기입니다.
- `response_validator.py`: 최종 응답 내용 검증기입니다.

### `data/`

데이터 적재 및 가공 결과를 보관하는 폴더입니다.

- `load/.gitkeep`: 적재 대상 데이터 폴더를 Git에 유지하기 위한 파일입니다.
- `processed/matched_spotify_enriched.csv`: 가공된 Spotify 관련 데이터 CSV입니다.

### `db/`

PostgreSQL 스키마와 초기 데이터 적재 스크립트를 관리합니다.

- `schema.sql`: v4 기준 PostgreSQL 테이블 스키마입니다.
- `seed.sql`: 최소 동작을 위한 기본 시드 데이터입니다.
- `init/03-load-source-data.sh`: Docker 초기화 단계에서 소스 데이터를 적재하는 스크립트입니다.

### `docs/`

구현 기준 설계 문서를 보관합니다.

- `rimas_v_4_integrated_design_updated_final_.md`: RIMAS v4 통합 설계 문서입니다. 현재 구현 판단의 기준 문서입니다.

### `neo4j/`

Neo4j 그래프 데이터 적재와 연결 유틸리티를 포함합니다.

- `docker-compose.yml`: Neo4j 단독 또는 관련 서비스 실행 구성입니다.
- `requirements.txt`: Neo4j 데이터 적재 스크립트용 Python 의존성입니다.
- `data_insert.py`: CSV 데이터를 Neo4j에 적재하는 스크립트입니다.
- `common/connection.py`: Neo4j 연결 관리 모듈입니다.
- `common/querys.py`: Neo4j 쿼리 정의 모듈입니다.
- `common/utils.py`: Neo4j 적재 공통 유틸리티입니다.
- `data/artists.csv`: 아티스트 노드/관계 적재 데이터입니다.
- `data/genres.csv`: 장르 노드/관계 적재 데이터입니다.
- `data/moods.csv`: 무드 노드/관계 적재 데이터입니다.
- `data/music_catalog.csv`: 음악 카탈로그 그래프 적재 데이터입니다.
- `data/users.csv`: 사용자 그래프 적재 데이터입니다.

### `seed/`

- `.gitkeep`: 현재는 비어 있는 예약 폴더를 Git에 유지하기 위한 파일입니다.

### `tests/`

백엔드 동작 계약, Runtime Contract, Repository, Service, Validator, Adapter, API 흐름을 검증하는 pytest 테스트 폴더입니다.

- `conftest.py`: pytest 공통 fixture 설정입니다.
- `test_chatbot_service.py`: 챗봇 서비스 테스트입니다.
- `test_common_constants.py`: 공통 상수 계약 테스트입니다.
- `test_contract_enums.py`: 계약 enum/상수 테스트입니다.
- `test_contract_validator.py`: Contract Validator 테스트입니다.
- `test_json_templates.py`: JSON 템플릿 구조 테스트입니다.
- `test_llm_response_state_schema.py`: LLM 응답 상태 스키마 테스트입니다.
- `test_main_recommendation_service.py`: 메인 추천 서비스 테스트입니다.
- `test_mock_kag_adapter.py`: Mock KAG Adapter 테스트입니다.
- `test_mock_rag_adapter.py`: Mock RAG Adapter 테스트입니다.
- `test_music_detail_api.py`: 음악 상세 API 테스트입니다.
- `test_openai_llm_client.py`: OpenAI LLM 클라이언트 테스트입니다.
- `test_provenance_validator.py`: Provenance Validator 테스트입니다.
- `test_rdb_repositories.py`: RDB Repository 테스트입니다.
- `test_response_generator_fallback.py`: 응답 생성 fallback 테스트입니다.
- `test_response_validator.py`: Response Validator 테스트입니다.
- `test_v4_agent_and_detail_flow.py`: v4 Agent 및 음악 상세 흐름 테스트입니다.
- `test_v4_infra_contract.py`: v4 인프라 계약 테스트입니다.
- `test_v4_runtime_contracts.py`: v4 Runtime Contract 테스트입니다.

## 3. `frontend/` 상세 구조

`frontend/`는 React 19, TypeScript, Vite 기반 UI 애플리케이션입니다. React Query로 서버 상태를 조회하고, Zustand로 클라이언트 전역 상태를 관리하며, Axios 기반 API 클라이언트를 통해 백엔드와 통신합니다.

```text
frontend/
├── public/                 # 정적 에셋
├── src/                    # 프론트엔드 소스 코드
├── Dockerfile.dev          # 프론트엔드 개발용 Docker 이미지 정의
├── eslint.config.js        # ESLint 설정
├── index.html              # Vite HTML 진입점
├── package-lock.json       # npm 의존성 잠금 파일
├── package.json            # npm 스크립트 및 의존성 정의
├── README.md               # Vite 템플릿 기본 안내
├── tsconfig.app.json       # 앱 TypeScript 설정
├── tsconfig.json           # TypeScript 프로젝트 참조 설정
├── tsconfig.node.json      # Node/Vite 설정 파일용 TypeScript 설정
└── vite.config.ts          # Vite 빌드/개발 서버 설정
```

### `frontend` 루트 파일

- `Dockerfile.dev`: 프론트엔드 개발 컨테이너 이미지를 정의합니다.
- `eslint.config.js`: TypeScript/React 코드 린트 규칙을 정의합니다.
- `index.html`: Vite가 React 앱을 마운트하는 HTML 엔트리입니다.
- `package.json`: `dev`, `build`, `lint`, `preview` 스크립트와 React, Vite, Axios, Zustand, React Query, Tailwind, Framer Motion 의존성을 정의합니다.
- `package-lock.json`: npm 의존성 버전을 고정합니다.
- `README.md`: Vite 기본 템플릿 안내 문서입니다.
- `tsconfig.app.json`: 브라우저 앱 소스용 TypeScript 컴파일 설정입니다.
- `tsconfig.json`: TypeScript 프로젝트 참조 최상위 설정입니다.
- `tsconfig.node.json`: Vite 설정 등 Node 환경 파일용 TypeScript 설정입니다.
- `vite.config.ts`: Vite 플러그인, 개발 서버, 빌드 설정을 담당합니다.

### `frontend/public/`

브라우저에서 그대로 제공되는 정적 파일 폴더입니다.

- `favicon.svg`: 사이트 파비콘입니다.
- `icons.svg`: 공용 SVG 아이콘 스프라이트 또는 아이콘 리소스입니다.

주의: `MascotCharacter.tsx`는 `/mascot/body.png` 등 mascot 이미지를 참조하지만 현재 `rg --files` 기준으로 `frontend/public/mascot/` 이미지는 확인되지 않습니다. 이미지가 없으면 컴포넌트 내부 fallback UI가 표시됩니다.

### `frontend/src/`

```text
frontend/src/
├── api/                    # 백엔드 API 호출 함수와 Axios 클라이언트
├── components/             # 화면 구성 UI 컴포넌트
├── pages/                  # 페이지 단위 컨테이너
├── stores/                 # Zustand 전역 상태 저장소
├── styles/                 # 테마 상수
├── types/                  # API 응답 및 UI 데이터 타입
├── App.css                 # 앱 전체 스타일
├── App.tsx                 # 앱 루트, 페이지 전환, QueryClient Provider
├── index.css               # 전역 CSS
└── main.tsx                # React DOM 마운트 진입점
```

#### `frontend/src/App.tsx`

프론트엔드 앱의 루트 컴포넌트입니다.

- `QueryClientProvider`를 설정해 React Query를 전역으로 제공합니다.
- 내부 페이지 상태로 `main`과 `chatbot` 화면을 전환합니다.
- `sessionStore`에서 `userId`를 읽고 사용자 선택 UI를 제공합니다.
- `themeStore`에서 다크/라이트 테마 전환을 처리합니다.
- `MainRecommendationPage`와 `ChatbotPage`를 조건부 렌더링합니다.

#### `frontend/src/main.tsx`

React 앱의 브라우저 진입점입니다.

- `createRoot`로 `#root` DOM에 앱을 마운트합니다.
- `StrictMode`로 앱을 감쌉니다.
- 전역 CSS인 `index.css`를 로드합니다.

#### `frontend/src/App.css`

앱 레이아웃, 추천 카드, 상세 모달, 챗봇 UI, 마스코트 등 주요 화면 스타일을 정의하는 CSS 파일입니다.

#### `frontend/src/index.css`

전역 CSS와 기본 스타일을 정의하는 파일입니다.

### `frontend/src/api/`

백엔드 API와 통신하는 경계 계층입니다. UI 컴포넌트는 직접 Axios를 호출하지 않고 이 폴더의 함수들을 통해 API를 호출합니다.

- `client.ts`: 공통 Axios 인스턴스입니다. `VITE_API_URL`을 base URL로 사용하고, 요청/응답 로그 및 에러 로그 인터셉터를 설정합니다.
- `recommendation.ts`: `GET /api/recommendations/main` 호출 함수인 `fetchMainRecommendations`를 제공합니다.
- `musicDetailApi.ts`: `GET /api/music/detail/{content_id}` 호출 함수인 `fetchMusicDetail`을 제공합니다.
- `chatbot.ts`: 챗봇 관련 API 함수입니다. `sendChatMessage`, `fetchSessionHistory`, `flushSession`을 제공합니다.

### `frontend/src/types/`

프론트엔드와 백엔드 API 사이의 TypeScript 계약을 정의합니다.

- `index.ts`: 추천 카드, 메인 추천 ViewModel, 음악 상세 응답, 챗봇 응답 상태, 세션 히스토리 등 API 응답 및 UI 데이터 타입을 정의합니다.

주요 타입:

- `RecommendationCard`: 추천 카드 표시 데이터입니다.
- `MainViewModel`: 메인 추천 화면 ViewModel입니다.
- `MainRecommendationResponse`: 메인 추천 API 응답 타입입니다.
- `MusicDetail`: 음악 상세 모달 표시 데이터입니다.
- `MusicDetailResponse`: 음악 상세 API 응답 타입입니다.
- `ChatDisplayRecommendation`: 챗봇 응답에 포함되는 추천 카드 타입입니다.
- `ResponseState`: 챗봇 최종 응답 상태 타입입니다.
- `ChatbotResponse`: 챗봇 API 응답 타입입니다.
- `ChatTurn`: 세션 대화 이력 한 턴 타입입니다.
- `SessionHistoryResponse`: 세션 히스토리 API 응답 타입입니다.

### `frontend/src/stores/`

Zustand 기반 클라이언트 상태 저장소입니다. 서버에서 조회하는 데이터는 React Query가 담당하고, 여기서는 화면 전역에 필요한 최소 상태를 관리합니다.

- `sessionStore.ts`: 현재 `userId`와 `sessionId`를 관리합니다. 초기 사용자는 `user_001`이고, `sessionId`는 브라우저 실행 시 생성됩니다.
- `chatStore.ts`: 챗봇 대화 이력과 전송 중 상태를 관리합니다. 새 턴 추가, 히스토리 설정, 로딩 상태 변경, 초기화 기능을 제공합니다.
- `themeStore.ts`: `dark`/`light` 테마 상태를 관리합니다. Zustand `persist` middleware로 `rimas-theme`에 저장하고, `document.documentElement`의 `data-theme` 속성을 갱신합니다.

### `frontend/src/pages/`

페이지 단위 컨테이너입니다. API 호출, 상태 연결, 페이지 수준 이벤트를 담당하고 UI 세부 구성은 `components/`에 위임합니다.

- `MainRecommendationPage.tsx`: 메인 추천 화면입니다. React Query로 메인 추천 데이터를 가져오고, 추천 카드 클릭 시 URL query의 `detail` 값을 설정해 음악 상세 모달을 엽니다.
- `ChatbotPage.tsx`: 챗봇 화면입니다. 세션 히스토리를 최초 로드하고, 사용자 입력을 챗봇 API로 전송하며, 응답을 `chatStore` 히스토리에 추가합니다.

### `frontend/src/components/`

UI 컴포넌트 폴더입니다. 현재 `chatbot`, `mascot`, `recommendation` 도메인으로 나뉩니다.

```text
components/
├── chatbot/                # 챗봇 화면 구성 요소
├── mascot/                 # DJ 캐릭터/마스코트
└── recommendation/         # 추천 화면 구성 요소
```

#### `frontend/src/components/chatbot/`

- `ChatbotHeader.tsx`: 챗봇 상단 헤더입니다. 아이콘, `RIMAS DJ` 제목, 현재 `userId`를 표시합니다.
- `ChatHistory.tsx`: 사용자 입력과 봇 응답으로 구성된 대화 히스토리를 표시합니다. 히스토리가 비어 있으면 빈 상태 문구를 표시합니다.
- `ChatInput.tsx`: 챗봇 입력창입니다. Enter 전송, Shift+Enter 줄바꿈, 전송 버튼 비활성화 조건을 처리합니다.
- `RelatedRecommendationCards.tsx`: 챗봇 마지막 응답에 포함된 관련 추천 카드 목록을 표시합니다.

#### `frontend/src/components/mascot/`

- `MascotCharacter.tsx`: Framer Motion 기반 마스코트 컴포넌트입니다. `idle`, `thinking`, `talking`, `recommending`, `fallback` 상태별 애니메이션을 제공하고, `/mascot/` 이미지가 없으면 fallback 표시를 사용합니다.

#### `frontend/src/components/recommendation/`

- `TopTasteHeader.tsx`: 사용자의 취향 배지와 오늘의 테마 문구를 표시하는 추천 화면 상단 헤더입니다.
- `CharacterDjBanner.tsx`: 마스코트와 DJ 메시지를 표시하는 배너입니다. 챗봇 화면으로 이동하는 CTA를 받을 수 있습니다.
- `RecommendationSection.tsx`: 추천 섹션 단위 컴포넌트입니다. 섹션 제목, 라벨, 카드 그리드를 렌더링하고 카드가 없으면 렌더링하지 않습니다.
- `RecommendationCard.tsx`: 개별 추천 음악 카드입니다. 제목, 아티스트, 라벨, 장르/무드 태그, 추천 이유를 표시하고 클릭 시 상세 열기 콜백을 호출합니다.
- `MusicDetailModal.tsx`: 음악 상세 모달입니다. 로딩/에러/성공 상태를 표시하고, 음악 상세 정보와 추천 근거를 보여줍니다.

### `frontend/src/styles/`

- `theme.ts`: 색상, radius, shadow, blur 등 테마 상수를 정의합니다. 현재 코드 기준으로 CSS-in-TS 테마 상수이며, 실제 스타일 대부분은 CSS 파일에서 처리됩니다.

## 4. 프론트엔드 실행 흐름 요약

### 메인 추천 화면

```text
App.tsx
→ MainRecommendationPage.tsx
→ fetchMainRecommendations(userId, sessionId)
→ /api/recommendations/main
→ TopTasteHeader / CharacterDjBanner / RecommendationSection
→ RecommendationCard 클릭
→ URL query detail=<content_id>
→ fetchMusicDetail(contentId)
→ MusicDetailModal
```

### 챗봇 화면

```text
App.tsx
→ ChatbotPage.tsx
→ fetchSessionHistory(sessionId, userId)
→ ChatHistory 렌더링
→ ChatInput 입력
→ sendChatMessage(userId, sessionId, userInput)
→ chatStore.appendTurn(...)
→ RelatedRecommendationCards 렌더링
```

## 5. 확인된 구조상 주의점

- 요청한 `front/` 폴더는 없고 실제 폴더명은 `frontend/`입니다.
- 일부 문서와 UI 문자열은 현재 터미널 출력 기준으로 한글 인코딩이 깨져 보입니다.
- `MascotCharacter.tsx`가 참조하는 `/mascot/*.png` 정적 이미지 파일은 현재 파일 목록에서 확인되지 않습니다.
- `frontend/src/styles/theme.ts`는 테마 상수를 제공하지만, 현재 주요 스타일은 `App.css`와 `index.css`에 집중되어 있습니다.
