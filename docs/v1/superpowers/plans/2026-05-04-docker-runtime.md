# Docker Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Streamlit app and PostgreSQL can run together through Docker Compose while preserving the existing `RIMAS_DB_*` configuration contract.

**Architecture:** `Dockerfile` owns only the Python Streamlit application image. `docker-compose.yml` owns runtime wiring between the `app` service and the PostgreSQL `db` service, and mounts existing `db/schema.sql` and `db/seed.sql` as PostgreSQL initialization scripts.

**Tech Stack:** Docker, Docker Compose, Python 3.11, Streamlit, PostgreSQL, psycopg2.

---

### Task 1: Application Container Files

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `requirements.txt`

- [x] **Step 1: Add Python dependency list**

Create `requirements.txt` with the runtime and test dependencies already used by the project:

```text
pydantic>=2.0,<3.0
psycopg2-binary>=2.9,<3.0
pytest>=8.0,<9.0
streamlit>=1.30,<2.0
```

- [x] **Step 2: Add Streamlit Dockerfile**

Create `Dockerfile` using the existing `app/main.py` entry point:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

- [x] **Step 3: Add Docker ignore rules**

Create `.dockerignore` to keep local runtime and repository metadata out of the app image:

```text
.git
.pytest_cache
.ruff_cache
.mypy_cache
.venv
venv
env
__pycache__
*.pyc
*.pyo
*.log
.env
.env.*
docs
tests
db
```

### Task 2: Compose Runtime

**Files:**
- Create: `docker-compose.yml`

- [x] **Step 1: Add app and PostgreSQL services**

Create `docker-compose.yml` with two services:

```yaml
services:
  app:
    build:
      context: .
    environment:
      RIMAS_DB_HOST: db
      RIMAS_DB_PORT: "5432"
      RIMAS_DB_NAME: ${RIMAS_DB_NAME:-rimas}
      RIMAS_DB_USER: ${RIMAS_DB_USER:-rimas}
      RIMAS_DB_PASSWORD: ${RIMAS_DB_PASSWORD:-rimas_password}
    ports:
      - "${RIMAS_APP_PORT:-8501}:8501"
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${RIMAS_DB_NAME:-rimas}
      POSTGRES_USER: ${RIMAS_DB_USER:-rimas}
      POSTGRES_PASSWORD: ${RIMAS_DB_PASSWORD:-rimas_password}
    ports:
      - "${RIMAS_DB_HOST_PORT:-5432}:5432"
    volumes:
      - rimas_postgres_data:/var/lib/postgresql/data
      - ./db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
      - ./db/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  rimas_postgres_data:
```

### Task 3: Verification

**Files:**
- Read: `docker-compose.yml`
- Read: `Dockerfile`
- Read: `requirements.txt`

- [x] **Step 1: Validate compose syntax**

Run:

```powershell
docker compose config
```

Expected: exit code 0 and resolved `app`, `db`, and `rimas_postgres_data` entries.

- [x] **Step 2: Run existing Python tests**

Run:

```powershell
pytest
```

Expected: exit code 0.

- [x] **Step 3: Validate full Compose startup**

Run:

```powershell
$env:RIMAS_DB_HOST_PORT='15432'; docker compose up -d
docker compose ps
docker compose logs --tail 30 app
docker compose down
```

Expected: PostgreSQL reports `healthy`, Streamlit starts on port `8501`, and verification containers are stopped afterward.
