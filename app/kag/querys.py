# 로그
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
# 실행할 쿼리 목록 정의 (조각 조립 방식)
####################################################################
class KagCypherQuery:
    """KAG Cypher Query 목록 정의.

    빌더는 ``(query, parameters)`` 만 반환한다.
    문자열은 `_assemble_query`로 조립하고, 조각별로 필요한 바인딩은 `_merge_params`로 합친다.

    반환 컬럼 ``track_id``는 Neo4j ``MusicCatalog`` 키이다. 앱 계약의 ``content_id``와
    다를 수 있으므로 어댑터/서비스에서 필요 시 매핑한다.
    """

    #############################################################
    # 쿼리 / 파라미터 조립 함수 
    #############################################################
    @staticmethod
    def _assemble_query(*blocks: str) -> str:
        """비어 있지 않은 블록만 줄바꿈으로 이어 최종 Cypher 문자열을 만든다."""
        parts = []
        for b in blocks:
            if not b:
                continue
            stripped = b.strip()
            if stripped:
                parts.append(stripped)
        return "\n".join(parts)

    @staticmethod
    def _merge_params(*param_parts: dict) -> dict:
        """조각에서 넘긴 dict만 합친다. 같은 키는 뒤쪽이 덮어쓴다."""
        merged: dict = {}
        for p in param_parts:
            merged.update(p)
        return merged

    #############################################################
    # 조립할 쿼리 조각 가공 함수 
    #############################################################

    # ----- 개인화: 입력 가공 -----
    @staticmethod
    def _prep_personalized_row(row: dict) -> tuple[list[str], list[str], int]:
        genre_candidates = list(row.get("genre_candidates") or [])
        mood_candidates = list(row.get("mood_candidates") or [])
        limit = _limit_from_row(row)
        return genre_candidates, mood_candidates, limit

    @staticmethod
    def _frag_mc_through_genre(genre_candidates: list[str]) -> tuple[str, dict]:
        """장르 후보 유무에 따라 진입 MATCH/WITH 조각과 파라미터."""
        if genre_candidates:
            frag = """MATCH (mc:MusicCatalog)-[:HAS_GENRE]->(g:Genre)
WHERE g.genre IN $genre_candidates
WITH DISTINCT mc"""
            return frag, {"genre_candidates": genre_candidates}
        frag = "MATCH (mc:MusicCatalog)"
        return frag, {}

    @staticmethod
    def _frag_mood_score_optional(mood_candidates: list[str]) -> tuple[str, dict]:
        """무드 후보가 있을 때만 무드 가중 WITH 조각과 파라미터."""
        if not mood_candidates:
            return "", {}
        frag = """OPTIONAL MATCH (mc)-[:HAS_MOOD]->(mo:Mood)
WITH mc, sum(CASE WHEN mo.mood IN $mood_candidates THEN 1 ELSE 0 END) AS mood_score"""
        return frag, {"mood_candidates": mood_candidates}

    @staticmethod
    def _frag_personalized_order_by(use_mood_score: bool) -> str:
        if use_mood_score:
            return "ORDER BY mood_score DESC, mc.track_popularity DESC"
        return "ORDER BY mc.track_popularity DESC"

    # ----- 신규 발매: 입력 가공 -----
    @staticmethod
    def _prep_new_release_row(row: dict) -> int:
        return _limit_from_row(row)

    @staticmethod
    def _frag_release_date_where() -> str:
        return """WHERE mc.track_album_release_date IS NOT NULL
  AND trim(toString(mc.track_album_release_date)) <> ''"""

    # ----- 발견: 입력 가공 -----
    @staticmethod
    def _prep_discovery_row(row: dict) -> tuple[list[str], int]:
        exclude_genres = list(row.get("exclude_genres") or [])
        limit = _limit_from_row(row)
        return exclude_genres, limit

    @staticmethod
    def _frag_discovery_match(exclude_genres: list[str]) -> tuple[str, dict]:
        if exclude_genres:
            frag = """MATCH (mc:MusicCatalog)-[:HAS_GENRE]->(g:Genre)
WHERE NOT g.genre IN $exclude_genres"""
            return frag, {"exclude_genres": exclude_genres}
        return "MATCH (mc:MusicCatalog)", {}

    @staticmethod
    def _frag_discovery_return_order(use_exclude_filter: bool) -> tuple[str, str]:
        """RETURN 절 문자열, ORDER BY 절 문자열."""
        if use_exclude_filter:
            return (
                "RETURN DISTINCT mc.track_id AS track_id, mc.track_popularity AS popularity",
                "ORDER BY popularity DESC",
            )
        return "RETURN mc.track_id AS track_id", "ORDER BY mc.track_popularity DESC"



    #############################################################
    # ----- 실행 쿼리 목록 -----
    #############################################################
    @staticmethod
    def user_info(row: dict) -> tuple[str, dict]:
        """
        지정한 사용자의 이름을 조회한다.

        row:
            user_id (str): 사용자 ID
        """
        query = KagCypherQuery._assemble_query(
            "MATCH (u:User {user_id: $user_id})",
            "RETURN u.display_name AS display_name",
        )
        return query, {"user_id": row["user_id"]}

    @staticmethod
    def personalized_recommendation_candidates(row: dict) -> tuple[str, dict]:
        """
        primary_goal ``personalized_recommendation`` / 카테고리 ``personalized_match`` 후보.

        row:
            genre_candidates (list[str], optional): 비면 전체 MusicCatalog 진입 후 인기순.
            mood_candidates (list[str], optional): 있으면 HAS_MOOD 기반 가중 정렬 조각을 붙인다.
            limit (int, optional): 기본 10, 최대 500.
            user_id (str, optional): 예약. 현재 쿼리에는 미사용.
        """
        genre_candidates, mood_candidates, limit = KagCypherQuery._prep_personalized_row(row)
        match_part, p_match = KagCypherQuery._frag_mc_through_genre(genre_candidates)
        mood_part, p_mood = KagCypherQuery._frag_mood_score_optional(mood_candidates)
        use_mood = bool(mood_part)
        order_by = KagCypherQuery._frag_personalized_order_by(use_mood)

        query = KagCypherQuery._assemble_query(
            match_part,
            mood_part,
            "RETURN mc.track_id AS track_id",
            order_by,
            "LIMIT $limit",
        )
        params = KagCypherQuery._merge_params(p_match, p_mood, {"limit": limit})
        return query, params

    @staticmethod
    def new_release_recommendation_candidates(row: dict) -> tuple[str, dict]:
        """
        primary_goal ``new_release_recommendation`` / 카테고리 ``new_release`` 후보.

        ``track_album_release_date`` 문자열을 최신순으로 정렬한다 (ISO 유사 ``YYYY-MM-DD`` 가정).

        row:
            limit (int, optional): 기본 10, 최대 500.
            user_id (str, optional): 예약. 미사용.
        """
        limit = KagCypherQuery._prep_new_release_row(row)
        query = KagCypherQuery._assemble_query(
            "MATCH (mc:MusicCatalog)",
            KagCypherQuery._frag_release_date_where(),
            "RETURN mc.track_id AS track_id",
            "ORDER BY mc.track_album_release_date DESC",
            "LIMIT $limit",
        )
        return query, {"limit": limit}

    @staticmethod
    def discovery_recommendation_candidates(row: dict) -> tuple[str, dict]:
        """
        primary_goal ``discovery_recommendation`` / 카테고리 ``discovery_candidate`` 후보.

        row:
            exclude_genres (list[str], optional): 제외할 장르. 비면 전체에서 인기순 폴백.
            limit (int, optional): 기본 10, 최대 500.
            user_id (str, optional): 예약. 미사용.
        """
        exclude_genres, limit = KagCypherQuery._prep_discovery_row(row)
        match_part, p_match = KagCypherQuery._frag_discovery_match(exclude_genres)
        use_exclude = bool(exclude_genres)
        ret_clause, ord_clause = KagCypherQuery._frag_discovery_return_order(use_exclude)

        query = KagCypherQuery._assemble_query(
            match_part,
            ret_clause,
            ord_clause,
            "LIMIT $limit",
        )
        params = KagCypherQuery._merge_params(p_match, {"limit": limit})
        return query, params


if __name__ == "__main__":
    logger.info("Neo4j 실행 스모크는 python -m app.kag.adapters.execute_querys 를 사용하세요.")
