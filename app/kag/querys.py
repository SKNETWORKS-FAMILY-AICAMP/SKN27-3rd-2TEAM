# 로그
import logging
from collections.abc import Callable

from app.kag.connection import Neo4j_Connection
from app.kag.constant import KagQueryTemplateConstants, resolve_scenario_param

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


def _max_depth_from_row(row: dict | None, default: int = 3) -> int:
    if not row:
        return default
    raw = row.get("max_depth", default)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, 10))


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
        # if query_key == KagQueryTemplateConstants.Q_SEARCH_008:
        #     merged["max_depth"] = _max_depth_from_row(merged, default=int((tmpl.get("defaults") or {}).get("max_depth") or 3))

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
            "tool_q_search_002_music_relation_info_lookup": KagQueryTools.tool_q_search_002_music_relation_info_lookup,
            "tool_q_search_003_music_condition_search": KagQueryTools.tool_q_search_003_music_condition_search,
            "tool_q_search_004_similar_music_lookup": KagQueryTools.tool_q_search_004_similar_music_lookup,
            "tool_q_search_005_music_stat_lookup": KagQueryTools.tool_q_search_005_music_stat_lookup,
            "tool_q_search_006_connected_node_music_lookup": KagQueryTools.tool_q_search_006_connected_node_music_lookup,
            "tool_q_search_007_music_common_feature_lookup": KagQueryTools.tool_q_search_007_music_common_feature_lookup,
            # "tool_q_search_008_music_path_lookup": KagQueryTools.tool_q_search_008_music_path_lookup,
            "tool_q_search_009_artist_music_lookup": KagQueryTools.tool_q_search_009_artist_music_lookup,
            "tool_q_search_010_category_top_music_lookup": KagQueryTools.tool_q_search_010_category_top_music_lookup,
            # "tool_q_search_011_temporal_music_lookup": KagQueryTools.tool_q_search_011_temporal_music_lookup,
            "tool_q_search_012_composite_condition_search": KagQueryTools.tool_q_search_012_composite_condition_search,
            # "tool_q_search_013_high_connection_music_lookup": KagQueryTools.tool_q_search_013_high_connection_music_lookup,
            # "tool_q_search_014_relation_type_lookup": KagQueryTools.tool_q_search_014_relation_type_lookup,
            "tool_q_rec_001_genre_based_recommendation": KagQueryTools.tool_q_rec_001_genre_based_recommendation,
            "tool_q_rec_002_mood_based_recommendation": KagQueryTools.tool_q_rec_002_mood_based_recommendation,
            "tool_q_rec_003_situation_based_recommendation": KagQueryTools.tool_q_rec_003_situation_based_recommendation,
            "tool_q_rec_004_weather_based_recommendation": KagQueryTools.tool_q_rec_004_weather_based_recommendation,
            "tool_q_rec_005_similar_song_recommendation": KagQueryTools.tool_q_rec_005_similar_song_recommendation,
            "tool_q_rec_006_popularity_based_recommendation": KagQueryTools.tool_q_rec_006_popularity_based_recommendation,
            "tool_q_rec_007_diversity_recommendation": KagQueryTools.tool_q_rec_007_diversity_recommendation,
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
    def tool_q_search_002_music_relation_info_lookup(
        conn: Neo4j_Connection,
        keyword: str,
        relation_filter: str | None = None,
        node_label_filter: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """특정 곡(제목 키워드)에 연결된 관계·상대 노드를 조회한다.

        예상 질문:
        - Ditto랑 연결된 정보 보여줘
        - 이 노래는 어떤 날씨랑 연결돼?
        - Hype Boy랑 연결된 감정이 있어?
        - Attention은 어떤 상황에 어울려?
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_SEARCH_002,
            {
                "keyword": keyword,
                "relation_filter": relation_filter,
                "node_label_filter": node_label_filter,
                "limit": limit,
            },
            conn,
        )

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
        - "2019년에 발매된 남성 가수 노래 찾아줘"
        - "2020년에 발매된 pop장르 노래 알려줘"
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
    def tool_q_search_004_similar_music_lookup(conn: Neo4j_Connection, keyword: str, limit: int = 20) -> list[dict]:
        """기준 곡과 공유 특성 노드가 많은 다른 곡을 조회한다.

        예상 질문:
        - Ditto랑 비슷한 노래 찾아줘
        - Hype Boy랑 비슷한 곡 보여줘
        - 이 가수의 노래와 비슷한 분위기를 가지는 노래 알려줘
        - 내가 이 노래를 좋아하는데 이 노래와 비슷한 분위기를 가지는 노래 알려줘
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_SEARCH_004, {"keyword": keyword, "limit": limit}, conn)

    @staticmethod
    def tool_q_search_005_music_stat_lookup(conn: Neo4j_Connection, stat_type: str, limit: int = 10) -> list[dict]:
        """장르·아티스트·연도별 곡 수 집계 상위 그룹을 조회한다. stat_type: genre | artist | year.

        예상 질문:
        - 특정 장르에 해당하는 곡 알려줘
        - 아티스트별 곡 수 보여줘
        - 인기있는 장르 알려줘
        - 해당 연도 혹은 해당 달에 발매된 노래 알려줘
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_SEARCH_005, {"stat_type": stat_type, "limit": limit}, conn)

    @staticmethod
    def tool_q_search_006_connected_node_music_lookup(
        conn: Neo4j_Connection,
        node_value: str,
        node_label_filter: str | None = None,
        relation_filter: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """연결 차원 노드 속성 값으로 역방향 곡 검색을 수행한다.

        예상 질문:
        - 날씨와 연결된 음악 보여줘
        - 운동할 때 듣기 좋은 음악 찾아줘
        - 우울할 때 듣는 노래 있어?
        - 새벽에 어울리는 음악 알려줘
        - 집중할 때 듣기 좋은 음악 찾아줘
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_SEARCH_006,
            {
                "node_value": node_value,
                "node_label_filter": node_label_filter,
                "relation_filter": relation_filter,
                "limit": limit,
            },
            conn,
        )

    @staticmethod
    def tool_q_search_007_music_common_feature_lookup(
        conn: Neo4j_Connection,
        music1: str,
        music2: str,
        limit: int = 20,
    ) -> list[dict]:
        """두 곡이 공유하는 중간 특성 노드를 조회한다.

        예상 질문:
        - 내가 특정가수를 좋아하는데 이 가수와 장르가 비슷한 가수 노래 알려줘
        - 이 장르를 좋아하는데 이 장르를 노래하는 가수의 곡을 알려줘
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_SEARCH_007,
            {"music1": music1, "music2": music2, "limit": limit},
            conn,
        )

    # @staticmethod
    # def tool_q_search_008_music_path_lookup(
    #     conn: Neo4j_Connection,
    #     keyword: str,
    #     target_label: str | None = None,
    #     max_depth: int = 3,
    #     limit: int = 10,
    # ) -> list[dict]:
    #     """기준 곡에서 출발하는 그래프 경로를 길이 상한 내에서 조회한다.

    #     예상 질문:
    #     - Ditto에서 연결 경로 보여줘
    #     - 이 노래가 어떤 노드를 통해 추천되는지 보여줘
    #     - Hype Boy의 그래프 연결 구조 보여줘
    #     - 이 곡에서 감정 노드까지 가는 경로 보여줘
    #     - Attention이 어떤 장르와 상황으로 연결되는지 보여줘
    #     """
    #     return KagQueryTools.execute(
    #         KagQueryTemplateConstants.Q_SEARCH_008,
    #         {
    #             "keyword": keyword,
    #             "target_label": target_label,
    #             "max_depth": max_depth,
    #             "limit": limit,
    #         },
    #         conn,
    #     )

    @staticmethod
    def tool_q_search_009_artist_music_lookup(conn: Neo4j_Connection, artist: str, limit: int = 30) -> list[dict]:
        """아티스트 중심으로 대표/인기 곡을 조회한다.

        용도:
        - 특정 아티스트 디스코그래피 탐색 요청을 처리한다.
        - 아티스트 이름 일부만 주어져도 부분 일치 검색이 가능하다.

        예상 질문:
        - "Taylor Swift 노래 추천해줘"
        - "아이유 곡 목록 보여줘"
        - "Ed Sheeran 노래 추천해줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_SEARCH_009, {"artist": artist, "limit": limit}, conn)

    @staticmethod
    def tool_q_search_010_category_top_music_lookup(
        conn: Neo4j_Connection,
        category_type: str,
        category_value: str,
        limit: int = 20,
    ) -> list[dict]:
        """카테고리(장르·서브장르·아티스트) 내 인기 순 곡을 조회한다.

        예상 질문:
        - pop에서 인기 많은 노래 보여줘
        - rock 장르 인기곡 알려줘
        - 힙합 중 유명한 곡 찾아줘
        - Taylor Swift 노래 중 인기곡 보여줘
        - subgenre 기준으로 인기곡 찾아줘
        - 발매 연도 혹은 달 기준 인기곡 알려줘
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_SEARCH_010,
            {"category_type": category_type, "category_value": category_value, "limit": limit},
            conn,
        )

    # @staticmethod
    # def tool_q_search_011_temporal_music_lookup(
    #     conn: Neo4j_Connection,
    #     year: int | None = None,
    #     start_year: int | None = None,
    #     end_year: int | None = None,
    #     limit: int = 20,
    # ) -> list[dict]:
    #     """특정 연도 또는 연도 구간 기준으로 곡을 조회한다.

    #     용도:
    #     - 시대/시점 조건이 핵심인 탐색 요청을 처리한다.
    #     - 단일 연도 검색과 기간 검색을 모두 지원한다.

    #     예상 질문:
    #     - "2018년 노래 추천해줘"
    #     - "2010~2015 사이 인기곡 알려줘"
    #     """
    #     return KagQueryTools.execute(
    #         KagQueryTemplateConstants.Q_SEARCH_011,
    #         {
    #             "year": year,
    #             "start_year": start_year,
    #             "end_year": end_year,
    #             "limit": limit,
    #         },
    #         conn,
    #     )

    @staticmethod
    def tool_q_search_012_composite_condition_search(
        conn: Neo4j_Connection,
        genre: str | None = None,
        mood: str | None = None,
        situation: str | None = None,
        weather: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """장르·감정(LabelEmotion)·상황(time/season 포함)·날씨(LabelWeather) 복합 조건으로 곡을 검색한다.

        용도:
        - 장르·무드·상황·날씨를 한 번에 조합해 필터링할 때 사용한다.
        - mood/situation/weather는 그래프 `name`과 맞는 영문 토큰이거나 ``resolve_scenario_param``으로 한글 별칭을 치환한 값을 넘긴다.
        - 호출 예: 비+잔잔한 pop → genre=pop, mood=calm, weather=rain / 운동+힙합 → genre=hip hop, situation=gym / 밤 → situation=night

        예상 질문:
        - 비 오는 날 듣기 좋은 잔잔한 pop 음악 찾아줘
        - 운동할 때 듣는 신나는 힙합 보여줘
        - 밤에 듣기 좋은 감성적인 노래 찾아줘
        - 기분 좋을 때 들을 dance 음악 있어?
        - 집중할 때 어울리는 조용한 음악 찾아줘
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_SEARCH_012,
            {
                "genre": genre,
                "mood": mood,
                "situation": situation,
                "weather": weather,
                "limit": limit,
            },
            conn,
        )

    # @staticmethod
    # def tool_q_search_013_high_connection_music_lookup(conn: Neo4j_Connection, limit: int = 20) -> list[dict]:
    #     """관계 수가 많은 곡(그래프 허브에 가까운 트랙)을 조회한다.

    #     예상 질문:
    #     - 가장 많이 연결된 음악 보여줘
    #     - 그래프에서 중심에 가까운 노래가 뭐야?
    #     - 연결 정보가 많은 곡 알려줘
    #     - 추천 근거가 많은 음악 찾아줘
    #     - 노드 연결이 많은 음악 순위 보여줘
    #     """
    #     return KagQueryTools.execute(KagQueryTemplateConstants.Q_SEARCH_013, {"limit": limit}, conn)

    # @staticmethod
    # def tool_q_search_014_relation_type_lookup(conn: Neo4j_Connection, keyword: str, limit: int = 20) -> list[dict]:
    #     """기준 곡에 연결된 관계 타입 목록을 조회한다.

    #     예상 질문:
    #     - Ditto는 어떤 관계들이 있어?
    #     - 이 노래랑 연결된 엣지 타입 보여줘
    #     - Hype Boy의 관계 종류 알려줘
    #     - 이 곡은 어떤 정보랑 연결될 수 있어?
    #     - Attention의 연결 타입 목록 보여줘
    #     """
    #     return KagQueryTools.execute(KagQueryTemplateConstants.Q_SEARCH_014, {"keyword": keyword, "limit": limit}, conn)

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
        """감정(emotion) 시나리오 라벨(`LabelEmotion.name`)을 기준으로 추천한다.

        용도:
        - 감정/분위기 중심 추천 요청을 처리한다. 차분함, 신남 등 정성적 무드 질의에 대응한다.
        - `music_catalog_scenarios.csv`의 `emotion` 열이 연결한 태그와 매칭한다.
        - 파라미터는 그래프 영문 토큰(예: calm, hyped)이거나 ``resolve_scenario_param("emotion", "잔잔함")`` 등으로 한글 별칭을 치환한 값을 넘긴다.

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
        """상황·활동·시간·계절 시나리오 라벨을 기준으로 추천한다.

        용도:
        - 운동, 출근, 집중, 여행, 밤·계절 등 사용 맥락 기반 추천을 처리한다. 상황 태그와 매핑된 곡을 우선 노출한다.
        - exercise/home/commute/focus/special 및 time·season 등 `HAS_LABEL_*`로 연결된 값 노드 `name`과 CONTAINS 매칭한다.
        - 한글 발화는 ``resolve_scenario_param``으로 영문 토큰 치환(예: exercise 카테고리에서 운동→gym, time에서 밤→night, season에서 겨울→winter).

        예상 질문:
        - "운동할 때 들을 노래 추천"
        - "집중할 때 좋은 음악 찾아줘"
        - "밤에 듣기 좋은 음악 찾아줘"
        - "겨울에 어울리는 곡 추천해줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_REC_003, {"situation": situation, "limit": limit}, conn)

    @staticmethod
    def tool_q_rec_004_weather_based_recommendation(conn: Neo4j_Connection, weather: str, limit: int = 10) -> list[dict]:
        """날씨(`LabelWeather.name`)를 기준으로 추천한다.

        용도:
        - 맑음/비/눈 등 날씨 기반 감성 추천 요청을 처리한다. 일상 컨텍스트 질의에서 빠른 후보군 생성에 쓴다.
        - 그래프 영문 토큰(`sunny`, `rain` 등)으로 매칭한다. 한글(맑음, 비)은 ``resolve_scenario_param("weather", "...")`` 로 치환해 전달한다.

        예상 질문:
        - "비 오는 날 듣기 좋은 노래 추천"
        - "화창한 날씨에 어울리는 곡 찾아줘"
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_REC_004, {"weather": weather, "limit": limit}, conn)

    @staticmethod
    def tool_q_rec_005_similar_song_recommendation(conn: Neo4j_Connection, keyword: str, limit: int = 10) -> list[dict]:
        """공유 특성 수를 점수화한 유사 곡 추천을 수행한다.

        예상 질문:
        - Ditto 같은 노래 추천해줘
        - Hype Boy랑 비슷한 노래 추천해줘
        - 이 곡이 마음에 드는데 비슷한 곡 있어?
        - Shape of You 느낌으로 추천해줘
        - Attention 비슷한 음악 들려줘
        """
        return KagQueryTools.execute(KagQueryTemplateConstants.Q_REC_005, {"keyword": keyword, "limit": limit}, conn)

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
        - "OO 아티스트의의 대중적인 곡 찾아줘"
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
    def tool_q_rec_007_diversity_recommendation(
        conn: Neo4j_Connection,
        genre: str | None = None,
        mood: str | None = None,
        situation: str | None = None,
        weather: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """아티스트당 대표곡 1곡씩 모아 다양성 있는 추천 목록을 만든다.

        예상 질문:
        - Pop장르에 해당하는 노래 다양하게 추천해줘
        - 아티스트 안 겹치게 추천해줘
        - 비슷한 노래 말고 다양하게 보여줘
        - 장르 안에서 다양하게 골라줘
        """
        return KagQueryTools.execute(
            KagQueryTemplateConstants.Q_REC_007,
            {
                "genre": genre,
                "mood": mood,
                "situation": situation,
                "weather": weather,
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
        """장르·LabelEmotion·상황(time/season 포함)·LabelWeather를 함께 고려한 하이브리드 추천.

        용도:
        - 복합 조건이 들어온 고난도 추천 질의를 처리한다.
        - 다중 컨텍스트 매칭 수와 인기도를 함께 점수화해 정렬한다.
        - 파라미터는 그래프 영문 태그이거나 ``resolve_scenario_param``으로 한글 별칭을 치환한 값을 넘긴다.

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
    # 스모크: 일부 파라미터는 resolve_scenario_param 으로 한글→영문 저장 토큰 치환 후 실행한다.
    # (Neo4j 적재 및 시나리오 라벨이 있어야 결과 행이 나올 수 있다.)
    conn = Neo4j_Connection()

    smoke_cases = [
        (
            "Q_SEARCH_001",
            lambda: KagQueryTools.tool_q_search_001_music_basic_info_lookup(conn, keyword="love", limit=3),
        ),
        (
            "Q_SEARCH_002",
            lambda: KagQueryTools.tool_q_search_002_music_relation_info_lookup(conn, keyword="love", limit=3),
        ),
        (
            "Q_SEARCH_003",
            lambda: KagQueryTools.tool_q_search_003_music_condition_search(conn, genre="hip hop", limit=3),
        ),
        (
            "Q_SEARCH_004",
            lambda: KagQueryTools.tool_q_search_004_similar_music_lookup(conn, keyword="love", limit=3),
        ),
        (
            "Q_SEARCH_005",
            lambda: KagQueryTools.tool_q_search_005_music_stat_lookup(conn, stat_type="genre", limit=5),
        ),
        (
            "Q_SEARCH_006",
            lambda: KagQueryTools.tool_q_search_006_connected_node_music_lookup(
                conn,
                node_value=resolve_scenario_param("weather", "비"),
                limit=3,
            ),
        ),
        (
            "Q_SEARCH_007",
            lambda: KagQueryTools.tool_q_search_007_music_common_feature_lookup(conn, music1="love", music2="you", limit=3),
        ),
        # (
        #     "Q_SEARCH_008",
        #     lambda: KagQueryTools.tool_q_search_008_music_path_lookup(conn, keyword="love", max_depth=2, limit=3),
        # ),
        (
            "Q_SEARCH_009",
            lambda: KagQueryTools.tool_q_search_009_artist_music_lookup(conn, artist="Taylor", limit=3),
        ),
        (
            "Q_SEARCH_010",
            lambda: KagQueryTools.tool_q_search_010_category_top_music_lookup(conn, category_type="genre", category_value="pop", limit=3),
        ),
        # (
        #     "Q_SEARCH_011",
        #     lambda: KagQueryTools.tool_q_search_011_temporal_music_lookup(conn, year=2020, limit=3),
        # ),
        (
            "Q_SEARCH_012",
            lambda: KagQueryTools.tool_q_search_012_composite_condition_search(
                conn,
                genre="pop",
                mood=resolve_scenario_param("emotion", "잔잔함"),
                weather=resolve_scenario_param("weather", "비"),
                limit=3,
            ),
        ),
        # (
        #     "Q_SEARCH_013",
        #     lambda: KagQueryTools.tool_q_search_013_high_connection_music_lookup(conn, limit=3),
        # ),
        # (
        #     "Q_SEARCH_014",
        #     lambda: KagQueryTools.tool_q_search_014_relation_type_lookup(conn, keyword="love", limit=10),
        # ),
        (
            "Q_REC_001",
            lambda: KagQueryTools.tool_q_rec_001_genre_based_recommendation(conn, genre="rock", limit=3),
        ),
        (
            "Q_REC_002",
            lambda: KagQueryTools.tool_q_rec_002_mood_based_recommendation(
                conn,
                mood=resolve_scenario_param("emotion", "잔잔함"),
                limit=3,
            ),
        ),
        (
            "Q_REC_003",
            lambda: KagQueryTools.tool_q_rec_003_situation_based_recommendation(
                conn,
                situation=resolve_scenario_param("exercise", "운동"),
                limit=3,
            ),
        ),
        (
            "Q_REC_003_season_ko",
            lambda: KagQueryTools.tool_q_rec_003_situation_based_recommendation(
                conn,
                situation=resolve_scenario_param("season", "겨울"),
                limit=3,
            ),
        ),
        (
            "Q_REC_004",
            lambda: KagQueryTools.tool_q_rec_004_weather_based_recommendation(
                conn,
                weather=resolve_scenario_param("weather", "맑음"),
                limit=3,
            ),
        ),
        (
            "Q_REC_005",
            lambda: KagQueryTools.tool_q_rec_005_similar_song_recommendation(conn, keyword="love", limit=3),
        ),
        (
            "Q_REC_006",
            lambda: KagQueryTools.tool_q_rec_006_popularity_based_recommendation(conn, genre="pop", limit=3),
        ),
        (
            "Q_REC_007",
            lambda: KagQueryTools.tool_q_rec_007_diversity_recommendation(conn, genre="pop", limit=3),
        ),
        (
            "Q_REC_008",
            lambda: KagQueryTools.tool_q_rec_008_hybrid_context_recommendation(
                conn,
                genre="pop",
                mood=resolve_scenario_param("emotion", "잔잔함"),
                weather=resolve_scenario_param("weather", "맑음"),
                limit=3,
            ),
        ),
    ]

    logger.info("KAG Query Tool smoke 시작")
    for label, runner in smoke_cases:
        try:
            rows = runner()
            logger.info("[SMOKE PASS] %s rows=%s", label, len(rows))
            logger.info(rows)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[SMOKE FAIL] %s (%s: %s)", label, type(exc).__name__, exc)
    logger.info("KAG Query Tool smoke 완료")
