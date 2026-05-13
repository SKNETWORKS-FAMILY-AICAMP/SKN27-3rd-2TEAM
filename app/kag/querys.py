# 로그
import logging
from collections.abc import Callable

from app.kag.connection import Neo4j_Connection
from app.kag.constant import KagQueryTemplateConstants

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
class KagQueryTools:
    """외부 Agent가 호출하는 KAG Query Tool 함수 모음.

    쿼리 문자열/파라미터 기본 템플릿은 `KagQueryTemplateConstants`에서 조회한다.
    """

    @staticmethod
    def _normalize_limit(params: dict) -> dict:
        out = dict(params)
        out["limit"] = _limit_from_row(out, default=10)
        return out

    @staticmethod
    def _apply_parameter_template(query_key: str, params: dict | None) -> dict:
        payload = dict(params or {})
        tmpl = KagQueryTemplateConstants.parameter_template_for(query_key)
        defaults = dict(tmpl.get("defaults") or {})
        required = list(tmpl.get("required") or [])

        merged = dict(defaults)
        merged.update(payload)
        merged = KagQueryTools._normalize_limit(merged)

        for key in required:
            value = merged.get(key)
            if value is None:
                raise ValueError(f"{query_key}: required parameter missing -> {key}")
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"{query_key}: required parameter empty -> {key}")
        return merged

    @staticmethod
    def build_query(query_key: str, params: dict | None = None) -> tuple[str, dict]:
        query = KagQueryTemplateConstants.cypher_for(query_key)
        merged_params = KagQueryTools._apply_parameter_template(query_key, params)
        return query, merged_params

    @staticmethod
    def execute(query_key: str, params: dict | None, conn: Neo4j_Connection) -> list[dict]:
        query, merged_params = KagQueryTools.build_query(query_key, params)
        records = conn.execute_query(query, merged_params)
        return [dict(r) for r in records]

    @staticmethod
    def tool_registry() -> dict[str, Callable]:
        """LLM Agent가 호출할 KAG Query Tool 엔트리 포인트 목록.

        용도:
        - 어댑터 계층과 분리된 상태에서 Agent가 직접 쿼리 툴을 선택/호출하도록 지원한다.
        - 호출자는 ``tool_name`` 문자열로 함수를 선택해 실행할 수 있다.
        """
        return {
            "tool_q_search_001_music_basic_info_lookup": KagQueryTools.tool_q_search_001_music_basic_info_lookup,
            "tool_q_search_003_music_condition_search": KagQueryTools.tool_q_search_003_music_condition_search,
            "tool_q_search_009_artist_music_lookup": KagQueryTools.tool_q_search_009_artist_music_lookup,
            "tool_q_search_011_temporal_music_lookup": KagQueryTools.tool_q_search_011_temporal_music_lookup,
            "tool_q_rec_001_genre_based_recommendation": KagQueryTools.tool_q_rec_001_genre_based_recommendation,
            "tool_q_rec_002_mood_based_recommendation": KagQueryTools.tool_q_rec_002_mood_based_recommendation,
            "tool_q_rec_003_situation_based_recommendation": KagQueryTools.tool_q_rec_003_situation_based_recommendation,
            "tool_q_rec_004_weather_based_recommendation": KagQueryTools.tool_q_rec_004_weather_based_recommendation,
            "tool_q_rec_006_popularity_based_recommendation": KagQueryTools.tool_q_rec_006_popularity_based_recommendation,
            "tool_q_rec_008_hybrid_context_recommendation": KagQueryTools.tool_q_rec_008_hybrid_context_recommendation,
        }

    # ----- tool wrappers (현재 운영 쿼리) -----
    @staticmethod
    def tool_q_search_001_music_basic_info_lookup(conn: Neo4j_Connection, keyword: str, limit: int = 10) -> list[dict]:
        """곡명 키워드로 기본 메타데이터를 빠르게 찾는다.

        용도:
        - 특정 곡 제목/키워드 기반으로 트랙 기본 정보를 조회한다.
        - 정보 탐색형 질의의 첫 진입점으로 사용한다.

        예상 질문:
        - "love 들어간 노래 찾아줘"
        - "shape of you 곡 정보 알려줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_SEARCH_001, {"keyword": keyword, "limit": limit}, conn)

    @staticmethod
    def tool_q_search_003_music_condition_search(
        conn: Neo4j_Connection,
        genre: str | None = None,
        subgenre: str | None = None,
        artist: str | None = None,
        release_year: int | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """장르/서브장르/아티스트/연도 조건을 조합해 곡을 검색한다.

        용도:
        - 필터 기반 탐색 질의를 처리한다.
        - 여러 조건이 동시에 들어오는 정교한 검색 요청에 대응한다.

        예상 질문:
        - "2020년 이후 힙합 중 Drake 비슷한 곡 찾아줘"
        - "pop 장르에서 여성 보컬 느낌 곡 보여줘"
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_SEARCH_003,
            {
                "genre": genre,
                "subgenre": subgenre,
                "artist": artist,
                "release_year": release_year,
                "limit": limit,
            },
            conn,
        )

    @staticmethod
    def tool_q_search_009_artist_music_lookup(conn: Neo4j_Connection, artist: str, limit: int = 30) -> list[dict]:
        """아티스트 중심으로 대표/인기 곡을 조회한다.

        용도:
        - 특정 아티스트 디스코그래피 탐색 요청을 처리한다.
        - 아티스트 이름 일부만 주어져도 부분 일치 검색이 가능하다.

        예상 질문:
        - "Taylor Swift 노래 추천해줘"
        - "아이유 곡 목록 보여줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_SEARCH_009, {"artist": artist, "limit": limit}, conn)

    @staticmethod
    def tool_q_search_011_temporal_music_lookup(
        conn: Neo4j_Connection,
        year: int | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """특정 연도 또는 연도 구간 기준으로 곡을 조회한다.

        용도:
        - 시대/시점 조건이 핵심인 탐색 요청을 처리한다.
        - 단일 연도 검색과 기간 검색을 모두 지원한다.

        예상 질문:
        - "2018년 노래 추천해줘"
        - "2010~2015 사이 인기곡 알려줘"
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_SEARCH_011,
            {
                "year": year,
                "start_year": start_year,
                "end_year": end_year,
                "limit": limit,
            },
            conn,
        )

    @staticmethod
    def tool_q_rec_001_genre_based_recommendation(conn: Neo4j_Connection, genre: str, limit: int = 10) -> list[dict]:
        """지정 장르 기반 기본 추천을 수행한다.

        용도:
        - 장르 선호가 명확한 사용자의 기본 추천 요청에 대응한다.
        - 개인화 정보가 부족할 때 안전한 초기 추천으로 사용한다.

        예상 질문:
        - "락 장르로 추천해줘"
        - "요즘 들을 만한 R&B 추천"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_REC_001, {"genre": genre, "limit": limit}, conn)

    @staticmethod
    def tool_q_rec_002_mood_based_recommendation(conn: Neo4j_Connection, mood: str, limit: int = 10) -> list[dict]:
        """분위기(mood) 태그를 기준으로 추천한다.

        용도:
        - 감정/분위기 중심 추천 요청을 처리한다.
        - 차분함, 신남 등 정성적 무드 질의에 대응한다.

        예상 질문:
        - "잔잔한 분위기 노래 추천해줘"
        - "신나는 무드 플레이리스트 만들어줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_REC_002, {"mood": mood, "limit": limit}, conn)

    @staticmethod
    def tool_q_rec_003_situation_based_recommendation(
        conn: Neo4j_Connection,
        situation: str,
        limit: int = 10,
    ) -> list[dict]:
        """상황/활동 컨텍스트를 기준으로 추천한다.

        용도:
        - 운동, 출근, 집중, 여행 같은 사용 맥락 기반 추천을 처리한다.
        - 상황 태그와 매핑된 곡을 우선 노출한다.

        예상 질문:
        - "운동할 때 들을 노래 추천"
        - "집중할 때 좋은 음악 찾아줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_REC_003, {"situation": situation, "limit": limit}, conn)

    @staticmethod
    def tool_q_rec_004_weather_based_recommendation(conn: Neo4j_Connection, weather: str, limit: int = 10) -> list[dict]:
        """날씨 컨텍스트를 기준으로 추천한다.

        용도:
        - 맑음/비/눈 등 날씨 기반 감성 추천 요청을 처리한다.
        - 일상 컨텍스트 질의에서 빠른 후보군 생성을 담당한다.

        예상 질문:
        - "비 오는 날 듣기 좋은 노래 추천"
        - "화창한 날씨에 어울리는 곡 찾아줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_REC_004, {"weather": weather, "limit": limit}, conn)

    @staticmethod
    def tool_q_rec_006_popularity_based_recommendation(
        conn: Neo4j_Connection,
        genre: str | None = None,
        subgenre: str | None = None,
        artist: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """조건을 반영하되 인기도를 우선해 추천한다.

        용도:
        - 개인화 신호가 약할 때 대중성 기반으로 품질을 보장한다.
        - 조건 검색과 인기 정렬을 결합한 안전한 추천 경로로 사용한다.

        예상 질문:
        - "팝 중에서 인기 많은 곡 추천해줘"
        - "OO 아티스트 느낌으로 대중적인 곡 찾아줘"
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_REC_006,
            {
                "genre": genre,
                "subgenre": subgenre,
                "artist": artist,
                "limit": limit,
            },
            conn,
        )

    @staticmethod
    def tool_q_rec_008_hybrid_context_recommendation(
        conn: Neo4j_Connection,
        genre: str | None = None,
        mood: str | None = None,
        situation: str | None = None,
        weather: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """장르/무드/상황/날씨를 함께 고려한 하이브리드 추천을 수행한다.

        용도:
        - 복합 조건이 들어온 고난도 추천 질의를 처리한다.
        - 다중 컨텍스트 매칭 수와 인기도를 함께 점수화해 정렬한다.

        예상 질문:
        - "비 오는 날, 차분한 인디 추천해줘"
        - "드라이브 상황에 신나는 팝 추천해줘"
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_REC_008,
            {
                "genre": genre,
                "mood": mood,
                "situation": situation,
                "weather": weather,
                "limit": limit,
            },
            conn,
        )


