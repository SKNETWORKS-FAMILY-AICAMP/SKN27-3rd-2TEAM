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
