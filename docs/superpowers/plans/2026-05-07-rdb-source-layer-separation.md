# RDB Source Layer Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spotify/KKBOX 원천 테이블을 Source Layer로 추가하되 기존 docs의 Runtime Contract, Service Flow, SQL 상수 규칙을 깨지 않는다.

**Architecture:** 문서 계약을 먼저 정렬한 뒤 스키마와 Repository를 구현한다. Source Layer 테이블은 원천 데이터와 provenance 보존을 담당하고, Service Layer는 기존 Runtime Repository만 의존한다. 모든 SQL 상수는 기존 문서 기준을 유지해 `app/repositories/query_constants.py`에 둔다.

**Tech Stack:** Python, pytest/unittest, PostgreSQL SQL, psycopg2-compatible DB-API repository pattern.

---

## File Structure

- Modify: `docs/DB Schema 상세 설계.md`
  - Source Layer와 Runtime Contract Layer의 경계를 먼저 문서화한다.
  - Source SQL도 기존 SQL 상수 문서 규칙에 맞춰 `query_constants.py`에 둔다고 명시한다.
- Modify: `README.md`
  - DB 기준에 Source Layer 설명을 추가한다.
  - Service Layer가 Source Layer를 직접 조회하지 않는다고 명시한다.
- Modify: `docs/Common Constants State.md`
  - SQL 상수 위치를 `app/repositories/query_constants.py` 단일 파일로 유지한다고 명시한다.
- Modify: `db/schema.sql`
  - Source Layer 테이블을 추가한다.
  - `users.source_user_id`, `users.source_type`을 추가한다.
  - `music_catalog.track_id`, `content_id VARCHAR(140)`을 추가하되 기존 Runtime 계약을 보수적으로 유지한다.
  - `music_catalog.artist`는 `NOT NULL`을 유지한다.
  - `music_catalog.source_type` 기본값은 기존 문서와 호환되도록 `mock_music_catalog`를 유지한다.
  - `ml_outputs` nullable 완화는 하지 않는다.
  - `interaction_logs.primary_goal`, `intent_type`, `target_page`, `primary_section`은 유지한다.
- Modify: `app/repositories/query_constants.py`
  - Runtime SQL과 Source SQL을 같은 Repository SQL 상수 파일에 둔다.
- Create: `app/repositories/spotify_track_repository.py`
- Create: `app/repositories/spotify_audio_feature_repository.py`
- Create: `app/repositories/spotify_lyrics_repository.py`
- Create: `app/repositories/spotify_emotion_repository.py`
- Create: `app/repositories/kkbox_user_feature_repository.py`
- Create: `app/repositories/user_music_profile_repository.py`
- Create: `tests/test_rdb_source_layer_schema.py`
- Create: `tests/test_source_repositories.py`
- Create: `tests/test_service_source_boundary.py`

---

### Task 1: Documentation Contract Alignment

**Files:**
- Modify: `docs/DB Schema 상세 설계.md`
- Modify: `README.md`
- Modify: `docs/Common Constants State.md`

- [ ] **Step 1: Update DB schema documentation first**

Append this section near the table overview in `docs/DB Schema 상세 설계.md`:

```markdown
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
```

- [ ] **Step 2: Update README DB section**

Append this paragraph under the README DB section:

```markdown
Source Layer는 Spotify/KKBOX 원천 데이터와 전처리 산출물을 보존하는 계층입니다. Runtime Service Flow는 Source Layer 테이블을 직접 조회하지 않고, `music_catalog`, `ml_outputs`, `interaction_logs` 같은 Runtime Contract 테이블을 Repository Layer를 통해 사용합니다. SQL 상수는 기존 규칙대로 `app/repositories/query_constants.py`에서 관리합니다.
```

- [ ] **Step 3: Update common constants note**

Append this bullet under the SQL constants note in `docs/Common Constants State.md`:

```markdown
- Source Layer Repository SQL도 같은 Repository Layer 책임이므로 별도 SQL 상수 파일을 만들지 않고 `app/repositories/query_constants.py`에 둔다.
```

