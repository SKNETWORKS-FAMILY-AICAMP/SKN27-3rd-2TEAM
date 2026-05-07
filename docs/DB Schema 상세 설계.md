# RIMAS DB Schema 상세 설계 v1
# PostgreSQL 기준

---

# 1. 문서 목적

본 문서는 RIMAS v2의 DB 저장 구조를 정의한다.

DB는 다음 목적을 가진다.

1. ML Output 조회
2. 사용자 입력/응답 로그 저장
3. KAG_STATE / RAG_STATE 원본 저장
4. LLM Response 저장
5. Validation 결과 저장
6. fallback/error 추적
7. 데모 및 테스트 재현 가능성 확보

---

# 2. DB 설계 원칙

## 2.1 JSON 원본 보존

ML Output, KAG_STATE, RAG_STATE, RESPONSE_STATE는 JSONB로 원본 그대로 저장한다.

이유:
- 계약 검증 가능
- 디버깅 가능
- Mock → Real Adapter 교체 시 구조 추적 가능
- LLM 응답 provenance 검증 가능

---

## 2.2 정규 컬럼 + JSONB 혼합

자주 조회하는 값은 일반 컬럼으로 분리한다.

예:
- user_id
- status
- validation_status
- error_type
- response_type
- primary_goal
- intent_type
- latency_ms
- created_at

상세 원본은 JSONB로 저장한다.

---

## 2.3 로그 누적 저장

interaction_logs는 append-only 방식으로 저장한다.

금지:
- 기존 로그 덮어쓰기 금지
- 성공 로그만 저장 금지
- 실패 로그 누락 금지

---

# 3. 테이블 목록

필수 테이블:

1. users
2. ml_outputs
3. music_catalog
4. interaction_logs

선택 테이블:

5. llm_call_logs
6. validation_logs

MVP에서는 1~4번을 우선 구현한다.

## Source Layer 분리 원칙

Spotify/KKBOX 원천 데이터 기반 확장 테이블은 기존 Runtime Contract와 분리된 Source Layer로 관리한다.

Source Layer 테이블:

- `spotify_tracks`
- `spotify_audio_features`
- `spotify_lyrics`
- `spotify_emotions`
- `kkbox_user_features`
- `user_music_profiles`

Runtime Contract Layer 테이블:

- `users`
- `ml_outputs`
- `music_catalog`
- `interaction_logs`
- 선택: `llm_call_logs`
- 선택: `validation_logs`

Service Layer는 Source Layer 테이블을 직접 조회하지 않는다. Source Layer 데이터는 loader, transformer, validator, catalog/profile build process를 거쳐 `music_catalog`와 `ml_outputs`에 반영한 뒤 Runtime Repository를 통해 사용한다.

`interaction_logs.primary_goal`, `intent_type`, `target_page`, `primary_section`은 기존 Service Flow 로그 계약이므로 유지한다.

Source Repository에서 사용하는 SQL도 Repository Layer 책임이므로 `app/repositories/query_constants.py`에 상수로 정의한다.

---

# 4. users 테이블

## 목적

사용자 기본 정보를 저장한다.

## DDL

