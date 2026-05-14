import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config.settings import create_database_connection

CATALOG_PATH = ROOT / "neo4j" / "data" / "music_catalog.csv"
SCENARIO_PATH = ROOT / "neo4j" / "data" / "music_catalog_scenarios.csv"
NEW_RELEASE_CUTOFF = "2024-01-01"
BATCH_SIZE = 1000
SCENARIO_MOOD_FIELDS = (
    "emotion",
    "emotion_situation",
    "time",
    "focus",
    "exercise",
    "home",
    "commute",
    "special",
    "weather",
    "season",
)

UPSERT_SQL = """
INSERT INTO music_catalog (
    content_id,
    track_id,
    title,
    artist,
    album,
    genres,
    moods,
    tempo,
    release_type,
    recommendation_category,
    evidence_summary,
    source_type,
    metadata_json
) VALUES %s
ON CONFLICT (content_id) DO UPDATE SET
    track_id = EXCLUDED.track_id,
    title = EXCLUDED.title,
    artist = EXCLUDED.artist,
    album = EXCLUDED.album,
    genres = EXCLUDED.genres,
    moods = EXCLUDED.moods,
    tempo = EXCLUDED.tempo,
    release_type = EXCLUDED.release_type,
    recommendation_category = EXCLUDED.recommendation_category,
    evidence_summary = EXCLUDED.evidence_summary,
    source_type = EXCLUDED.source_type,
    metadata_json = EXCLUDED.metadata_json,
    updated_at = NOW();
"""


def build_catalog_record(catalog_row: dict, scenario_row: dict | None = None) -> dict:
    scenario_row = scenario_row or {}
    track_id = _clean(catalog_row.get("track_id"))
    title = _bounded(catalog_row.get("track_name"), 255)
    artist = _bounded(catalog_row.get("track_artist"), 255)
    release_date = _clean(catalog_row.get("track_album_release_date"))
    genres = _unique(
        [
            _clean(catalog_row.get("playlist_genre")),
            _clean(catalog_row.get("playlist_subgenre")),
        ]
    )
    moods = _scenario_values(scenario_row)
    release_type = _release_type(release_date)
    recommendation_category = _recommendation_category(
        release_type=release_type,
        moods=moods,
        subgenre=_clean(catalog_row.get("playlist_subgenre")),
    )

    return {
        "content_id": track_id,
        "track_id": track_id,
        "title": title,
        "artist": artist,
        "album": _bounded(catalog_row.get("track_album_name"), 255),
        "genres": genres,
        "moods": moods,
        "tempo": _tempo_bucket(catalog_row.get("tempo")),
        "release_type": release_type,
        "recommendation_category": recommendation_category,
        "evidence_summary": _evidence_summary(title, artist, genres, moods),
        "source_type": "neo4j_music_catalog_csv",
        "metadata_json": {
            "track_popularity": _clean(catalog_row.get("track_popularity")),
            "track_album_release_date": release_date,
            "playlist_name": _clean(catalog_row.get("playlist_name")),
            "playlist_id": _clean(catalog_row.get("playlist_id")),
            "audio_features": {
                "danceability": _clean(catalog_row.get("danceability")),
                "energy": _clean(catalog_row.get("energy")),
                "acousticness": _clean(catalog_row.get("acousticness")),
                "instrumentalness": _clean(catalog_row.get("instrumentalness")),
                "liveness": _clean(catalog_row.get("liveness")),
                "valence": _clean(catalog_row.get("valence")),
                "tempo": _clean(catalog_row.get("tempo")),
                "duration_ms": _clean(catalog_row.get("duration_ms")),
            },
            "scenario_labels": moods,
        },
    }


def load_scenarios(path: Path) -> dict[str, dict]:
    scenarios = {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            track_id = _clean(row.get("track_id"))
            if track_id:
                scenarios[track_id] = row
    return scenarios


def iter_catalog_records(catalog_path: Path, scenario_path: Path):
    scenarios = load_scenarios(scenario_path)
    with catalog_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            track_id = _clean(row.get("track_id"))
            title = _clean(row.get("track_name"))
            artist = _clean(row.get("track_artist"))
            if not track_id or not title or not artist:
                continue
            yield build_catalog_record(row, scenarios.get(track_id))


def load_to_postgres(catalog_path: Path, scenario_path: Path, batch_size: int = BATCH_SIZE) -> int:
    from psycopg2.extras import Json, execute_values

    connection = create_database_connection()
    inserted = 0
    try:
        with connection.cursor() as cursor:
            batch = []
            for record in iter_catalog_records(catalog_path, scenario_path):
                batch.append(_to_db_values(record, Json))
                if len(batch) >= batch_size:
                    execute_values(cursor, UPSERT_SQL, batch, page_size=batch_size)
                    inserted += len(batch)
                    batch = []
            if batch:
                execute_values(cursor, UPSERT_SQL, batch, page_size=batch_size)
                inserted += len(batch)
        connection.commit()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _to_db_values(record: dict, json_adapter) -> tuple:
    return (
        record["content_id"],
        record["track_id"],
        record["title"],
        record["artist"],
        record["album"],
        record["genres"],
        record["moods"],
        record["tempo"],
        record["release_type"],
        record["recommendation_category"],
        record["evidence_summary"],
        record["source_type"],
        json_adapter(record["metadata_json"]),
    )


def _release_type(release_date: str) -> str:
    if release_date and release_date >= NEW_RELEASE_CUTOFF:
        return "new_release"
    return "existing_catalog"


def _recommendation_category(*, release_type: str, moods: list[str], subgenre: str) -> str:
    if release_type == "new_release":
        return "new_release"
    if moods or subgenre:
        return "discovery_candidate"
    return "personalized_match"


def _tempo_bucket(value) -> str:
    try:
        tempo = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if tempo < 90:
        return "slow"
    if tempo <= 140:
        return "medium"
    return "fast"


def _scenario_values(row: dict) -> list[str]:
    values = []
    for field in SCENARIO_MOOD_FIELDS:
        raw = _clean(row.get(field))
        if not raw:
            continue
        values.extend(part.strip() for part in raw.split(";") if part.strip())
    return _unique(values)


def _evidence_summary(title: str, artist: str, genres: list[str], moods: list[str]) -> str:
    genre_text = "/".join(genres) if genres else "catalog"
    mood_text = "/".join(moods[:3]) if moods else "general"
    return f"{artist}의 {title}는 {genre_text} 성향과 {mood_text} 맥락을 가진 카탈로그 후보입니다."


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _bounded(value, max_length: int) -> str:
    return _clean(value)[:max_length]


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Neo4j music catalog CSV into PostgreSQL music_catalog.")
    parser.add_argument("--catalog", default=str(CATALOG_PATH))
    parser.add_argument("--scenarios", default=str(SCENARIO_PATH))
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    total = load_to_postgres(
        catalog_path=Path(args.catalog),
        scenario_path=Path(args.scenarios),
        batch_size=max(1, args.batch_size),
    )
    print(json.dumps({"loaded": total}, ensure_ascii=False))


if __name__ == "__main__":
    main()
