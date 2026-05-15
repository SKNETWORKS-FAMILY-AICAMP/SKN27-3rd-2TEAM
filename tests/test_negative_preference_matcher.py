from app.services.negative_preference_matcher import NegativePreferenceMatcher


class StubMusicCatalogRepository:
    def __init__(self, rows):
        self.rows = rows
        self.received_text = None

    def find_identity_matches(self, text):
        self.received_text = text
        return self.rows


def test_negative_preference_matcher_prefers_artist_match_over_title_match():
    repository = StubMusicCatalogRepository([
        {"content_id": "track_001", "title": "Billie Eilish", "artist": "Another Artist"},
        {"content_id": "track_002", "title": "bad guy", "artist": "Billie Eilish"},
    ])

    result = NegativePreferenceMatcher(repository).resolve("Billie Eilish")

    assert repository.received_text == "Billie Eilish"
    assert result == {"disliked_artists": ["Billie Eilish"], "disliked_tracks": []}


def test_negative_preference_matcher_returns_all_track_ids_for_title_match():
    repository = StubMusicCatalogRepository([
        {"content_id": "track_a", "title": "Intro", "artist": "Artist A"},
        {"content_id": "track_b", "title": "Intro", "artist": "Artist B"},
    ])

    result = NegativePreferenceMatcher(repository).resolve("intro")

    assert result == {"disliked_artists": [], "disliked_tracks": ["track_a", "track_b"]}


def test_negative_preference_matcher_returns_empty_when_catalog_does_not_match():
    repository = StubMusicCatalogRepository([])

    result = NegativePreferenceMatcher(repository).resolve("그 노래")

    assert result == {"disliked_artists": [], "disliked_tracks": []}