- [ ] **Step 4: Verify documentation mentions the approved boundary**

Run:

```powershell
rg -n "Source Layer|Runtime Contract|spotify_tracks|query_constants.py" docs README.md
```

Expected:

```text
docs/DB Schema 상세 설계.md
docs/Common Constants State.md
docs/superpowers/specs/2026-05-07-rdb-source-layer-design.md
README.md
```

- [ ] **Step 5: Commit documentation alignment**

```powershell
git add "docs/DB Schema 상세 설계.md" "docs/Common Constants State.md" README.md
git commit -m "docs: align source layer contract"
```

---

### Task 2: Schema Boundary Tests

**Files:**
- Create: `tests/test_rdb_source_layer_schema.py`

- [ ] **Step 1: Write failing schema boundary tests**

Create `tests/test_rdb_source_layer_schema.py`:

```python
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
    assert "track_id VARCHAR(128) REFERENCES spotify_tracks(track_id) ON DELETE SET NULL" in SCHEMA_SQL
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_rdb_source_layer_schema.py -v
```

Expected:

```text
FAILED tests/test_rdb_source_layer_schema.py::test_source_layer_tables_are_declared
FAILED tests/test_rdb_source_layer_schema.py::test_users_keep_runtime_identity_and_add_source_identity
FAILED tests/test_rdb_source_layer_schema.py::test_music_catalog_links_to_spotify_source_without_relaxing_runtime_contract
```

- [ ] **Step 3: Commit failing schema tests**

```powershell
git add tests/test_rdb_source_layer_schema.py
git commit -m "test: define source layer schema contract"
```

---

### Task 3: PostgreSQL Schema Update

**Files:**
- Modify: `db/schema.sql`

- [ ] **Step 1: Update `users` table**

Replace the existing `users` table block with:

```sql
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(100),
    source_user_id VARCHAR(128),
    source_type VARCHAR(50) NOT NULL DEFAULT 'internal',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_users_source_type
        CHECK (source_type IN ('internal', 'kkbox', 'spotify', 'guest', 'mock'))
);
```

- [ ] **Step 2: Insert Source Layer tables after `users`**

Insert this block immediately after the `users` table:

```sql
CREATE TABLE IF NOT EXISTS spotify_tracks (
    track_id VARCHAR(128) PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT,
    album TEXT,
    genres TEXT[] DEFAULT ARRAY[]::TEXT[],
    release_date DATE,
    popularity INTEGER,
    source_dataset VARCHAR(100) NOT NULL DEFAULT 'spotify_900k',
    raw_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS spotify_audio_features (
    track_id VARCHAR(128) PRIMARY KEY REFERENCES spotify_tracks(track_id) ON DELETE CASCADE,
    danceability NUMERIC(6,5),
    energy NUMERIC(6,5),
    valence NUMERIC(6,5),
    tempo_bpm NUMERIC(8,3),
    acousticness NUMERIC(6,5),
    instrumentalness NUMERIC(6,5),
    liveness NUMERIC(6,5),
    speechiness NUMERIC(6,5),
    loudness NUMERIC(8,3),
    duration_ms INTEGER,
    raw_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_spotify_audio_danceability
        CHECK (danceability IS NULL OR danceability BETWEEN 0 AND 1),
    CONSTRAINT chk_spotify_audio_energy
        CHECK (energy IS NULL OR energy BETWEEN 0 AND 1),
    CONSTRAINT chk_spotify_audio_valence
        CHECK (valence IS NULL OR valence BETWEEN 0 AND 1),
    CONSTRAINT chk_spotify_audio_acousticness
        CHECK (acousticness IS NULL OR acousticness BETWEEN 0 AND 1),
    CONSTRAINT chk_spotify_audio_instrumentalness
        CHECK (instrumentalness IS NULL OR instrumentalness BETWEEN 0 AND 1),
    CONSTRAINT chk_spotify_audio_liveness
        CHECK (liveness IS NULL OR liveness BETWEEN 0 AND 1),
    CONSTRAINT chk_spotify_audio_speechiness
        CHECK (speechiness IS NULL OR speechiness BETWEEN 0 AND 1),
    CONSTRAINT chk_spotify_audio_tempo
        CHECK (tempo_bpm IS NULL OR tempo_bpm >= 0),
    CONSTRAINT chk_spotify_audio_duration
        CHECK (duration_ms IS NULL OR duration_ms >= 0)
);

CREATE TABLE IF NOT EXISTS spotify_lyrics (
    track_id VARCHAR(128) PRIMARY KEY REFERENCES spotify_tracks(track_id) ON DELETE CASCADE,
    lyrics TEXT,
    language VARCHAR(32),
    lyrics_available BOOLEAN NOT NULL DEFAULT FALSE,
    source_type VARCHAR(100) NOT NULL DEFAULT 'existing_lyrics_dataset',
    raw_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_spotify_lyrics_source_type
        CHECK (source_type IN ('existing_lyrics_dataset', 'spotify_api', 'manual', 'unknown'))
);

CREATE TABLE IF NOT EXISTS spotify_emotions (
    track_id VARCHAR(128) PRIMARY KEY REFERENCES spotify_tracks(track_id) ON DELETE CASCADE,
    primary_emotion VARCHAR(64),
    secondary_emotions TEXT[] DEFAULT ARRAY[]::TEXT[],
    emotion_score_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    source_type VARCHAR(100) NOT NULL DEFAULT 'existing_emotion_dataset',
    raw_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_spotify_emotions_source_type
        CHECK (source_type IN ('existing_emotion_dataset', 'ml_generated', 'manual', 'unknown'))
);

CREATE TABLE IF NOT EXISTS kkbox_user_features (
    feature_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    source_user_id VARCHAR(128),
    total_interactions INTEGER,
    unique_song_count INTEGER,
    repeat_listening_ratio NUMERIC(5,4),
    recent_listening_level VARCHAR(32),
    recent_discovery_level VARCHAR(32),
    new_artist_acceptance NUMERIC(5,4),
    churn_label INTEGER,
    feature_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    source_dataset VARCHAR(100) NOT NULL DEFAULT 'kkbox',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_kkbox_total_interactions
        CHECK (total_interactions IS NULL OR total_interactions >= 0),
    CONSTRAINT chk_kkbox_unique_song_count
        CHECK (unique_song_count IS NULL OR unique_song_count >= 0),
    CONSTRAINT chk_kkbox_repeat_listening_ratio
        CHECK (repeat_listening_ratio IS NULL OR repeat_listening_ratio BETWEEN 0 AND 1),
    CONSTRAINT chk_kkbox_new_artist_acceptance
        CHECK (new_artist_acceptance IS NULL OR new_artist_acceptance BETWEEN 0 AND 1),
    CONSTRAINT chk_kkbox_churn_label
        CHECK (churn_label IS NULL OR churn_label IN (0, 1)),
    CONSTRAINT chk_kkbox_recent_listening_level
        CHECK (recent_listening_level IS NULL OR recent_listening_level IN ('low', 'medium', 'high')),
    CONSTRAINT chk_kkbox_recent_discovery_level
        CHECK (recent_discovery_level IS NULL OR recent_discovery_level IN ('low', 'medium', 'high'))
);

CREATE TABLE IF NOT EXISTS user_music_profiles (
    profile_id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    preferred_genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    preferred_artists TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    preferred_moods TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    preferred_tempo VARCHAR(32) DEFAULT 'unknown',
    personalization_strength VARCHAR(32),
    discovery_readiness VARCHAR(32),
    new_release_affinity VARCHAR(32),
    source_type VARCHAR(64) NOT NULL DEFAULT 'kkbox_profile',
    profile_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_user_music_profiles_tempo
        CHECK (preferred_tempo IN ('slow', 'medium', 'fast', 'unknown')),
    CONSTRAINT chk_user_music_profiles_personalization
        CHECK (personalization_strength IS NULL OR personalization_strength IN ('low', 'medium', 'high')),
    CONSTRAINT chk_user_music_profiles_discovery
        CHECK (discovery_readiness IS NULL OR discovery_readiness IN ('low', 'medium', 'high')),
    CONSTRAINT chk_user_music_profiles_new_release
        CHECK (new_release_affinity IS NULL OR new_release_affinity IN ('low', 'medium', 'high'))
);
```

