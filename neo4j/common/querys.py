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
    def ml_outputs(row: pd.Series):
        """ml_outputs.csv: User -[:has_outputs]-> MlOutputs, 장르/아티스트/무드는 FOREACH로 다중 연결."""
        query = """
        MERGE (u:User {user_id: $user_id})
        MERGE (mo:MlOutputs {user_id: $user_id})
        SET
            mo.user_id = $user_id,
            mo.status = $status,
            mo.preferred_tempo = $preferred_tempo,
            mo.recent_listening_level = $recent_listening_level,
            mo.recent_discovery_level = $recent_discovery_level,
            mo.repeat_listening_ratio = $repeat_listening_ratio,
            mo.new_artist_acceptance = $new_artist_acceptance,
            mo.personalization_strength = $personalization_strength,
            mo.discovery_readiness = $discovery_readiness,
            mo.new_release_affinity = $new_release_affinity
        MERGE (u)-[:has_outputs]->(mo)
        FOREACH (g IN $genres | MERGE (mo)-[:preferred_genres]->(gn:Genre {genre: g}))
        FOREACH (a IN $artists | MERGE (mo)-[:preferred_artists]->(ar:Artist {artist: a}))
        FOREACH (m IN $moods | MERGE (mo)-[:preferred_moods]->(mm:Mood {mood: m}))
        """
        uid = str(row["user_id"])
        parameters = {
            "user_id": uid,
            "status": _scalar_or_none(row["status"]),
            "preferred_tempo": _scalar_or_none(row["preferred_tempo"]),
            "recent_listening_level": _scalar_or_none(row["recent_listening_level"]),
            "recent_discovery_level": _scalar_or_none(row["recent_discovery_level"]),
            "repeat_listening_ratio": _scalar_or_none(row["repeat_listening_ratio"]),
            "new_artist_acceptance": _scalar_or_none(row["new_artist_acceptance"]),
            "personalization_strength": _scalar_or_none(row["personalization_strength"]),
            "discovery_readiness": _scalar_or_none(row["discovery_readiness"]),
            "new_release_affinity": _scalar_or_none(row["new_release_affinity"]),
            "genres": _split_multi(row.get("preferred_genres")),
            "artists": _split_multi(row.get("preferred_artists")),
            "moods": _split_multi(row.get("preferred_moods")),
        }
        return query, parameters

    @staticmethod
    def music_catalog(row: pd.Series):
        """music_catalog.csv: MusicCatalog 중심, Album-[:in_album]->MusicCatalog 등 관계 구성."""
        query = """
        MERGE (mc:MusicCatalog {content_id: $content_id})
        SET mc.title = $title,
            mc.name = $title
        FOREACH (_ IN CASE WHEN $artist IS NOT NULL THEN [1] ELSE [] END |
            MERGE (mc)-[:has_artist]->(ar:Artist {artist: $artist})
        )
        FOREACH (_ IN CASE WHEN $album IS NOT NULL THEN [1] ELSE [] END |
            MERGE (al:Album {album: $album})-[:in_album]->(mc)
        )
        FOREACH (g IN $genres | MERGE (mc)-[:has_genre]->(gn:Genre {genre: g}))
        FOREACH (m IN $moods | MERGE (mc)-[:has_mood]->(mm:Mood {mood: m}))
        FOREACH (_ IN CASE WHEN $tempo IS NOT NULL THEN [1] ELSE [] END |
            MERGE (mc)-[:has_tempo]->(tp:Tempo {tempo: $tempo})
        )
        FOREACH (_ IN CASE WHEN $release_type IS NOT NULL THEN [1] ELSE [] END |
            MERGE (mc)-[:has_release_type]->(rt:ReleaseType {release_type: $release_type})
        )
        """
        parameters = {
            "content_id": str(row["content_id"]),
            "title": _scalar_or_none(row["title"]),
            "artist": _scalar_or_none(row.get("artist")),
            "album": _scalar_or_none(row.get("album")),
            "tempo": _scalar_or_none(row.get("tempo")),
            "release_type": _scalar_or_none(row.get("release_type")),
            "genres": _split_multi(row.get("genres")),
            "moods": _split_multi(row.get("moods")),
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
