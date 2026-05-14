import json

from scripts.verify_es_neo4j_id_alignment import (
    build_alignment_report,
    build_aligned_es_documents,
    load_es_documents,
    normalize_track_key,
)


def test_normalize_track_key_uses_song_artist_album_and_length():
    key = normalize_track_key(
        title="  The Scientist ",
        artist="Corinne Bailey Rae",
        album="Fifty Shades Darker (Original Motion Picture Soundtrack)",
        duration_ms="196000",
    )

    assert key == (
        "the scientist",
        "corinne bailey rae",
        "fifty shades darker (original motion picture soundtrack)",
        196000,
    )


def test_load_es_documents_accepts_ndjson_and_json_array(tmp_path):
    ndjson_path = tmp_path / "part0.json"
    ndjson_path.write_text(
        "\n".join(
            [
                json.dumps({"content_id": "lyrics_001", "song": "Song A", "artist": "Artist A"}),
                json.dumps({"doc_id": "lyrics_002", "song": "Song B", "artist": "Artist B"}),
            ]
        ),
        encoding="utf-8",
    )
    array_path = tmp_path / "part1.json"
    array_path.write_text(
        json.dumps([{"content_id": "lyrics_003", "song": "Song C", "artist": "Artist C"}]),
        encoding="utf-8",
    )

    docs = load_es_documents([ndjson_path, array_path])

    assert [doc["content_id"] for doc in docs] == ["lyrics_001", "lyrics_002", "lyrics_003"]


def test_load_es_documents_accepts_multiline_json_object(tmp_path):
    object_path = tmp_path / "single.json"
    object_path.write_text(
        json.dumps(
            {
                "doc_id": "lyrics_004",
                "song": "Song D",
                "artist": "Artist D",
                "content": "line 1\nline 2",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    docs = load_es_documents([object_path])

    assert docs[0]["content_id"] == "lyrics_004"
    assert docs[0]["content"] == "line 1\nline 2"


def test_load_es_documents_skips_malformed_ndjson_lines(tmp_path):
    ndjson_path = tmp_path / "broken.json"
    ndjson_path.write_text(
        "\n".join(
            [
                json.dumps({"content_id": "lyrics_005", "song": "Song E", "artist": "Artist E"}),
                '{"doc_id": "broken", "content": "unterminated',
                json.dumps({"content_id": "lyrics_006", "song": "Song F", "artist": "Artist F"}),
            ]
        ),
        encoding="utf-8",
    )

    docs = load_es_documents([ndjson_path])

    assert [doc["content_id"] for doc in docs] == ["lyrics_005", "lyrics_006"]


def test_build_alignment_report_classifies_exact_duplicate_and_missing_matches():
    neo4j_rows = [
        {
            "track_id": "nl_001",
            "track_name": "Song A",
            "track_artist": "Artist A",
            "track_album_name": "Album A",
            "duration_ms": "180000",
        },
        {
            "track_id": "nl_002",
            "track_name": "Song B",
            "track_artist": "Artist B",
            "track_album_name": "Album B",
            "duration_ms": "181000",
        },
        {
            "track_id": "nl_003",
            "track_name": "Song C",
            "track_artist": "Artist C",
            "track_album_name": "Album C",
            "duration_ms": "182000",
        },
    ]
    es_docs = [
        {
            "content_id": "lyrics_001",
            "song": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "length": "03:00",
        },
        {
            "content_id": "lyrics_002_a",
            "song": "Song B",
            "artist": "Artist B",
            "album": "Album B",
            "length": "03:01",
        },
        {
            "content_id": "lyrics_002_b",
            "song": "Song B",
            "artist": "Artist B",
            "album": "Album B",
            "length": "03:01",
        },
    ]

    report = build_alignment_report(neo4j_rows, es_docs)

    assert report["summary"] == {
        "neo4j_rows": 3,
        "es_documents": 3,
        "exact_matches": 1,
        "duplicate_matches": 1,
        "unmatched_neo4j": 1,
    }
    assert report["exact_matches"][0]["neo4j_track_id"] == "nl_001"
    assert report["duplicate_matches"][0]["neo4j_track_id"] == "nl_002"
    assert report["unmatched_neo4j"][0]["neo4j_track_id"] == "nl_003"


def test_build_aligned_es_documents_rewrites_only_exact_matches_to_neo4j_track_id():
    neo4j_rows = [
        {
            "track_id": "nl_001",
            "track_name": "Song A",
            "track_artist": "Artist A",
            "track_album_name": "Album A",
            "duration_ms": "180000",
        },
        {
            "track_id": "nl_002",
            "track_name": "Song B",
            "track_artist": "Artist B",
            "track_album_name": "Album B",
            "duration_ms": "181000",
        },
    ]
    es_docs = [
        {
            "content_id": "lyrics_001",
            "doc_id": "lyrics_001",
            "song": "Song A",
            "artist": "Artist A",
            "album": "Album A",
            "length": "03:00",
            "metadata": {"track_id": "lyrics_001"},
        },
        {
            "content_id": "lyrics_002_a",
            "song": "Song B",
            "artist": "Artist B",
            "album": "Album B",
            "length": "03:01",
        },
        {
            "content_id": "lyrics_002_b",
            "song": "Song B",
            "artist": "Artist B",
            "album": "Album B",
            "length": "03:01",
        },
    ]

    aligned_docs = build_aligned_es_documents(neo4j_rows, es_docs)

    assert len(aligned_docs) == 1
    assert aligned_docs[0]["content_id"] == "nl_001"
    assert aligned_docs[0]["metadata"]["track_id"] == "nl_001"
    assert aligned_docs[0]["metadata"]["legacy_content_id"] == "lyrics_001"