- [ ] **Step 3: Update `music_catalog` without relaxing existing runtime fields**

Replace the existing `music_catalog` table block with:

```sql
CREATE TABLE IF NOT EXISTS music_catalog (
    content_id VARCHAR(140) PRIMARY KEY,
    track_id VARCHAR(128) REFERENCES spotify_tracks(track_id) ON DELETE SET NULL,
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
```

- [ ] **Step 4: Add Source Layer indexes**

Insert these indexes before the existing `idx_ml_outputs_user_id` index:

```sql
CREATE INDEX IF NOT EXISTS idx_users_source_user_id
ON users(source_user_id);

CREATE INDEX IF NOT EXISTS idx_spotify_tracks_artist
ON spotify_tracks(artist);

CREATE INDEX IF NOT EXISTS idx_spotify_tracks_genres_gin
ON spotify_tracks USING GIN (genres);

CREATE INDEX IF NOT EXISTS idx_spotify_tracks_raw_json_gin
ON spotify_tracks USING GIN (raw_json);

CREATE INDEX IF NOT EXISTS idx_spotify_audio_tempo
ON spotify_audio_features(tempo_bpm);

CREATE INDEX IF NOT EXISTS idx_spotify_audio_energy
ON spotify_audio_features(energy);

CREATE INDEX IF NOT EXISTS idx_spotify_audio_valence
ON spotify_audio_features(valence);

CREATE INDEX IF NOT EXISTS idx_kkbox_user_features_user_id
ON kkbox_user_features(user_id);

CREATE INDEX IF NOT EXISTS idx_kkbox_user_features_source_user_id
ON kkbox_user_features(source_user_id);

CREATE INDEX IF NOT EXISTS idx_kkbox_user_features_json_gin
ON kkbox_user_features USING GIN (feature_json);

CREATE INDEX IF NOT EXISTS idx_user_music_profiles_user_id
ON user_music_profiles(user_id);

CREATE INDEX IF NOT EXISTS idx_user_music_profiles_genres_gin
ON user_music_profiles USING GIN (preferred_genres);

CREATE INDEX IF NOT EXISTS idx_user_music_profiles_moods_gin
ON user_music_profiles USING GIN (preferred_moods);

CREATE INDEX IF NOT EXISTS idx_user_music_profiles_artists_gin
ON user_music_profiles USING GIN (preferred_artists);

CREATE INDEX IF NOT EXISTS idx_user_music_profiles_json_gin
ON user_music_profiles USING GIN (profile_json);
```

- [ ] **Step 5: Add `music_catalog.track_id` index**

```sql
CREATE INDEX IF NOT EXISTS idx_music_catalog_track_id
ON music_catalog(track_id);
```

- [ ] **Step 6: Run schema and repository tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_rdb_source_layer_schema.py tests/test_rdb_repositories.py -v
```

Expected:

```text
9 passed
```

- [ ] **Step 7: Commit schema update**

```powershell
git add db/schema.sql tests/test_rdb_source_layer_schema.py
git commit -m "feat: add rdb source layer schema"
```

---

### Task 4: Source Repository Query Constants

**Files:**
- Modify: `app/repositories/query_constants.py`
- Create: `tests/test_source_repositories.py`

- [ ] **Step 1: Write failing tests for Source Repository query usage**

Create `tests/test_source_repositories.py`:

```python
import unittest

