# 로그
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.kag.connection import Neo4j_Connection


def _limit_from_row(row: dict | None, default: int = 10) -> int:
    if not row:
        return default
    raw = row.get("limit", default)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, 500))


####################################################################
# 실행할 쿼리 목록 정의
####################################################################
class KagCypherQuery:
    """KAG Cypher Query 목록 정의.

    빌더는 ``(query, parameters)`` 만 반환한다.

    반환 컬럼 ``track_id``는 Neo4j ``MusicCatalog`` 키이다. 앱 계약의 ``content_id``와
    다를 수 있으므로 어댑터/서비스에서 필요 시 매핑한다.
    """

    @staticmethod
    def user_info(row: dict) -> tuple[str, dict]:
        """
        지정한 사용자의 이름을 조회한다.

        row:
            user_id (str): 사용자 ID
        """

        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u.display_name AS display_name
        """

        parameters = {
            "user_id": row["user_id"],
        }
        return query, parameters

    @staticmethod
    def personalized_recommendation_candidates(row: dict) -> tuple[str, dict]:
        """
        primary_goal ``personalized_recommendation`` / 카테고리 ``personalized_match`` 후보.

        row:
            genre_candidates (list[str], optional): 비면 인기순 전체 폴백.
            mood_candidates (list[str], optional): 그래프에 ``HAS_MOOD``가 있으면 가중 정렬에 사용.
            limit (int, optional): 기본 10, 최대 500.
            user_id (str, optional): 예약. 현재 쿼리에는 미사용.
        """
        genre_candidates = list(row.get("genre_candidates") or [])
        mood_candidates = list(row.get("mood_candidates") or [])
        limit = _limit_from_row(row)

        if genre_candidates:
            query = """
            MATCH (mc:MusicCatalog)-[:HAS_GENRE]->(g:Genre)
            WHERE g.genre IN $genre_candidates
            WITH DISTINCT mc
            OPTIONAL MATCH (mc)-[:HAS_MOOD]->(mo:Mood)
            WITH mc, sum(CASE WHEN mo.mood IN $mood_candidates THEN 1 ELSE 0 END) AS mood_score
            RETURN mc.track_id AS track_id
            ORDER BY mood_score DESC, mc.track_popularity DESC NULLS LAST
            LIMIT $limit
            """
        else:
            query = """
            MATCH (mc:MusicCatalog)
            OPTIONAL MATCH (mc)-[:HAS_MOOD]->(mo:Mood)
            WITH mc, sum(CASE WHEN mo.mood IN $mood_candidates THEN 1 ELSE 0 END) AS mood_score
            RETURN mc.track_id AS track_id
            ORDER BY mood_score DESC, mc.track_popularity DESC NULLS LAST
            LIMIT $limit
            """

        parameters = {
            "genre_candidates": genre_candidates,
            "mood_candidates": mood_candidates,
            "limit": limit,
        }
        return query, parameters

    @staticmethod
    def new_release_recommendation_candidates(row: dict) -> tuple[str, dict]:
        """
        primary_goal ``new_release_recommendation`` / 카테고리 ``new_release`` 후보.

        ``track_album_release_date`` 문자열을 최신순으로 정렬한다 (ISO 유사 ``YYYY-MM-DD`` 가정).

        row:
            limit (int, optional): 기본 10, 최대 500.
            user_id (str, optional): 예약. 미사용.
        """
        limit = _limit_from_row(row)
        query = """
        MATCH (mc:MusicCatalog)
        WHERE mc.track_album_release_date IS NOT NULL
          AND trim(toString(mc.track_album_release_date)) <> ''
        RETURN mc.track_id AS track_id
        ORDER BY mc.track_album_release_date DESC
        LIMIT $limit
        """
        parameters = {"limit": limit}
        return query, parameters

    @staticmethod
    def discovery_recommendation_candidates(row: dict) -> tuple[str, dict]:
        """
        primary_goal ``discovery_recommendation`` / 카테고리 ``discovery_candidate`` 후보.

        row:
            exclude_genres (list[str], optional): 제외할 장르. 비면 전체에서 인기순 폴백.
            limit (int, optional): 기본 10, 최대 500.
            user_id (str, optional): 예약. 미사용.
        """
        exclude_genres = list(row.get("exclude_genres") or [])
        limit = _limit_from_row(row)

        if exclude_genres:
            query = """
            MATCH (mc:MusicCatalog)-[:HAS_GENRE]->(g:Genre)
            WHERE NOT g.genre IN $exclude_genres
            RETURN DISTINCT mc.track_id AS track_id, mc.track_popularity AS popularity
            ORDER BY popularity DESC NULLS LAST
            LIMIT $limit
            """
            parameters = {"exclude_genres": exclude_genres, "limit": limit}
        else:
            query = """
            MATCH (mc:MusicCatalog)
            RETURN mc.track_id AS track_id
            ORDER BY mc.track_popularity DESC NULLS LAST
            LIMIT $limit
            """
            parameters = {"limit": limit}

        return query, parameters


if __name__ == "__main__":
    conn = Neo4j_Connection()