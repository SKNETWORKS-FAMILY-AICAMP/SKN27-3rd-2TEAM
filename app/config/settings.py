import os

APP_ENV = os.getenv("APP_ENV", "local").lower()
_PROD_ENVS = {"prod", "production"}

# PostgreSQL
DB_HOST = os.getenv("RIMAS_DB_HOST", "localhost")
DB_PORT = int(os.getenv("RIMAS_DB_PORT", "5432"))
DB_NAME = os.getenv("RIMAS_DB_NAME", "rimas")
DB_USER = os.getenv("RIMAS_DB_USER", "rimas")
DB_PASSWORD = os.getenv("RIMAS_DB_PASSWORD", "")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_SESSION_TTL = int(os.getenv("REDIS_SESSION_TTL", "7200"))  # 2 hours

# Neo4j
RIMAS_NEO4J_URI = os.getenv("RIMAS_NEO4J_URI", "bolt://localhost:7687")
RIMAS_NEO4J_USER = os.getenv("RIMAS_NEO4J_USER", "neo4j")
RIMAS_NEO4J_PASSWORD = os.getenv("RIMAS_NEO4J_PASSWORD", "")

# Elasticsearch
RIMAS_ELASTICSEARCH_URL = os.getenv("RIMAS_ELASTICSEARCH_URL", "http://localhost:9200")
RIMAS_ELASTICSEARCH_INDEX = os.getenv("RIMAS_ELASTICSEARCH_INDEX", "spotify_songs")
RIMAS_ELASTICSEARCH_TIMEOUT = float(os.getenv("RIMAS_ELASTICSEARCH_TIMEOUT_SECONDS", "3"))

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
RIMAS_LLM_MODEL = os.getenv("RIMAS_LLM_MODEL", "GPT-5.4 mini")
RIMAS_LLM_TIMEOUT = float(os.getenv("RIMAS_LLM_TIMEOUT_SECONDS", "30"))

# CORS
_cors_default = "" if APP_ENV in _PROD_ENVS else "http://localhost:5173"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", _cors_default).split(",")

# ── prod fail-fast ────────────────────────────────────────────────────────────
if APP_ENV in _PROD_ENVS:
    _missing = [
        name for name, value in [
            ("RIMAS_DB_PASSWORD", DB_PASSWORD),
            ("RIMAS_NEO4J_PASSWORD", RIMAS_NEO4J_PASSWORD),
            ("OPENAI_API_KEY", OPENAI_API_KEY),
            ("CORS_ORIGINS", os.getenv("CORS_ORIGINS", "")),
        ]
        if not value
    ]
    if _missing:
        raise EnvironmentError(
            f"[RIMAS] prod 환경에서 필수 환경 변수가 누락되었습니다: {', '.join(_missing)}"
        )
# ─────────────────────────────────────────────────────────────────────────────


def get_database_config() -> dict:
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }


def create_database_connection():
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2 is required") from exc
    return psycopg2.connect(**get_database_config())
