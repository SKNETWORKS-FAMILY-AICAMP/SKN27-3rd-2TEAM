import os


DB_HOST = os.getenv("RIMAS_DB_HOST", "localhost")
DB_PORT = int(os.getenv("RIMAS_DB_PORT", "5432"))
DB_NAME = os.getenv("RIMAS_DB_NAME", "rimas")
DB_USER = os.getenv("RIMAS_DB_USER", "rimas")
DB_PASSWORD = os.getenv("RIMAS_DB_PASSWORD", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
RIMAS_LLM_MODEL = os.getenv("RIMAS_LLM_MODEL", "gpt-4.1-mini")
RIMAS_LLM_TIMEOUT_SECONDS = float(os.getenv("RIMAS_LLM_TIMEOUT_SECONDS", "30"))


def get_database_config():
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
        raise RuntimeError("psycopg2 is required for PostgreSQL connection") from exc

    # DB 연결 정보는 환경 변수에서만 가져와 하드코딩을 피한다.
    return psycopg2.connect(**get_database_config())