from app.repositories import query_constants
from app.repositories.kkbox_user_feature_repository import KkboxUserFeatureRepository
from app.repositories.spotify_audio_feature_repository import SpotifyAudioFeatureRepository
from app.repositories.spotify_emotion_repository import SpotifyEmotionRepository
from app.repositories.spotify_lyrics_repository import SpotifyLyricsRepository
from app.repositories.spotify_track_repository import SpotifyTrackRepository
from app.repositories.user_music_profile_repository import UserMusicProfileRepository


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


class FakeConnection:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.cursor_instance = FakeCursor(fetchone_result, fetchall_result)

    def cursor(self, *args, **kwargs):
        return self.cursor_instance


class SourceRepositoryTest(unittest.TestCase):
    def test_spotify_track_repository_finds_by_track_id(self):
        expected = {"track_id": "spotify_track_001"}
        connection = FakeConnection(fetchone_result=expected)
        repository = SpotifyTrackRepository(connection)

        result = repository.find_by_track_id("spotify_track_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_SPOTIFY_TRACK_BY_TRACK_ID,
                    {"track_id": "spotify_track_001"},
                )
            ],
        )

    def test_spotify_audio_feature_repository_finds_by_track_id(self):
        expected = {"track_id": "spotify_track_001", "energy": 0.8}
        connection = FakeConnection(fetchone_result=expected)
        repository = SpotifyAudioFeatureRepository(connection)

        result = repository.find_by_track_id("spotify_track_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_SPOTIFY_AUDIO_FEATURE_BY_TRACK_ID,
                    {"track_id": "spotify_track_001"},
                )
            ],
        )

    def test_spotify_lyrics_repository_finds_by_track_id(self):
        expected = {"track_id": "spotify_track_001", "lyrics_available": True}
        connection = FakeConnection(fetchone_result=expected)
        repository = SpotifyLyricsRepository(connection)

        result = repository.find_by_track_id("spotify_track_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_SPOTIFY_LYRICS_BY_TRACK_ID,
                    {"track_id": "spotify_track_001"},
                )
            ],
        )

    def test_spotify_emotion_repository_finds_by_track_id(self):
        expected = {"track_id": "spotify_track_001", "primary_emotion": "joy"}
        connection = FakeConnection(fetchone_result=expected)
        repository = SpotifyEmotionRepository(connection)

        result = repository.find_by_track_id("spotify_track_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_SPOTIFY_EMOTION_BY_TRACK_ID,
                    {"track_id": "spotify_track_001"},
                )
            ],
        )

    def test_kkbox_user_feature_repository_finds_by_user_id(self):
        expected = [{"user_id": "user_001"}]
        connection = FakeConnection(fetchall_result=expected)
        repository = KkboxUserFeatureRepository(connection)

        result = repository.find_by_user_id("user_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_KKBOX_USER_FEATURES_BY_USER_ID,
                    {"user_id": "user_001"},
                )
            ],
        )

    def test_user_music_profile_repository_finds_latest_by_user_id(self):
        expected = {"user_id": "user_001", "preferred_tempo": "medium"}
        connection = FakeConnection(fetchone_result=expected)
        repository = UserMusicProfileRepository(connection)

        result = repository.get_latest_by_user_id("user_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_LATEST_USER_MUSIC_PROFILE_BY_USER_ID,
                    {"user_id": "user_001"},
                )
            ],
        )

    def test_source_repositories_validate_required_ids(self):
        repositories = (
            SpotifyTrackRepository(FakeConnection()),
            SpotifyAudioFeatureRepository(FakeConnection()),
            SpotifyLyricsRepository(FakeConnection()),
            SpotifyEmotionRepository(FakeConnection()),
        )

        for repository in repositories:
            with self.assertRaises(ValueError):
                repository.find_by_track_id("")

        with self.assertRaises(ValueError):
            KkboxUserFeatureRepository(FakeConnection()).find_by_user_id("")

        with self.assertRaises(ValueError):
            UserMusicProfileRepository(FakeConnection()).get_latest_by_user_id("")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_source_repositories.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'app.repositories.spotify_track_repository'
