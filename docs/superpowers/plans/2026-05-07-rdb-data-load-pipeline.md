# RDB Data Load Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Source Layer 데이터를 수동 명령과 Docker 초기화 옵션으로 적재할 수 있는 안전한 파이프라인을 추가한다.

**Architecture:** 수동 적재를 기본 경로로 두고, Docker initdb 자동 적재는 새 PostgreSQL volume에서 CSV 파일이 있을 때만 실행되는 선택 옵션으로 둔다. 대용량 raw/load 파일은 git에 포함하지 않고, load SQL과 검증 SQL, init guard script만 버전 관리한다.

**Tech Stack:** PostgreSQL `psql`/`\copy`, Docker Compose, shell init script, Python pytest, Markdown docs.

---

## File Structure

- Modify: `docs/DB Schema 상세 설계.md`
  - Source Layer load SQL과 검증 SQL 위치를 문서화한다.
- Modify: `README.md`
  - 수동 적재 절차, 자동 적재 조건, volume 재초기화 주의사항을 추가한다.
- Modify: `.gitignore`
  - `data/load/*`, `seed/*` 생성물을 제외하고 `.gitkeep`만 유지한다.
- Modify: `docker-compose.yml`
  - `/workspace` bind mount를 추가한다.
  - optional init script를 `/docker-entrypoint-initdb.d/03-load-source-data.sh`로 마운트한다.
- Create: `db/load/load_kkbox_seed.sql`
  - `seed/users.csv`, `seed/kkbox_user_features.csv` 적재.
- Create: `db/load/load_spotify_catalog.sql`
  - `data/load/*_load.csv` 적재.
- Create: `db/load/verify_source_load.sql`
  - count/FK/중복/content_id 규칙 검증.
- Create: `db/init/03-load-source-data.sh`
  - Docker initdb에서 파일 존재 시에만 load SQL 실행.
- Create: `data/load/.gitkeep`
- Create: `seed/.gitkeep`
- Create: `tests/test_rdb_data_load_pipeline.py`
  - load SQL, verify SQL, init script, Compose mount, gitignore, README 계약 검증.

---

### Task 1: Documentation Contract Update

**Files:**
- Modify: `docs/DB Schema 상세 설계.md`
- Modify: `README.md`

- [ ] **Step 1: Update DB schema docs with load file locations**

Append this section after the existing Source Layer section in `docs/DB Schema 상세 설계.md`:

```markdown
## Source Layer 적재 파이프라인

Source Layer 데이터 적재는 수동 적재를 기본 경로로 사용한다. Docker 초기화 자동 적재는 새 PostgreSQL volume에서 load CSV가 존재할 때만 실행되는 선택 옵션이다.

적재 SQL 위치:

- `db/load/load_kkbox_seed.sql`
- `db/load/load_spotify_catalog.sql`
- `db/load/verify_source_load.sql`

Docker 초기화 보조 스크립트:

- `db/init/03-load-source-data.sh`

적재 CSV 위치:

- `seed/users.csv`
- `seed/kkbox_user_features.csv`
- `data/load/spotify_tracks_load.csv`
- `data/load/spotify_audio_features_load.csv`
- `data/load/spotify_lyrics_load.csv`
- `data/load/spotify_emotions_load.csv`
- `data/load/music_catalog_load.csv`

`user_music_profiles`는 현재 1차 적재 대상에서 제외한다. 테이블은 Source Layer 스키마로 유지하되, CSV 생성 규칙이 승인된 뒤 별도 적재 파이프라인으로 추가한다.
```

- [ ] **Step 2: Update README manual load section**

Append this section after the README DB section:

