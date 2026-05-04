CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml_outputs (
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ml_outputs_status
        CHECK (status IN ('success', 'partial_match', 'empty_result', 'timeout', 'error')),
    CONSTRAINT chk_recent_listening_level
        CHECK (recent_listening_level IN ('low', 'medium', 'high')),
    CONSTRAINT chk_recent_discovery_level
        CHECK (recent_discovery_level IN ('low', 'medium', 'high')),
    CONSTRAINT chk_repeat_listening_ratio
        CHECK (repeat_listening_ratio >= 0 AND repeat_listening_ratio <= 1),
    CONSTRAINT chk_new_artist_acceptance
        CHECK (new_artist_acceptance >= 0 AND new_artist_acceptance <= 1),
    CONSTRAINT chk_personalization_strength
        CHECK (personalization_strength IN ('low', 'medium', 'high')),
    CONSTRAINT chk_discovery_readiness
        CHECK (discovery_readiness IN ('low', 'medium', 'high')),
    CONSTRAINT chk_new_release_affinity
        CHECK (new_release_affinity IN ('low', 'medium', 'high'))
);

CREATE TABLE IF NOT EXISTS music_catalog (
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
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_music_catalog_tempo
        CHECK (tempo IN ('slow', 'medium', 'fast', 'unknown')),
    CONSTRAINT chk_music_catalog_release_type
        CHECK (release_type IN ('existing_catalog', 'new_release', 'updated_playlist', 'unknown')),
    CONSTRAINT chk_music_catalog_recommendation_category
        CHECK (
            recommendation_category IS NULL OR
            recommendation_category IN (
                'personalized_match',
                'similar_taste',
                'new_release',
                'discovery_candidate',
                'information_related'
            )
        )
);

CREATE TABLE IF NOT EXISTS interaction_logs (
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_interaction_logs_page_type
        CHECK (page_type IN ('main_recommendation_page', 'chatbot_page')),
    CONSTRAINT chk_interaction_logs_status
        CHECK (status IN ('success', 'partial_match', 'empty_result', 'timeout', 'error')),
    CONSTRAINT chk_interaction_logs_validation_status
        CHECK (validation_status IN ('success', 'failed', 'fallback')),
    CONSTRAINT chk_interaction_logs_response_type
        CHECK (
            response_type IS NULL OR
            response_type IN (
                'curator_recommendation',
                'curator_information',
                'recommendation_reason',
                'fallback'
            )
        ),
    CONSTRAINT chk_interaction_logs_error_type
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
        ),
    CONSTRAINT chk_interaction_logs_latency
        CHECK (latency_ms IS NULL OR latency_ms >= 0)
);

CREATE INDEX IF NOT EXISTS idx_ml_outputs_user_id
ON ml_outputs(user_id);

CREATE INDEX IF NOT EXISTS idx_ml_outputs_user_created_at
ON ml_outputs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ml_outputs_status
ON ml_outputs(status);

CREATE INDEX IF NOT EXISTS idx_ml_outputs_json_gin
ON ml_outputs USING GIN (ml_output_json);

CREATE INDEX IF NOT EXISTS idx_music_catalog_release_type
ON music_catalog(release_type);

CREATE INDEX IF NOT EXISTS idx_music_catalog_recommendation_category
ON music_catalog(recommendation_category);

CREATE INDEX IF NOT EXISTS idx_music_catalog_genres_gin
ON music_catalog USING GIN (genres);

CREATE INDEX IF NOT EXISTS idx_music_catalog_moods_gin
ON music_catalog USING GIN (moods);

CREATE INDEX IF NOT EXISTS idx_music_catalog_metadata_gin
ON music_catalog USING GIN (metadata_json);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_user_id
ON interaction_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_user_created_at
ON interaction_logs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_page_type
ON interaction_logs(page_type);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_status
ON interaction_logs(status);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_validation_status
ON interaction_logs(validation_status);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_error_type
ON interaction_logs(error_type);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_primary_goal
ON interaction_logs(primary_goal);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_intent_type
ON interaction_logs(intent_type);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_created_at
ON interaction_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_kag_json_gin
ON interaction_logs USING GIN (kag_state_json);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_rag_json_gin
ON interaction_logs USING GIN (rag_state_json);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_response_json_gin
ON interaction_logs USING GIN (response_state_json);
