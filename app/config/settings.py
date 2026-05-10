import os

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

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
RIMAS_LLM_MODEL = os.getenv("RIMAS_LLM_MODEL", "gpt-4.1-mini")
RIMAS_LLM_TIMEOUT = float(os.getenv("RIMAS_LLM_TIMEOUT_SECONDS", "30"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


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