```markdown
## Source Layer 데이터 적재

기본 경로는 수동 적재입니다.

```powershell
docker compose up -d db
docker compose exec db psql -U rimas -d rimas -f /workspace/db/load/load_kkbox_seed.sql
docker compose exec db psql -U rimas -d rimas -f /workspace/db/load/load_spotify_catalog.sql
docker compose exec db psql -U rimas -d rimas -f /workspace/db/load/verify_source_load.sql
```

필수 CSV:

- `seed/users.csv`
- `seed/kkbox_user_features.csv`
- `data/load/spotify_tracks_load.csv`
- `data/load/spotify_audio_features_load.csv`
- `data/load/music_catalog_load.csv`

선택 CSV:

- `data/load/spotify_lyrics_load.csv`
- `data/load/spotify_emotions_load.csv`

Docker 초기화 자동 적재는 새 PostgreSQL volume에서만 실행됩니다. 기존 volume에는 `/docker-entrypoint-initdb.d` 스크립트가 다시 실행되지 않습니다. 처음부터 다시 적재해야 하면 데이터가 삭제된다는 점을 확인한 뒤 `docker compose down -v`를 사용합니다.

raw 데이터와 생성된 load CSV는 git에 포함하지 않습니다. `data/load/.gitkeep`, `seed/.gitkeep`만 저장소에 유지합니다.
```
```

- [ ] **Step 3: Run docs grep**

Run:

```powershell
rg -n "Source Layer 데이터 적재|load_kkbox_seed.sql|docker compose exec db|docker compose down -v" docs README.md
```

Expected:

```text
docs/DB Schema 상세 설계.md
README.md
```

- [ ] **Step 4: Commit documentation update**

```powershell
git add "docs/DB Schema 상세 설계.md" README.md
git commit -m "docs: document source data load pipeline"
```

---

### Task 2: Pipeline Contract Tests

**Files:**
- Create: `tests/test_rdb_data_load_pipeline.py`

- [ ] **Step 1: Write failing tests for load pipeline files**

Create `tests/test_rdb_data_load_pipeline.py`:

```python
from pathlib import Path


ROOT = Path(".")
LOAD_DIR = ROOT / "db" / "load"
INIT_SCRIPT = ROOT / "db" / "init" / "03-load-source-data.sh"
COMPOSE_FILE = ROOT / "docker-compose.yml"
GITIGNORE = ROOT / ".gitignore"
README = ROOT / "README.md"


def read(path):
    return path.read_text(encoding="utf-8")


def test_load_sql_files_exist():
    expected_files = (
        LOAD_DIR / "load_kkbox_seed.sql",
        LOAD_DIR / "load_spotify_catalog.sql",
        LOAD_DIR / "verify_source_load.sql",
    )

    for path in expected_files:
        assert path.exists(), f"missing {path}"


def test_kkbox_load_sql_uses_expected_copy_targets():
    sql = read(LOAD_DIR / "load_kkbox_seed.sql")

    assert "\\copy users(user_id, display_name, source_user_id, source_type)" in sql
    assert "/workspace/seed/users.csv" in sql
    assert "\\copy kkbox_user_features(" in sql
    assert "/workspace/seed/kkbox_user_features.csv" in sql
    assert "user_music_profiles" not in sql


def test_spotify_load_sql_uses_expected_copy_targets():
    sql = read(LOAD_DIR / "load_spotify_catalog.sql")

    expected_fragments = (
        "\\copy spotify_tracks(",
        "/workspace/data/load/spotify_tracks_load.csv",
        "\\copy spotify_audio_features(",
        "/workspace/data/load/spotify_audio_features_load.csv",
        "\\copy spotify_lyrics(",
        "/workspace/data/load/spotify_lyrics_load.csv",
        "\\copy spotify_emotions(",
        "/workspace/data/load/spotify_emotions_load.csv",
        "\\copy music_catalog(",
        "/workspace/data/load/music_catalog_load.csv",
    )

    for fragment in expected_fragments:
        assert fragment in sql


def test_verify_sql_contains_required_checks():
    sql = read(LOAD_DIR / "verify_source_load.sql")

    expected_fragments = (
        "table_name",
        "spotify_tracks",
        "spotify_audio_features",
        "spotify_lyrics",
        "spotify_emotions",
        "music_catalog",
        "kkbox_user_features",
        "missing_audio_feature_fk",
        "missing_lyrics_fk",
        "missing_emotions_fk",
        "duplicate_spotify_track_id",
        "invalid_music_catalog_content_id",
        "invalid_music_catalog_track_id",
        "invalid_music_catalog_content_id_rule",
    )

    for fragment in expected_fragments:
        assert fragment in sql


