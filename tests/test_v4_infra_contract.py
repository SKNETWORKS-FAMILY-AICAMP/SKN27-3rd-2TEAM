from pathlib import Path


ROOT = Path(".")
SCHEMA = ROOT / "db" / "schema.sql"
SEED = ROOT / "db" / "seed.sql"
INIT_SCRIPT = ROOT / "db" / "init" / "03-load-source-data.sh"
COMPOSE_FILE = ROOT / "docker-compose.yml"
DOCKERFILE = ROOT / "Dockerfile"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v4_schema_uses_minimal_postgres_tables():
    sql = read(SCHEMA)

    expected_tables = (
        "CREATE TABLE IF NOT EXISTS users",
        "CREATE TABLE IF NOT EXISTS music_catalog",
        "CREATE TABLE IF NOT EXISTS interaction_logs",
        "CREATE TABLE IF NOT EXISTS chat_sessions",
        "CREATE TABLE IF NOT EXISTS chat_session_turns",
        "CREATE TABLE IF NOT EXISTS detail_view_logs",
    )
    forbidden_tables = (
        "CREATE TABLE IF NOT EXISTS ml_outputs",
        "CREATE TABLE IF NOT EXISTS kkbox_user_features",
        "CREATE TABLE IF NOT EXISTS user_music_profiles",
        "CREATE TABLE IF NOT EXISTS spotify_lyrics",
        "CREATE TABLE IF NOT EXISTS spotify_emotions",
    )

    for fragment in expected_tables:
        assert fragment in sql
    for fragment in forbidden_tables:
        assert fragment not in sql


def test_interaction_logs_store_compact_state_and_request_id():
    sql = read(SCHEMA)
    interaction_logs_sql = sql.split("CREATE TABLE IF NOT EXISTS chat_sessions", maxsplit=1)[0]

    expected_columns = (
        "request_id VARCHAR(100) NOT NULL",
        "compact_kag_state_json JSONB NOT NULL",
        "compact_rag_state_json JSONB NOT NULL",
        "compact_response_state_json JSONB NOT NULL",
        "validation_status VARCHAR(32) NOT NULL",
        "latency_ms INTEGER",
        "error_type VARCHAR(100)",
    )
    forbidden_columns = (
        "    ml_output_json ",
        "    kag_state_json ",
        "    rag_state_json ",
        "    response_state_json ",
    )

    for fragment in expected_columns:
        assert fragment in interaction_logs_sql
    for fragment in forbidden_columns:
        assert fragment not in interaction_logs_sql


def test_seed_sql_does_not_insert_ml_output():
    sql = read(SEED)

    assert "INSERT INTO ml_outputs" not in sql
    assert "INSERT INTO users" in sql
    assert "INSERT INTO music_catalog" in sql


def test_v4_init_script_only_loads_minimal_seed():
    script = read(INIT_SCRIPT)

    assert "set -eu" in script
    assert "db/seed.sql" in script
    assert "load_kkbox_seed.sql" not in script
    assert "verify_source_load.sql" not in script


def test_dockerfile_runs_fastapi_on_port_8000():
    dockerfile = read(DOCKERFILE)

    assert "EXPOSE 8000" in dockerfile
    assert "uvicorn" in dockerfile
    assert "streamlit" not in dockerfile
    assert "8501" not in dockerfile


def test_taste_tables_exist_in_schema():
    sql = read(SCHEMA)

    assert "CREATE TABLE IF NOT EXISTS user_taste_events" in sql
    assert "CREATE TABLE IF NOT EXISTS user_taste_profiles" in sql
    assert "idx_user_taste_events_user_created_at" in sql
    assert "idx_user_taste_profiles_updated_at" in sql


def test_compose_defines_v4_runtime_services():
    compose = read(COMPOSE_FILE)

    expected_fragments = (
        "backend:",
        "frontend:",
        "db:",
        "redis:",
        "neo4j:",
        "elasticsearch:",
        "${NEO4J_BROWSER_PORT:-7474}:7474",
        "${NEO4J_BOLT_PORT:-7687}:7687",
        "${ELASTICSEARCH_PORT:-9200}:9200",
        "RIMAS_NEO4J_URI:",
        "RIMAS_ELASTICSEARCH_URL:",
    )

    for fragment in expected_fragments:
        assert fragment in compose