```

- [ ] **Step 3: Add Source query constants to existing `query_constants.py`**

Append this block to `app/repositories/query_constants.py`:

```python
SELECT_SPOTIFY_TRACK_BY_TRACK_ID = """
SELECT *
FROM spotify_tracks
WHERE track_id = %(track_id)s;
"""

SELECT_SPOTIFY_AUDIO_FEATURE_BY_TRACK_ID = """
SELECT *
FROM spotify_audio_features
WHERE track_id = %(track_id)s;
"""

SELECT_SPOTIFY_LYRICS_BY_TRACK_ID = """
SELECT *
FROM spotify_lyrics
WHERE track_id = %(track_id)s;
"""

SELECT_SPOTIFY_EMOTION_BY_TRACK_ID = """
SELECT *
FROM spotify_emotions
WHERE track_id = %(track_id)s;
"""

SELECT_KKBOX_USER_FEATURES_BY_USER_ID = """
SELECT *
FROM kkbox_user_features
WHERE user_id = %(user_id)s
ORDER BY created_at DESC;
"""

SELECT_LATEST_USER_MUSIC_PROFILE_BY_USER_ID = """
SELECT *
FROM user_music_profiles
WHERE user_id = %(user_id)s
ORDER BY created_at DESC
LIMIT 1;
"""
```

- [ ] **Step 4: Commit failing repository tests and query constants**

```powershell
git add app/repositories/query_constants.py tests/test_source_repositories.py
git commit -m "test: define source repository query contracts"
```

---

### Task 5: Source Repository Implementations

**Files:**
- Create: `app/repositories/spotify_track_repository.py`
- Create: `app/repositories/spotify_audio_feature_repository.py`
- Create: `app/repositories/spotify_lyrics_repository.py`
- Create: `app/repositories/spotify_emotion_repository.py`
- Create: `app/repositories/kkbox_user_feature_repository.py`
- Create: `app/repositories/user_music_profile_repository.py`

- [ ] **Step 1: Implement `SpotifyTrackRepository`**

Create `app/repositories/spotify_track_repository.py`:

```python
from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class SpotifyTrackRepository(BaseRepository):
    def find_by_track_id(self, track_id):
        if not track_id:
            raise ValueError("track_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_SPOTIFY_TRACK_BY_TRACK_ID,
                {"track_id": track_id},
            )
            return cursor.fetchone()
```

- [ ] **Step 2: Implement `SpotifyAudioFeatureRepository`**

Create `app/repositories/spotify_audio_feature_repository.py`:

```python
from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class SpotifyAudioFeatureRepository(BaseRepository):
    def find_by_track_id(self, track_id):
        if not track_id:
            raise ValueError("track_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_SPOTIFY_AUDIO_FEATURE_BY_TRACK_ID,
                {"track_id": track_id},
            )
            return cursor.fetchone()
```

- [ ] **Step 3: Implement `SpotifyLyricsRepository`**

Create `app/repositories/spotify_lyrics_repository.py`:

```python
from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class SpotifyLyricsRepository(BaseRepository):
    def find_by_track_id(self, track_id):
        if not track_id:
            raise ValueError("track_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_SPOTIFY_LYRICS_BY_TRACK_ID,
                {"track_id": track_id},
            )
            return cursor.fetchone()
```

- [ ] **Step 4: Implement `SpotifyEmotionRepository`**

Create `app/repositories/spotify_emotion_repository.py`:

```python
from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class SpotifyEmotionRepository(BaseRepository):
    def find_by_track_id(self, track_id):
        if not track_id:
            raise ValueError("track_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_SPOTIFY_EMOTION_BY_TRACK_ID,
                {"track_id": track_id},
            )
            return cursor.fetchone()
```

- [ ] **Step 5: Implement `KkboxUserFeatureRepository`**

Create `app/repositories/kkbox_user_feature_repository.py`:

```python
from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class KkboxUserFeatureRepository(BaseRepository):
    def find_by_user_id(self, user_id):
        if not user_id:
            raise ValueError("user_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_KKBOX_USER_FEATURES_BY_USER_ID,
                {"user_id": user_id},
            )
            return cursor.fetchall()