def test_docker_init_script_guards_missing_files():
    script = read(INIT_SCRIPT)

    expected_fragments = (
        "set -eu",
        "seed/users.csv",
        "seed/kkbox_user_features.csv",
        "data/load/spotify_tracks_load.csv",
        "data/load/spotify_audio_features_load.csv",
        "data/load/music_catalog_load.csv",
        "Skipping Source Layer data load",
        "load_kkbox_seed.sql",
        "load_spotify_catalog.sql",
        "verify_source_load.sql",
    )

    for fragment in expected_fragments:
        assert fragment in script


def test_compose_mounts_workspace_and_optional_init_script():
    compose = read(COMPOSE_FILE)

    assert "- .:/workspace:ro" in compose
    assert (
        "- ./db/init/03-load-source-data.sh:/docker-entrypoint-initdb.d/03-load-source-data.sh:ro"
        in compose
    )


def test_generated_data_files_are_gitignored_but_keep_directories():
    gitignore = read(GITIGNORE)

    expected_fragments = (
        "data/load/*",
        "!data/load/.gitkeep",
        "seed/*",
        "!seed/.gitkeep",
    )

    for fragment in expected_fragments:
        assert fragment in gitignore

    assert (ROOT / "data" / "load" / ".gitkeep").exists()
    assert (ROOT / "seed" / ".gitkeep").exists()


def test_readme_documents_manual_and_docker_init_load():
    readme = read(README)

    expected_fragments = (
        "Source Layer 데이터 적재",
        "docker compose exec db psql",
        "load_kkbox_seed.sql",
        "load_spotify_catalog.sql",
        "verify_source_load.sql",
        "docker compose down -v",
        "data/load/.gitkeep",
        "seed/.gitkeep",
    )

    for fragment in expected_fragments:
        assert fragment in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_rdb_data_load_pipeline.py -v
```

Expected:

```text
FAILED tests/test_rdb_data_load_pipeline.py::test_load_sql_files_exist
```

- [ ] **Step 3: Commit failing tests**

```powershell
git add tests/test_rdb_data_load_pipeline.py
git commit -m "test: define source data load pipeline contract"
```

---

### Task 3: Load SQL And Verify SQL

**Files:**
- Create: `db/load/load_kkbox_seed.sql`
- Create: `db/load/load_spotify_catalog.sql`
- Create: `db/load/verify_source_load.sql`

- [ ] **Step 1: Create KKBOX load SQL**

Create `db/load/load_kkbox_seed.sql`:

```sql
\copy users(user_id, display_name, source_user_id, source_type) FROM '/workspace/seed/users.csv' WITH (FORMAT csv, HEADER true);

\copy kkbox_user_features(user_id, source_user_id, total_interactions, unique_song_count, repeat_listening_ratio, recent_listening_level, recent_discovery_level, new_artist_acceptance, churn_label, feature_json, source_dataset) FROM '/workspace/seed/kkbox_user_features.csv' WITH (FORMAT csv, HEADER true);
```

- [ ] **Step 2: Create Spotify load SQL**

Create `db/load/load_spotify_catalog.sql`:

```sql
\copy spotify_tracks(track_id, title, artist, album, genres, release_date, popularity, source_dataset, raw_json) FROM '/workspace/data/load/spotify_tracks_load.csv' WITH (FORMAT csv, HEADER true);

\copy spotify_audio_features(track_id, danceability, energy, valence, tempo_bpm, acousticness, instrumentalness, liveness, speechiness, loudness, duration_ms, raw_json) FROM '/workspace/data/load/spotify_audio_features_load.csv' WITH (FORMAT csv, HEADER true);

\copy spotify_lyrics(track_id, lyrics, language, lyrics_available, source_type, raw_json) FROM '/workspace/data/load/spotify_lyrics_load.csv' WITH (FORMAT csv, HEADER true);

