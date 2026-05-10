# 로그
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 패키지
import pandas as pd


def _split_multi(value) -> list[str]:
    """CSV 쉼표 구분 필드를 리스트로 정규화. 비어 있으면 빈 리스트."""
    if value is None or pd.isna(value):
        return []
    s = str(value).strip()
    if not s:
        return []
    return [p.strip() for p in s.split(",") if p.strip()]


def _scalar_or_none(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


####################################################################
# 실행할 쿼리 목록 정의
####################################################################
class Query:
    """CSV 한 행(pandas Series)마다 노드 적재용 query와 파라미터를 반환한다.
    import_data(..., row_query=Query.<메서드>)처럼 콜러블을 넘긴다.

    참고: @property는 row 인자를 받을 수 없어 @staticmethod로 둔다.
    """

    @staticmethod
    def users(row: pd.Series):
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.display_name = $display_name
        """
        parameters = {
            "user_id": str(row["user_id"]),
            "display_name": row["display_name"],
        }
        return query, parameters

    @staticmethod
    def genres(row: pd.Series):
        query = """
        MERGE (g:Genre {genre: $genre})
        """
        parameters = {"genre": row["genre"]}
        return query, parameters

    @staticmethod
    def artists(row: pd.Series):
        query = """
        MERGE (a:Artist {artist: $artist})
        """
        parameters = {"artist": row["artist"]}
        return query, parameters

    @staticmethod
    def moods(row: pd.Series):
        query = """
        MERGE (m:Mood {mood: $mood})
        """
        parameters = {"mood": row["mood"]}
        return query, parameters


    @staticmethod
    def music_catalog(row: pd.Series):
        """Kaggle/Spotify 포맷 music_catalog.csv 한 행을 MusicCatalog 노드에 프로퍼티로만 적재한다. 엣지·별도 노드 연결은 별도 쿼리에서 처리."""
        track_id = str(row["track_id"]).strip()
        content_id = f"mc_{track_id}"
        query = """
        MERGE (mc:MusicCatalog {content_id: $content_id})
        SET mc.name = $track_name,
            mc.track_id = $track_id,
            mc.content_id = $content_id,
            mc.track_name = $track_name,
            mc.track_artist = $track_artist,
            mc.track_popularity = $track_popularity,
            mc.track_album_id = $track_album_id,
            mc.track_album_name = $track_album_name,
            mc.track_album_release_date = $track_album_release_date,
            mc.playlist_name = $playlist_name,
            mc.playlist_id = $playlist_id,
            mc.playlist_genre = $playlist_genre,
            mc.playlist_subgenre = $playlist_subgenre,
            mc.danceability = $danceability,
            mc.energy = $energy,
            mc.`key` = $key,
            mc.loudness = $loudness,
            mc.mode = $mode,
            mc.speechiness = $speechiness,
            mc.acousticness = $acousticness,
            mc.instrumentalness = $instrumentalness,
            mc.liveness = $liveness,
            mc.valence = $valence,
            mc.tempo = $tempo,
            mc.duration_ms = $duration_ms
        """
        parameters = {
            "content_id": content_id,
            "track_id": track_id,
            "track_name": _scalar_or_none(row["track_name"]),
            "track_artist": _scalar_or_none(row["track_artist"]),
            "track_popularity": _scalar_or_none(row["track_popularity"]),
            "track_album_id": _scalar_or_none(row["track_album_id"]),
            "track_album_name": _scalar_or_none(row["track_album_name"]),
            "track_album_release_date": _scalar_or_none(row["track_album_release_date"]),
            "playlist_name": _scalar_or_none(row["playlist_name"]),
            "playlist_id": _scalar_or_none(row["playlist_id"]),
            "playlist_genre": _scalar_or_none(row["playlist_genre"]),
            "playlist_subgenre": _scalar_or_none(row["playlist_subgenre"]),
            "danceability": _scalar_or_none(row["danceability"]),
            "energy": _scalar_or_none(row["energy"]),
            "key": _scalar_or_none(row["key"]),
            "loudness": _scalar_or_none(row["loudness"]),
            "mode": _scalar_or_none(row["mode"]),
            "speechiness": _scalar_or_none(row["speechiness"]),
            "acousticness": _scalar_or_none(row["acousticness"]),
            "instrumentalness": _scalar_or_none(row["instrumentalness"]),
            "liveness": _scalar_or_none(row["liveness"]),
            "valence": _scalar_or_none(row["valence"]),
            "tempo": _scalar_or_none(row["tempo"]),
            "duration_ms": _scalar_or_none(row["duration_ms"]),
        }
        return query, parameters

    @staticmethod
    def recommands(row: pd.Series):
        """recommands.csv: Recommand 노드, RecommendationCategory 및 MusicCatalog 관계."""
        query = """
        MERGE (r:Recommand {recommendation_id: $recommendation_id})
        SET
            r.evidence_summary = $evidence_summary,
            r.metadata_json = $metadata_json
        MERGE (rc:RecommendationCategory {recommendation_category: $recommendation_category})
        MERGE (r)-[:has_recommendation_category]->(rc)
        MERGE (mc:MusicCatalog {content_id: $content_id})
        MERGE (r)-[:related_by]->(mc)
        """
        parameters = {
            "recommendation_id": str(row["recommend_id"]),
            "recommendation_category": str(row["recommendation_category"]),
            "evidence_summary": _scalar_or_none(row.get("evidence_summary")),
            "content_id": str(row["content_id"]),
            "metadata_json": _scalar_or_none(row.get("metadata_json")),
        }
        return query, parameters
