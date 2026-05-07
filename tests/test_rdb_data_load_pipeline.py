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
        LOAD_DIR / "load_spotify_lyrics.sql",
        LOAD_DIR / "load_spotify_emotions.sql",
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
        "\\copy music_catalog(",
        "/workspace/data/load/music_catalog_load.csv",
    )

    for fragment in expected_fragments:
        assert fragment in sql

    assert "spotify_lyrics_load.csv" not in sql
    assert "spotify_emotions_load.csv" not in sql


def test_optional_spotify_load_sql_uses_expected_copy_targets():
    lyrics_sql = read(LOAD_DIR / "load_spotify_lyrics.sql")
    emotions_sql = read(LOAD_DIR / "load_spotify_emotions.sql")

    assert "\\copy spotify_lyrics(" in lyrics_sql
    assert "/workspace/data/load/spotify_lyrics_load.csv" in lyrics_sql
    assert "\\copy spotify_emotions(" in emotions_sql
    assert "/workspace/data/load/spotify_emotions_load.csv" in emotions_sql


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
        "spotify_lyrics_load.csv",
        "load_spotify_lyrics.sql",
        "spotify_emotions_load.csv",
        "load_spotify_emotions.sql",
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
        "load_spotify_lyrics.sql",
        "load_spotify_emotions.sql",
        "verify_source_load.sql",
        "docker compose down -v",
        "data/load/.gitkeep",
        "seed/.gitkeep",
    )

    for fragment in expected_fragments:
        assert fragment in readme