\copy spotify_emotions(track_id, primary_emotion, secondary_emotions, emotion_score_json, source_type, raw_json) FROM '/workspace/data/load/spotify_emotions_load.csv' WITH (FORMAT csv, HEADER true);

\copy music_catalog(content_id, track_id, title, artist, album, genres, moods, tempo, release_type, recommendation_category, evidence_summary, source_type, metadata_json) FROM '/workspace/data/load/music_catalog_load.csv' WITH (FORMAT csv, HEADER true);
```

- [ ] **Step 3: Create verification SQL**

Create `db/load/verify_source_load.sql`:

```sql
SELECT 'users' AS table_name, count(*) FROM users
UNION ALL SELECT 'kkbox_user_features', count(*) FROM kkbox_user_features
UNION ALL SELECT 'spotify_tracks', count(*) FROM spotify_tracks
UNION ALL SELECT 'spotify_audio_features', count(*) FROM spotify_audio_features
UNION ALL SELECT 'spotify_lyrics', count(*) FROM spotify_lyrics
UNION ALL SELECT 'spotify_emotions', count(*) FROM spotify_emotions
UNION ALL SELECT 'music_catalog', count(*) FROM music_catalog
ORDER BY table_name;

SELECT count(*) AS missing_audio_feature_fk
FROM spotify_audio_features f
LEFT JOIN spotify_tracks t ON t.track_id = f.track_id
WHERE t.track_id IS NULL;

SELECT count(*) AS missing_lyrics_fk
FROM spotify_lyrics l
LEFT JOIN spotify_tracks t ON t.track_id = l.track_id
WHERE t.track_id IS NULL;

SELECT count(*) AS missing_emotions_fk
FROM spotify_emotions e
LEFT JOIN spotify_tracks t ON t.track_id = e.track_id
WHERE t.track_id IS NULL;

SELECT track_id AS duplicate_spotify_track_id, count(*) AS duplicate_count
FROM spotify_tracks
GROUP BY track_id
HAVING count(*) > 1;

SELECT count(*) AS invalid_music_catalog_content_id
FROM music_catalog
WHERE content_id IS NULL OR content_id = '';

SELECT count(*) AS invalid_music_catalog_track_id
FROM music_catalog
WHERE track_id IS NULL OR track_id = '';

SELECT count(*) AS invalid_music_catalog_content_id_rule
FROM music_catalog
WHERE track_id IS NOT NULL
AND content_id <> ('mc_' || track_id);
```

- [ ] **Step 4: Run load SQL contract tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_rdb_data_load_pipeline.py::test_load_sql_files_exist tests/test_rdb_data_load_pipeline.py::test_kkbox_load_sql_uses_expected_copy_targets tests/test_rdb_data_load_pipeline.py::test_spotify_load_sql_uses_expected_copy_targets tests/test_rdb_data_load_pipeline.py::test_verify_sql_contains_required_checks -v
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Commit SQL files**

```powershell
git add db/load/load_kkbox_seed.sql db/load/load_spotify_catalog.sql db/load/verify_source_load.sql
git commit -m "feat: add source data load sql"
```

---

### Task 4: Docker Optional Init Script

**Files:**
- Create: `db/init/03-load-source-data.sh`

- [ ] **Step 1: Create guarded init script**

Create `db/init/03-load-source-data.sh`:

```sh
#!/bin/sh
set -eu

required_files="
/workspace/seed/users.csv
/workspace/seed/kkbox_user_features.csv
/workspace/data/load/spotify_tracks_load.csv
/workspace/data/load/spotify_audio_features_load.csv
/workspace/data/load/music_catalog_load.csv
"

for file_path in $required_files; do
  if [ ! -f "$file_path" ]; then
    echo "Skipping Source Layer data load: missing $file_path"
    exit 0
  fi
done

echo "Loading KKBOX Source Layer data"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/load_kkbox_seed.sql

echo "Loading Spotify Source Layer data"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/load_spotify_catalog.sql

