from pathlib import Path


SCHEMA_SQL = Path("db/schema.sql").read_text(encoding="utf-8")


def test_source_layer_tables_are_declared():
    expected_tables = (
        "spotify_tracks",
        "spotify_audio_features",
        "spotify_lyrics",
        "spotify_emotions",
        "kkbox_user_features",
        "user_music_profiles",
    )

    for table_name in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in SCHEMA_SQL


def test_users_keep_runtime_identity_and_add_source_identity():
    assert "user_id VARCHAR(64) PRIMARY KEY" in SCHEMA_SQL
    assert "source_user_id VARCHAR(128)" in SCHEMA_SQL
    assert "source_type VARCHAR(50) NOT NULL DEFAULT 'internal'" in SCHEMA_SQL
    assert "chk_users_source_type" in SCHEMA_SQL


def test_music_catalog_links_to_spotify_source_without_relaxing_runtime_contract():
    assert "content_id VARCHAR(140) PRIMARY KEY" in SCHEMA_SQL
    assert (
        "track_id VARCHAR(128) REFERENCES spotify_tracks(track_id) ON DELETE SET NULL"
        in SCHEMA_SQL
    )
    assert "artist VARCHAR(255) NOT NULL" in SCHEMA_SQL
    assert "source_type VARCHAR(100) NOT NULL DEFAULT 'mock_music_catalog'" in SCHEMA_SQL
    assert "recommendation_category VARCHAR(64)" in SCHEMA_SQL
    assert "chk_music_catalog_recommendation_category" in SCHEMA_SQL


def test_interaction_logs_keep_existing_service_flow_columns():
    required_columns = (
        "primary_goal VARCHAR(64)",
        "intent_type VARCHAR(64)",
        "target_page VARCHAR(64)",
        "primary_section VARCHAR(64)",
    )

    for column_definition in required_columns:
        assert column_definition in SCHEMA_SQL


def test_ml_outputs_not_relaxed_to_nullable_placeholder_in_this_patch():
    required_definitions = (
        "status VARCHAR(32) NOT NULL",
        "preferred_genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[]",
        "ml_output_json JSONB NOT NULL",
    )

    for column_definition in required_definitions:
        assert column_definition in SCHEMA_SQL
