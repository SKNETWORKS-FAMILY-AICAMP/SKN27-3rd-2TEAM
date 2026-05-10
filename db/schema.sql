CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS music_catalog (
    content_id VARCHAR(140) PRIMARY KEY,
    track_id VARCHAR(128),
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255),
    genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    moods TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    tempo VARCHAR(32) NOT NULL DEFAULT 'unknown',
    release_type VARCHAR(32) NOT NULL DEFAULT 'unknown',
    recommendation_category VARCHAR(64),
    evidence_summary TEXT,
    source_type VARCHAR(100) NOT NULL DEFAULT 'canonical_music_catalog',
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
    request_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    session_id VARCHAR(100),
    user_input TEXT,
    page_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    response_type VARCHAR(64),
    intent_type VARCHAR(64),
    validation_status VARCHAR(32) NOT NULL,
    error_type VARCHAR(100),
    compact_kag_state_json JSONB NOT NULL,
    compact_rag_state_json JSONB NOT NULL,
    compact_response_state_json JSONB NOT NULL,
    validation_result_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_interaction_logs_page_type
        CHECK (page_type IN ('main_recommendation_page', 'chatbot_page', 'music_detail_page')),
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
        )
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    turn_count INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_session_turns (
    turn_id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    user_input TEXT NOT NULL DEFAULT '',
    chatbot_response TEXT NOT NULL DEFAULT '',
    response_state_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS detail_view_logs (
    detail_log_id BIGSERIAL PRIMARY KEY,
    request_id VARCHAR(100),
    user_id VARCHAR(64) REFERENCES users(user_id),
    session_id VARCHAR(100),
    content_id VARCHAR(140) NOT NULL REFERENCES music_catalog(content_id),
    source VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_music_catalog_track_id
ON music_catalog(track_id);

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

CREATE INDEX IF NOT EXISTS idx_interaction_logs_request_id
ON interaction_logs(request_id);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_user_created_at
ON interaction_logs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_session_created_at
ON interaction_logs(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_validation_status
ON interaction_logs(validation_status);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_kag_compact_gin
ON interaction_logs USING GIN (compact_kag_state_json);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_rag_compact_gin
ON interaction_logs USING GIN (compact_rag_state_json);

CREATE INDEX IF NOT EXISTS idx_interaction_logs_response_compact_gin
ON interaction_logs USING GIN (compact_response_state_json);

CREATE INDEX IF NOT EXISTS idx_chat_session_turns_session_created_at
ON chat_session_turns(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_detail_view_logs_content_created_at
ON detail_view_logs(content_id, created_at DESC);