```

- [ ] **Step 6: Implement `UserMusicProfileRepository`**

Create `app/repositories/user_music_profile_repository.py`:

```python
from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class UserMusicProfileRepository(BaseRepository):
    def get_latest_by_user_id(self, user_id):
        if not user_id:
            raise ValueError("user_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_LATEST_USER_MUSIC_PROFILE_BY_USER_ID,
                {"user_id": user_id},
            )
            return cursor.fetchone()
```

- [ ] **Step 7: Run Source Repository tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_source_repositories.py -v
```

Expected:

```text
7 passed
```

- [ ] **Step 8: Commit Source Repository implementations**

```powershell
git add app/repositories/query_constants.py app/repositories/spotify_track_repository.py app/repositories/spotify_audio_feature_repository.py app/repositories/spotify_lyrics_repository.py app/repositories/spotify_emotion_repository.py app/repositories/kkbox_user_feature_repository.py app/repositories/user_music_profile_repository.py tests/test_source_repositories.py
git commit -m "feat: add source layer repositories"
```

---

### Task 6: Service Boundary Guard

**Files:**
- Create: `tests/test_service_source_boundary.py`

- [ ] **Step 1: Write boundary test**

Create `tests/test_service_source_boundary.py`:

```python
from pathlib import Path


SERVICE_DIR = Path("app/services")
SOURCE_REPOSITORY_MODULES = (
    "spotify_track_repository",
    "spotify_audio_feature_repository",
    "spotify_lyrics_repository",
    "spotify_emotion_repository",
    "kkbox_user_feature_repository",
    "user_music_profile_repository",
)


def test_service_layer_does_not_import_source_repositories_directly():
    service_files = sorted(SERVICE_DIR.glob("*.py"))
    assert service_files

    violations = []
    for service_file in service_files:
        source = service_file.read_text(encoding="utf-8")
        for module_name in SOURCE_REPOSITORY_MODULES:
            if module_name in source:
                violations.append(f"{service_file}:{module_name}")

    assert violations == []
```

- [ ] **Step 2: Run boundary test**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_service_source_boundary.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 3: Run all RDB-related tests**

Run:

```powershell
C:\Python314\python.exe -m pytest tests/test_rdb_source_layer_schema.py tests/test_source_repositories.py tests/test_service_source_boundary.py tests/test_rdb_repositories.py -v
```

Expected:

```text
17 passed
```

- [ ] **Step 4: Commit boundary guard**

```powershell
git add tests/test_service_source_boundary.py
git commit -m "test: guard service source layer boundary"
```

---

## Final Verification

- [ ] **Step 1: Run RDB test suite**

```powershell
C:\Python314\python.exe -m pytest tests/test_rdb_source_layer_schema.py tests/test_source_repositories.py tests/test_service_source_boundary.py tests/test_rdb_repositories.py -v
```

Expected:

```text
17 passed
```

- [ ] **Step 2: Run full test suite**

```powershell
C:\Python314\python.exe -m pytest -v
```

Expected:

```text
All collected tests pass
```

- [ ] **Step 3: Confirm clean git status**

```powershell
git status --short
```

Expected:

```text
no modified or untracked files
```

## Self-Review

- Spec coverage: Source Layer, Runtime Contract Layer, Repository boundary, transformation direction, schema compatibility, and service boundary are covered by tasks.
- Docs compliance: Documentation alignment is Task 1, before schema or code changes.
- SQL constant compliance: Source SQL constants are added to existing `app/repositories/query_constants.py`.
- Runtime contract compliance: `music_catalog.artist NOT NULL`, `music_catalog.source_type DEFAULT 'mock_music_catalog'`, `ml_outputs NOT NULL` fields, and existing `interaction_logs` service columns are preserved.
- Scope decision: This plan does not implement loader/transformer CSV generation. That remains a separate plan because it touches external dataset processing and file generation.