if __name__ == "__main__":
    # 스모크 테스트: 쿼리 문법/실행 가능 여부만 확인한다.
    # (결과 개수/정확도 검증은 범위 밖)
    conn = Neo4j_Connection()

    smoke_cases = [
        (
            "Q_SEARCH_001",
            lambda: KagQueryTools.tool_q_search_001_music_basic_info_lookup(conn, keyword="love", limit=3),
        ),
        (
            "Q_SEARCH_003",
            lambda: KagQueryTools.tool_q_search_003_music_condition_search(conn, genre="hip hop", limit=3),
        ),
        (
            "Q_SEARCH_009",
            lambda: KagQueryTools.tool_q_search_009_artist_music_lookup(conn, artist="Taylor", limit=3),
        ),
        (
            "Q_SEARCH_011",
            lambda: KagQueryTools.tool_q_search_011_temporal_music_lookup(conn, year=2020, limit=3),
        ),
        (
            "Q_REC_001",
            lambda: KagQueryTools.tool_q_rec_001_genre_based_recommendation(conn, genre="rock", limit=3),
        ),
        (
            "Q_REC_002",
            lambda: KagQueryTools.tool_q_rec_002_mood_based_recommendation(conn, mood="calm", limit=3),
        ),
        (
            "Q_REC_003",
            lambda: KagQueryTools.tool_q_rec_003_situation_based_recommendation(conn, situation="exercise", limit=3),
        ),
        (
            "Q_REC_004",
            lambda: KagQueryTools.tool_q_rec_004_weather_based_recommendation(conn, weather="weather_sunny", limit=3),
        ),
        (
            "Q_REC_006",
            lambda: KagQueryTools.tool_q_rec_006_popularity_based_recommendation(conn, genre="pop", limit=3),
        ),
        (
            "Q_REC_008",
            lambda: KagQueryTools.tool_q_rec_008_hybrid_context_recommendation(
                conn,
                genre="pop",
                mood="calm",
                weather="weather_sunny",
                limit=3,
            ),
        ),
    ]

    logger.info("KAG Query Tool smoke 시작")
    for label, runner in smoke_cases:
        try:
            rows = runner()
            logger.info("[SMOKE PASS] %s rows=%s", label, len(rows))
        except Exception as exc:  # noqa: BLE001
            logger.exception("[SMOKE FAIL] %s (%s: %s)", label, type(exc).__name__, exc)
    logger.info("KAG Query Tool smoke 완료")