echo "Verifying Source Layer data load"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/verify_source_load.sql
```

- [ ] **Step 2: Run init script contract test**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_rdb_data_load_pipeline.py::test_docker_init_script_guards_missing_files -v
```

Expected:

```text
1 passed
```

- [ ] **Step 3: Commit init script**

```powershell
git add db/init/03-load-source-data.sh
git commit -m "feat: add optional source data init script"
```

---

### Task 5: Compose Mounts And Data File Policy

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.gitignore`
- Create: `data/load/.gitkeep`
- Create: `seed/.gitkeep`

- [ ] **Step 1: Update Docker Compose db volumes**

Modify `docker-compose.yml` db volumes to include these entries:

```yaml
      - .:/workspace:ro
      - ./db/init/03-load-source-data.sh:/docker-entrypoint-initdb.d/03-load-source-data.sh:ro
```

The db volumes block must include:

```yaml
    volumes:
      - rimas_postgres_data:/var/lib/postgresql/data
      - .:/workspace:ro
      - ./db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
      - ./db/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql:ro
      - ./db/init/03-load-source-data.sh:/docker-entrypoint-initdb.d/03-load-source-data.sh:ro
```

- [ ] **Step 2: Update `.gitignore`**

Append:

```gitignore
# Generated source data load files
data/load/*
!data/load/.gitkeep
seed/*
!seed/.gitkeep
```

- [ ] **Step 3: Add `.gitkeep` files**

Create empty files:

```text
data/load/.gitkeep
seed/.gitkeep
```

- [ ] **Step 4: Run compose and file policy tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_rdb_data_load_pipeline.py::test_compose_mounts_workspace_and_optional_init_script tests/test_rdb_data_load_pipeline.py::test_generated_data_files_are_gitignored_but_keep_directories -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit compose and file policy**

```powershell
git add docker-compose.yml .gitignore data/load/.gitkeep seed/.gitkeep
git commit -m "feat: wire optional source data docker init"
```

---

### Task 6: README Verification And Full Test

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Ensure README contains load instructions**

If Task 1 did not already add the exact required README fragments, update `README.md` so it includes:

```markdown
Source Layer 데이터 적재
docker compose exec db psql
load_kkbox_seed.sql
load_spotify_catalog.sql
verify_source_load.sql
docker compose down -v
data/load/.gitkeep
seed/.gitkeep
```

- [ ] **Step 2: Run README contract test**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_rdb_data_load_pipeline.py::test_readme_documents_manual_and_docker_init_load -v
```

Expected:

```text
1 passed
```

- [ ] **Step 3: Run all pipeline tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_rdb_data_load_pipeline.py -v
```

Expected:

```text
8 passed
```

- [ ] **Step 4: Commit README/test completion**

```powershell
git add README.md tests/test_rdb_data_load_pipeline.py
git commit -m "docs: document source data load commands"
```

---

## Final Verification

- [ ] **Step 1: Run RDB and pipeline tests**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_rdb_source_layer_schema.py tests/test_source_repositories.py tests/test_service_source_boundary.py tests/test_rdb_repositories.py tests/test_rdb_data_load_pipeline.py -v
```

Expected:

```text
25 passed
```

- [ ] **Step 2: Run full test suite**

```powershell
.venv\Scripts\python.exe -m pytest -v
```

Expected:

```text
All collected tests pass
```

- [ ] **Step 3: Confirm docker compose config is valid**

Run:

```powershell
docker compose config
```

Expected:

```text
Exit code 0 and db volumes include /workspace and 03-load-source-data.sh.
```

- [ ] **Step 4: Confirm clean git status**

```powershell
git status --short
```

Expected:

```text
no modified or untracked files
```

## Self-Review

- Spec coverage: Manual load, optional Docker init load, file policy, load SQL, verify SQL, docs, and tests are covered.
- Scope control: Loader/transformer CSV generation is not implemented here; this plan consumes generated CSV files only.
- Source boundary: No Service Layer dependency on Source tables is introduced.
- Data safety: Generated CSV files are ignored by git and Docker auto load skips when required files are missing.
