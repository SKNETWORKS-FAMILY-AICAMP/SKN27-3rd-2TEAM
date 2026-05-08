import unittest

from app.repositories import query_constants
from app.repositories.kkbox_user_feature_repository import KkboxUserFeatureRepository
from app.repositories.spotify_audio_feature_repository import (
    SpotifyAudioFeatureRepository,
)
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