CREATE TABLE users (
    user_id VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

## 컬럼 설명

user_id:
- 사용자 식별자
- ML Output, interaction_logs와 연결

display_name:
- UI 표시용 이름
- 없으면 user_id 사용

created_at:
- 생성 시각

updated_at:
- 수정 시각

---

# 5. ml_outputs 테이블

## 목적

사용자 기반 추천에 필요한 ML Output을 저장한다.

## DDL

CREATE TABLE ml_outputs (
    ml_output_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),

    status VARCHAR(32) NOT NULL,

    preferred_genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    preferred_artists TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    preferred_moods TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    preferred_tempo VARCHAR(32) NOT NULL DEFAULT 'unknown',

    recent_listening_level VARCHAR(32) NOT NULL,
    recent_discovery_level VARCHAR(32) NOT NULL,
    repeat_listening_ratio NUMERIC(5,4) NOT NULL,
    new_artist_acceptance NUMERIC(5,4) NOT NULL,

    personalization_strength VARCHAR(32) NOT NULL,
    discovery_readiness VARCHAR(32) NOT NULL,
    new_release_affinity VARCHAR(32) NOT NULL,

    ml_output_json JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

## 제약 조건

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_ml_outputs_status
CHECK (status IN ('success', 'partial_match', 'empty_result', 'timeout', 'error'));

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_recent_listening_level
CHECK (recent_listening_level IN ('low', 'medium', 'high'));

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_recent_discovery_level
CHECK (recent_discovery_level IN ('low', 'medium', 'high'));

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_repeat_listening_ratio
CHECK (repeat_listening_ratio >= 0 AND repeat_listening_ratio <= 1);

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_new_artist_acceptance
CHECK (new_artist_acceptance >= 0 AND new_artist_acceptance <= 1);

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_personalization_strength
CHECK (personalization_strength IN ('low', 'medium', 'high'));

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_discovery_readiness
CHECK (discovery_readiness IN ('low', 'medium', 'high'));

ALTER TABLE ml_outputs
ADD CONSTRAINT chk_new_release_affinity
CHECK (new_release_affinity IN ('low', 'medium', 'high'));

## 인덱스

CREATE INDEX idx_ml_outputs_user_id
ON ml_outputs(user_id);

CREATE INDEX idx_ml_outputs_user_created_at
ON ml_outputs(user_id, created_at DESC);

CREATE INDEX idx_ml_outputs_status
ON ml_outputs(status);

CREATE INDEX idx_ml_outputs_json_gin
ON ml_outputs USING GIN (ml_output_json);

## 조회 기준

기본 조회:
- user_id 기준 최신 ML Output 1건

SQL 상수 예시:
SELECT_LATEST_ML_OUTPUT_BY_USER_ID =
SELECT *
FROM ml_outputs
WHERE user_id = :user_id
ORDER BY created_at DESC
LIMIT 1;

---

# 6. music_catalog 테이블

## 목적

RAG Mock 또는 Real RAG가 참조할 수 있는 음악 후보 데이터를 저장한다.

MVP에서는 Mock 데이터 기반으로 사용한다.

## DDL

CREATE TABLE music_catalog (
    content_id VARCHAR(64) PRIMARY KEY,

    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255),

    genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    moods TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    tempo VARCHAR(32) NOT NULL DEFAULT 'unknown',

    release_type VARCHAR(32) NOT NULL DEFAULT 'unknown',
    recommendation_category VARCHAR(64),

    evidence_summary TEXT,
    source_type VARCHAR(100) NOT NULL DEFAULT 'mock_music_catalog',

    metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

## 제약 조건

ALTER TABLE music_catalog
ADD CONSTRAINT chk_music_catalog_tempo
CHECK (tempo IN ('slow', 'medium', 'fast', 'unknown'));

ALTER TABLE music_catalog
ADD CONSTRAINT chk_music_catalog_release_type
CHECK (release_type IN ('existing_catalog', 'new_release', 'updated_playlist', 'unknown'));

ALTER TABLE music_catalog
ADD CONSTRAINT chk_music_catalog_recommendation_category
CHECK (
    recommendation_category IS NULL OR
    recommendation_category IN (
        'personalized_match',
        'similar_taste',
        'new_release',
        'discovery_candidate',
        'information_related'
    )
);

## 인덱스

CREATE INDEX idx_music_catalog_release_type
ON music_catalog(release_type);

CREATE INDEX idx_music_catalog_recommendation_category
ON music_catalog(recommendation_category);

CREATE INDEX idx_music_catalog_genres_gin
ON music_catalog USING GIN (genres);

CREATE INDEX idx_music_catalog_moods_gin
ON music_catalog USING GIN (moods);

CREATE INDEX idx_music_catalog_metadata_gin
ON music_catalog USING GIN (metadata_json);

## 사용 방식

RAG Mock 단계:
- music_catalog에서 추천 후보 조회
- KAG_STATE의 content_requirements 기준으로 필터링
- RAG_STATE.recommended_content_evidence 생성

Real RAG 단계:
- 외부 Vector DB 또는 RAG 모듈 결과를 우선 사용
- music_catalog는 fallback 또는 데모 데이터로 사용 가능

---

# 7. interaction_logs 테이블

## 목적

사용자 요청부터 최종 응답까지 전체 결과를 누적 저장한다.

저장 대상:
- user_input
- ML Output
- KAG_STATE
- RAG_STATE
- RESPONSE_STATE
- validation 결과
- error 정보
- latency

## DDL

CREATE TABLE interaction_logs (
    log_id VARCHAR(100) PRIMARY KEY,

    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    user_input TEXT,

    page_type VARCHAR(64) NOT NULL,

    status VARCHAR(32) NOT NULL,
    response_type VARCHAR(64),

    primary_goal VARCHAR(64),
    intent_type VARCHAR(64),
    target_page VARCHAR(64),
    primary_section VARCHAR(64),

    validation_status VARCHAR(32) NOT NULL,
    error_type VARCHAR(100),

    ml_output_json JSONB,
    kag_state_json JSONB,
    rag_state_json JSONB,
    response_state_json JSONB,
    validation_result_json JSONB,

    latency_ms INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

## 제약 조건

ALTER TABLE interaction_logs
ADD CONSTRAINT chk_interaction_logs_page_type
CHECK (page_type IN ('main_recommendation_page', 'chatbot_page'));

ALTER TABLE interaction_logs
ADD CONSTRAINT chk_interaction_logs_status
CHECK (status IN ('success', 'partial_match', 'empty_result', 'timeout', 'error'));

ALTER TABLE interaction_logs
ADD CONSTRAINT chk_interaction_logs_validation_status
CHECK (validation_status IN ('success', 'failed', 'fallback'));

ALTER TABLE interaction_logs
ADD CONSTRAINT chk_interaction_logs_response_type
CHECK (
    response_type IS NULL OR
    response_type IN (
        'curator_recommendation',
        'curator_information',
        'recommendation_reason',
        'fallback'
    )
);

ALTER TABLE interaction_logs
ADD CONSTRAINT chk_interaction_logs_error_type
CHECK (
    error_type IS NULL OR
    error_type IN (
        'ML_OUTPUT_NOT_FOUND',
        'KAG_STATE_ERROR',
        'RAG_STATE_ERROR',
        'CONTRACT_VALIDATION_FAILED',
        'LLM_CALL_FAILED',
        'RESPONSE_VALIDATION_FAILED',
        'PROVENANCE_VALIDATION_FAILED',
        'UNKNOWN_ERROR'
    )
);

ALTER TABLE interaction_logs
ADD CONSTRAINT chk_interaction_logs_latency
CHECK (latency_ms IS NULL OR latency_ms >= 0);

## 인덱스

CREATE INDEX idx_interaction_logs_user_id
ON interaction_logs(user_id);

CREATE INDEX idx_interaction_logs_user_created_at
ON interaction_logs(user_id, created_at DESC);

CREATE INDEX idx_interaction_logs_page_type
ON interaction_logs(page_type);

CREATE INDEX idx_interaction_logs_status
ON interaction_logs(status);

CREATE INDEX idx_interaction_logs_validation_status
ON interaction_logs(validation_status);

CREATE INDEX idx_interaction_logs_error_type
ON interaction_logs(error_type);

CREATE INDEX idx_interaction_logs_primary_goal
ON interaction_logs(primary_goal);

CREATE INDEX idx_interaction_logs_intent_type
ON interaction_logs(intent_type);

CREATE INDEX idx_interaction_logs_created_at
ON interaction_logs(created_at DESC);

CREATE INDEX idx_interaction_logs_kag_json_gin
ON interaction_logs USING GIN (kag_state_json);

CREATE INDEX idx_interaction_logs_rag_json_gin
ON interaction_logs USING GIN (rag_state_json);

CREATE INDEX idx_interaction_logs_response_json_gin
ON interaction_logs USING GIN (response_state_json);

## 저장 규칙

1. success, fallback, error 모두 저장한다.
2. Validation 실패 응답은 status=error 또는 validation_status=failed로 저장한다.
3. fallback 응답은 validation_status=fallback으로 저장한다.
4. raw JSON은 수정하지 않고 그대로 저장한다.
5. UI에 표시하지 않는 내부 데이터도 Debug 및 재현성을 위해 저장한다.

---

# 8. 선택 테이블: llm_call_logs

## 목적

LLM 호출 이력을 별도로 저장한다.

MVP에서는 interaction_logs만으로 충분하지만, LLM 디버깅이 필요하면 추가한다.

## DDL

CREATE TABLE llm_call_logs (
    llm_call_id BIGSERIAL PRIMARY KEY,

    log_id VARCHAR(100) REFERENCES interaction_logs(log_id),

    provider VARCHAR(64) NOT NULL,
    model_name VARCHAR(128) NOT NULL,

    request_json JSONB,
    response_json JSONB,

    status VARCHAR(32) NOT NULL,
    error_message TEXT,

    latency_ms INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

## 제약 조건

ALTER TABLE llm_call_logs
ADD CONSTRAINT chk_llm_call_logs_status
CHECK (status IN ('success', 'timeout', 'error'));

## 인덱스

CREATE INDEX idx_llm_call_logs_log_id
ON llm_call_logs(log_id);

CREATE INDEX idx_llm_call_logs_status
ON llm_call_logs(status);

CREATE INDEX idx_llm_call_logs_created_at
ON llm_call_logs(created_at DESC);

---

# 9. 선택 테이블: validation_logs

## 목적

Contract / Response / Provenance 검증 결과를 세부적으로 저장한다.

MVP에서는 interaction_logs.validation_result_json으로 충분하다.

검증을 상세하게 추적해야 하면 별도 테이블로 분리한다.

## DDL

CREATE TABLE validation_logs (
    validation_log_id BIGSERIAL PRIMARY KEY,

    log_id VARCHAR(100) REFERENCES interaction_logs(log_id),

    validation_type VARCHAR(64) NOT NULL,
    validation_status VARCHAR(32) NOT NULL,

    error_path TEXT,
    error_message TEXT,
    validation_detail_json JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

## 제약 조건

ALTER TABLE validation_logs
ADD CONSTRAINT chk_validation_logs_type
CHECK (validation_type IN ('contract', 'response', 'provenance'));

ALTER TABLE validation_logs
ADD CONSTRAINT chk_validation_logs_status
CHECK (validation_status IN ('success', 'failed'));

## 인덱스

CREATE INDEX idx_validation_logs_log_id
ON validation_logs(log_id);

CREATE INDEX idx_validation_logs_type
ON validation_logs(validation_type);

CREATE INDEX idx_validation_logs_status
ON validation_logs(validation_status);

---

# 10. Seed Data 기준

## 10.1 users seed

INSERT INTO users (user_id, display_name)
VALUES
('user_001', 'user_001'),
('user_002', 'user_002'),
('user_003', 'user_003');

---

## 10.2 ml_outputs seed

user_001:
- rnb / indie
- calm / night
- personalized high
- discovery medium

user_002:
- pop / dance
- bright / energetic
- new_release high

user_003:
- ballad / acoustic
- soft / calm
- discovery low

---

## 10.3 music_catalog seed

필수 추천 카테고리별 최소 데이터:

personalized_match:
- 기존 취향과 직접 연결되는 곡

similar_taste:
- 기존 취향과 유사한 곡

new_release:
- 최신 업데이트 곡

discovery_candidate:
- 새 취향 탐색 후보

information_related:
- 정보 설명과 연결 가능한 곡 또는 메타데이터

---

# 11. Repository 파일 매핑

repositories/
  query_constants.py
  ml_output_repository.py
  music_catalog_repository.py
  interaction_log_repository.py
  llm_call_log_repository.py
  validation_log_repository.py

---

# 12. query_constants.py 기준

SQL은 코드 내부에 직접 작성하지 않는다.
모든 SQL은 query_constants.py에 상수로 정의한다.

필수 Query 상수:

1. SELECT_LATEST_ML_OUTPUT_BY_USER_ID
2. SELECT_MUSIC_BY_CONTENT_REQUIREMENTS
3. INSERT_INTERACTION_LOG
4. SELECT_INTERACTION_LOGS_BY_USER_ID
5. INSERT_LLM_CALL_LOG
6. INSERT_VALIDATION_LOG

---

# 13. 필수 Repository 책임

## 13.1 MlOutputRepository

메서드:
- get_latest_by_user_id(user_id)

역할:
- user_id 기준 최신 ML Output 조회
- 없으면 None 반환

금지:
- ML Output 재계산 금지
- JSON 수정 금지

---

## 13.2 MusicCatalogRepository

메서드:
- find_by_categories(categories)
- find_by_release_type(release_type)
- find_by_genres(genres)
- find_by_moods(moods)

역할:
- Mock RAG 후보 조회

금지:
- 최종 RAG_STATE 생성 금지
- LLM 호출 금지

---

## 13.3 InteractionLogRepository

메서드:
- save(log)
- find_by_user_id(user_id)
- find_recent(limit)

역할:
- interaction_logs 저장 및 조회

금지:
- validation 결과 조작 금지
- response_state 수정 금지

---

# 14. 실무적 선택지

[방안 01: interaction_logs 단일 로그 중심]
- 특징: 대부분의 실행 결과를 interaction_logs에 JSONB로 저장
- 장점: 구현 빠름, MVP에 적합, 디버깅 쉬움
- 단점: LLM 호출/검증 로그를 세밀하게 분석하기는 어려움
- 실무적 관점의 제언: 1주 MVP에서는 가장 적합

[방안 02: interaction_logs + llm_call_logs 분리]
- 특징: 사용자 흐름 로그와 LLM 호출 로그를 분리
- 장점: LLM 실패/latency 분석이 쉬움
- 단점: 구현량 증가
- 실무적 관점의 제언: LLM 호출 안정성까지 보여줘야 한다면 적합

[방안 03: interaction_logs + llm_call_logs + validation_logs 분리]
- 특징: 실행 로그, LLM 로그, 검증 로그 완전 분리
- 장점: 운영 분석과 디버깅에 가장 강함
- 단점: MVP에는 과함
- 실무적 관점의 제언: 실제 서비스 운영 단계에서 적합

추천:
- 현재는 방안 01로 구현한다.
- 단, DDL은 02/03으로 확장 가능하게 유지한다.
- 시간이 남으면 llm_call_logs만 추가한다.

---

# 15. 최종 DB 구현 우선순위

1순위:
- users
- ml_outputs
- music_catalog
- interaction_logs

2순위:
- query_constants.py
- Repository 구현

3순위:
- Seed Data 작성

4순위:
- llm_call_logs 선택 구현

5순위:
- validation_logs 선택 구현

---

# 16. 완료 기준

DB 설계 완료 기준:

- users 테이블 생성 가능
- ml_outputs 테이블 생성 가능
- music_catalog 테이블 생성 가능
- interaction_logs 테이블 생성 가능
- JSONB 원본 저장 가능
- user_id 기준 최신 ML Output 조회 가능
- user_id 기준 interaction_logs 조회 가능
- status / validation_status / error_type 필터링 가능
- RAG Mock 후보 조회 가능
- 모든 SQL은 query_constants.py로 분리 가능
- Repository Layer에서만 DB 접근 가능
