from scripts.load_postgres_music_catalog import build_catalog_record


def test_build_catalog_record_classifies_recent_release_as_new_release():
    catalog_row = {
        "track_id": "track_new",
        "track_name": "Fresh Track",
        "track_artist": "Fresh Artist",
        "track_album_name": "Fresh Album",
        "track_album_release_date": "2024-08-16",
        "playlist_genre": "pop",
        "playlist_subgenre": "dance pop",
        "track_popularity": "70",
        "tempo": "158.6",
    }
    scenario_row = {"emotion": "joy", "exercise": "running", "weather": "sunny"}

    record = build_catalog_record(catalog_row, scenario_row)

    assert record["content_id"] == "track_new"
    assert record["release_type"] == "new_release"
    assert record["recommendation_category"] == "new_release"
    assert record["tempo"] == "fast"
    assert record["genres"] == ["pop", "dance pop"]
    assert record["moods"] == ["joy", "running", "sunny"]


def test_build_catalog_record_classifies_existing_scenario_track_as_discovery():
    catalog_row = {
        "track_id": "track_discovery",
        "track_name": "Deep Cut",
        "track_artist": "Hidden Artist",
        "track_album_name": "Hidden Album",
        "track_album_release_date": "2020-01-01",
        "playlist_genre": "rock",
        "playlist_subgenre": "",
        "track_popularity": "15",
        "tempo": "88",
    }
    scenario_row = {"emotion_situation": "focus", "home": "chores;shower"}

    record = build_catalog_record(catalog_row, scenario_row)

    assert record["release_type"] == "existing_catalog"
    assert record["recommendation_category"] == "discovery_candidate"
    assert record["tempo"] == "slow"
    assert record["genres"] == ["rock"]
    assert record["moods"] == ["focus", "chores", "shower"]


def test_build_catalog_record_uses_personalized_match_when_no_discovery_signal():
    catalog_row = {
        "track_id": "track_personal",
        "track_name": "Steady Track",
        "track_artist": "Known Artist",
        "track_album_name": "Known Album",
        "track_album_release_date": "2019-01-01",
        "playlist_genre": "rnb",
        "playlist_subgenre": "",
        "track_popularity": "55",
        "tempo": "110",
    }

    record = build_catalog_record(catalog_row, {})

    assert record["release_type"] == "existing_catalog"
    assert record["recommendation_category"] == "personalized_match"
    assert record["tempo"] == "medium"
    assert record["moods"] == []


def test_build_catalog_record_truncates_database_bounded_text_fields():
    catalog_row = {
        "track_id": "track_long",
        "track_name": "T" * 300,
        "track_artist": "A" * 300,
        "track_album_name": "B" * 300,
        "track_album_release_date": "2019-01-01",
        "playlist_genre": "pop",
        "playlist_subgenre": "",
        "track_popularity": "55",
        "tempo": "110",
    }

    record = build_catalog_record(catalog_row, {})

    assert len(record["title"]) == 255
    assert len(record["artist"]) == 255
    assert len(record["album"]) == 255
