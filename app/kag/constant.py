"""KAG Query 템플릿·그래프 스키마 상수.

`neo4j/common/constant.py`와 도메인은 같으나 앱 패키지(`app`)는 독립적으로 유지한다.
노드 라벨·관계 타입·그래프 프로퍼티·쿼리 결과 컬럼명은 여기서만 정의하고 Cypher에는 하드코딩하지 않는다.
"""

from enum import Enum
from typing import ClassVar


###########################################################
# node 타입
###########################################################
class KagNodeLabel(str, Enum):
    """Neo4j 노드 라벨 (스키마와 동일하게 유지)."""

    MUSIC_CATALOG = "MusicCatalog"
    GENRE = "Genre"
    SUBGENRE = "SubGenre"
    ARTIST = "Artist"
    MOOD = "Mood"
    TEMPO = "Tempo"
    RELEASE_YEAR = "ReleaseYear"
    DIM_WEATHER = "DimWeather"
    DIM_SEASON = "DimSeason"
    DIM_EMOTION = "DimEmotion"
    DIM_TIME_OF_DAY = "DimTimeOfDay"
    DIM_ENERGY_LEVEL = "DimEnergyLevel"
    DIM_CTX_COMMUTE = "DimCtxCommute"
    DIM_CTX_HOME = "DimCtxHome"
    DIM_CTX_FOCUS = "DimCtxFocus"
    DIM_CTX_EXERCISE = "DimCtxExercise"
    DIM_CTX_SOCIAL = "DimCtxSocial"
    DIM_CTX_EMOTION_SIT = "DimCtxEmotionSit"
    DIM_CTX_TRAVEL = "DimCtxTravel"
    DIM_CTX_SPECIAL = "DimCtxSpecial"


###########################################################
# relationship 타입
###########################################################
class KagRelationType(str, Enum):
    """Neo4j 관계 타입 (스키마와 동일하게 유지)."""

    HAS_GENRE = "HAS_GENRE"
    HAS_SUBGENRE = "HAS_SUBGENRE"
    PERFORMED_BY = "PERFORMED_BY"
    HAS_MOOD = "HAS_MOOD"
    HAS_TEMPO = "HAS_TEMPO"
    RELEASED_IN = "RELEASED_IN"
    HAS_DIM_WEATHER = "HAS_DIM_WEATHER"
    HAS_DIM_SEASON = "HAS_DIM_SEASON"
    HAS_DIM_EMOTION = "HAS_DIM_EMOTION"
    HAS_DIM_TIME_OF_DAY = "HAS_DIM_TIME_OF_DAY"
    HAS_DIM_ENERGY_LEVEL = "HAS_DIM_ENERGY_LEVEL"
    HAS_DIM_CTX_COMMUTE = "HAS_DIM_CTX_COMMUTE"
    HAS_DIM_CTX_HOME = "HAS_DIM_CTX_HOME"
    HAS_DIM_CTX_FOCUS = "HAS_DIM_CTX_FOCUS"
    HAS_DIM_CTX_EXERCISE = "HAS_DIM_CTX_EXERCISE"
    HAS_DIM_CTX_SOCIAL = "HAS_DIM_CTX_SOCIAL"
    HAS_DIM_CTX_EMOTION_SIT = "HAS_DIM_CTX_EMOTION_SIT"
    HAS_DIM_CTX_TRAVEL = "HAS_DIM_CTX_TRAVEL"
    HAS_DIM_CTX_SPECIAL = "HAS_DIM_CTX_SPECIAL"


def _cypher_rel_type_union(relations: tuple[KagRelationType, ...]) -> str:
    return "|".join(r.value for r in relations)


# Q_REC_003 · 상황 매칭에 쓰는 컨텍스트 관계 묶음
KAG_QUERY_SITUATION_CONTEXT_REL_TYPES: tuple[KagRelationType, ...] = (
    KagRelationType.HAS_DIM_CTX_EXERCISE,
    KagRelationType.HAS_DIM_CTX_COMMUTE,
    KagRelationType.HAS_DIM_CTX_HOME,
    KagRelationType.HAS_DIM_CTX_SOCIAL,
    KagRelationType.HAS_DIM_CTX_FOCUS,
    KagRelationType.HAS_DIM_CTX_TRAVEL,
    KagRelationType.HAS_DIM_CTX_SPECIAL,
)

KAG_CYPHER_SITUATION_REL_PATTERN: str = _cypher_rel_type_union(KAG_QUERY_SITUATION_CONTEXT_REL_TYPES)

# Q_REC_008 하이브리드 — 감정 상황 차원 포함
KAG_QUERY_HYBRID_SITUATION_REL_TYPES: tuple[KagRelationType, ...] = (
    *KAG_QUERY_SITUATION_CONTEXT_REL_TYPES,
    KagRelationType.HAS_DIM_CTX_EMOTION_SIT,
)

KAG_CYPHER_HYBRID_SITUATION_REL_PATTERN: str = _cypher_rel_type_union(KAG_QUERY_HYBRID_SITUATION_REL_TYPES)


###########################################################
# 노드 프로퍼티 (쿼리에 등장하는 필드)
###########################################################
class KagMusicCatalogProperty(str, Enum):
    """MusicCatalog 노드 프로퍼티 키."""

    TRACK_ID = "track_id"
    TRACK_NAME = "track_name"
    TRACK_ARTIST = "track_artist"
    TRACK_ALBUM_NAME = "track_album_name"
    TRACK_ALBUM_RELEASE_DATE = "track_album_release_date"
    PLAYLIST_GENRE = "playlist_genre"
    PLAYLIST_SUBGENRE = "playlist_subgenre"
    DURATION_MS = "duration_ms"
    TRACK_POPULARITY = "track_popularity"


class KagMoodProperty(str, Enum):
    """Mood 노드 프로퍼티 키."""

    MOOD = "mood"


class KagGenreProperty(str, Enum):
    """Genre 노드 프로퍼티 키."""

    GENRE = "genre"


class KagDimTagProperty(str, Enum):
    """DimWeather 등 이름 기반 차원 노드의 표시 필드."""

    NAME = "name"


###########################################################
# Cypher WITH 등 중간 식별자
###########################################################
class KagCypherBinding(str, Enum):
    """WITH 절 등에서 쓰는 중간 바인딩 이름."""

    RELEASE_YEAR = "release_year"


###########################################################
# RETURN 컬럼(별칭)
###########################################################
class KagQueryResultColumn(str, Enum):
    """RETURN 절 `AS` 에 사용하는 출력 컬럼명."""

    TRACK_ID = "track_id"
    TRACK_NAME = "track_name"
    TRACK_ARTIST = "track_artist"
    ALBUM_NAME = "album_name"
    RELEASE_DATE = "release_date"
    GENRE = "genre"
    SUBGENRE = "subgenre"
    DURATION_MS = "duration_ms"
    POPULARITY = "popularity"
    MATCHED_MOOD = "matched_mood"
    MATCHED_SITUATION = "matched_situation"
    MATCHED_WEATHER = "matched_weather"
    RECOMMENDATION_SCORE = "recommendation_score"
    MATCHED_COUNT = "matched_count"
    RELATION_TYPE = "relation_type"
    CONNECTED_NODE_LABELS = "connected_node_labels"
    CONNECTED_NODE_PROPERTIES = "connected_node_properties"
    SHARED_FEATURE_COUNT = "shared_feature_count"
    GROUP_KEY = "group_key"
    MUSIC_COUNT = "music_count"
    MATCHED_NODE_LABELS = "matched_node_labels"
    MATCHED_NODE_PROPERTIES = "matched_node_properties"
    COMMON_NODE_LABELS = "common_node_labels"
    COMMON_NODE_PROPERTIES = "common_node_properties"
    PATH_LENGTH = "path_length"
    PATH_NODES = "path_nodes"
    PATH_REL_TYPES = "path_rel_types"
    RELATION_COUNT = "relation_count"
    MATCHED_FEATURE_COUNT = "matched_feature_count"


###########################################################
# 템플릿 조립 (클래스 속성에서 참조 가능한 모듈 레벨 빌더)
###########################################################
def _build_cypher_templates() -> dict[str, str]:
    """Cypher 문자열은 f-string으로 조립한다. Python 3.12+ 에서 Enum 기본 서식이 값이 아닐 수 있어 `.value` 를 강제한다."""

    def _ev(m: Enum) -> str:
        return m.value

    nl = KagNodeLabel
    rt = KagRelationType
    mc = KagMusicCatalogProperty
    mm = KagMoodProperty
    rg = KagGenreProperty
    dt = KagDimTagProperty
    cb = KagCypherBinding
    rc = KagQueryResultColumn
    sit = KAG_CYPHER_SITUATION_REL_PATTERN
    hysit = KAG_CYPHER_HYBRID_SITUATION_REL_PATTERN

    q_search_001 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WHERE toLower(m.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($keyword)
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  m.{_ev(mc.TRACK_ALBUM_NAME)} AS {_ev(rc.ALBUM_NAME)},
  m.{_ev(mc.TRACK_ALBUM_RELEASE_DATE)} AS {_ev(rc.RELEASE_DATE)},
  m.{_ev(mc.PLAYLIST_GENRE)} AS {_ev(rc.GENRE)},
  m.{_ev(mc.PLAYLIST_SUBGENRE)} AS {_ev(rc.SUBGENRE)},
  m.{_ev(mc.DURATION_MS)} AS {_ev(rc.DURATION_MS)},
  m.{_ev(mc.TRACK_POPULARITY)} AS {_ev(rc.POPULARITY)}
ORDER BY coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) DESC
LIMIT $limit
"""

    q_search_003 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WHERE
  ($genre IS NULL OR toLower(m.{_ev(mc.PLAYLIST_GENRE)}) = toLower($genre))
  AND ($subgenre IS NULL OR toLower(m.{_ev(mc.PLAYLIST_SUBGENRE)}) = toLower($subgenre))
  AND ($artist IS NULL OR toLower(m.{_ev(mc.TRACK_ARTIST)}) CONTAINS toLower($artist))
  AND ($release_year IS NULL OR toString(m.{_ev(mc.TRACK_ALBUM_RELEASE_DATE)}) STARTS WITH toString($release_year))
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  m.{_ev(mc.TRACK_ALBUM_NAME)} AS {_ev(rc.ALBUM_NAME)},
  m.{_ev(mc.TRACK_ALBUM_RELEASE_DATE)} AS {_ev(rc.RELEASE_DATE)},
  m.{_ev(mc.PLAYLIST_GENRE)} AS {_ev(rc.GENRE)},
  m.{_ev(mc.PLAYLIST_SUBGENRE)} AS {_ev(rc.SUBGENRE)},
  m.{_ev(mc.TRACK_POPULARITY)} AS {_ev(rc.POPULARITY)}
ORDER BY coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) DESC
LIMIT $limit
"""

    q_search_009 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WHERE toLower(m.{_ev(mc.TRACK_ARTIST)}) CONTAINS toLower($artist)
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  m.{_ev(mc.TRACK_ALBUM_NAME)} AS {_ev(rc.ALBUM_NAME)},
  m.{_ev(mc.TRACK_POPULARITY)} AS {_ev(rc.POPULARITY)}
ORDER BY coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) DESC
LIMIT $limit
"""

    q_search_011 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WITH m, toInteger(left(toString(m.{_ev(mc.TRACK_ALBUM_RELEASE_DATE)}), 4)) AS {_ev(cb.RELEASE_YEAR)}
WHERE
  ($year IS NOT NULL AND {_ev(cb.RELEASE_YEAR)} = $year)
  OR ($year IS NULL AND $start_year IS NOT NULL AND $end_year IS NOT NULL
      AND {_ev(cb.RELEASE_YEAR)} >= $start_year AND {_ev(cb.RELEASE_YEAR)} <= $end_year)
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  m.{_ev(mc.TRACK_ALBUM_RELEASE_DATE)} AS {_ev(rc.RELEASE_DATE)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)}
ORDER BY {_ev(rc.POPULARITY)} DESC
LIMIT $limit
"""

    q_rec_001 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WHERE toLower(m.{_ev(mc.PLAYLIST_GENRE)}) = toLower($genre)
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  m.{_ev(mc.PLAYLIST_GENRE)} AS {_ev(rc.GENRE)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    q_rec_002 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})-[:{_ev(rt.HAS_MOOD)}]-(mood:{_ev(nl.MOOD)})
WHERE toLower(mood.{_ev(mm.MOOD)}) CONTAINS toLower($mood)
RETURN DISTINCT
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  mood.{_ev(mm.MOOD)} AS {_ev(rc.MATCHED_MOOD)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  10 + coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    q_rec_003 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})-[:{sit}]-(s)
WHERE toLower(s.{_ev(dt.NAME)}) CONTAINS toLower($situation)
RETURN DISTINCT
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  s.{_ev(dt.NAME)} AS {_ev(rc.MATCHED_SITUATION)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  10 + coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    q_rec_004 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})-[:{_ev(rt.HAS_DIM_WEATHER)}]-(w:{_ev(nl.DIM_WEATHER)})
WHERE toLower(w.{_ev(dt.NAME)}) CONTAINS toLower($weather)
RETURN DISTINCT
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  w.{_ev(dt.NAME)} AS {_ev(rc.MATCHED_WEATHER)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  10 + coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    q_rec_006 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WHERE
  ($genre IS NULL OR toLower(m.{_ev(mc.PLAYLIST_GENRE)}) = toLower($genre))
  AND ($subgenre IS NULL OR toLower(m.{_ev(mc.PLAYLIST_SUBGENRE)}) = toLower($subgenre))
  AND ($artist IS NULL OR toLower(m.{_ev(mc.TRACK_ARTIST)}) CONTAINS toLower($artist))
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  m.{_ev(mc.PLAYLIST_GENRE)} AS {_ev(rc.GENRE)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    q_rec_008 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_GENRE)}]-(g:{_ev(nl.GENRE)})
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_MOOD)}]-(mood:{_ev(nl.MOOD)})
OPTIONAL MATCH (m)-[:{hysit}]-(s)
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_DIM_WEATHER)}]-(w:{_ev(nl.DIM_WEATHER)})
WITH m,
  max(CASE WHEN $genre IS NOT NULL AND toLower(g.{_ev(rg.GENRE)}) = toLower($genre) THEN 1 ELSE 0 END) AS genre_match,
  max(CASE WHEN $mood IS NOT NULL AND toLower(mood.{_ev(mm.MOOD)}) = toLower($mood) THEN 1 ELSE 0 END) AS mood_match,
  max(CASE WHEN $situation IS NOT NULL AND toLower(s.{_ev(dt.NAME)}) CONTAINS toLower($situation) THEN 1 ELSE 0 END) AS situation_match,
  max(CASE WHEN $weather IS NOT NULL AND toLower(w.{_ev(dt.NAME)}) CONTAINS toLower($weather) THEN 1 ELSE 0 END) AS weather_match
WITH m, genre_match + mood_match + situation_match + weather_match AS {_ev(rc.MATCHED_COUNT)}
WHERE {_ev(rc.MATCHED_COUNT)} > 0
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  {_ev(rc.MATCHED_COUNT)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  {_ev(rc.MATCHED_COUNT)} * 10 + coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    q_search_002 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})-[r]-(n)
WHERE toLower(m.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($keyword)
  AND ($relation_filter IS NULL OR type(r) = $relation_filter)
  AND ($node_label_filter IS NULL OR $node_label_filter IN labels(n))
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  type(r) AS {_ev(rc.RELATION_TYPE)},
  labels(n) AS {_ev(rc.CONNECTED_NODE_LABELS)},
  properties(n) AS {_ev(rc.CONNECTED_NODE_PROPERTIES)}
LIMIT $limit
"""

    q_search_004 = f"""
MATCH (base:{_ev(nl.MUSIC_CATALOG)})-[]-(feature)<-[]-(other:{_ev(nl.MUSIC_CATALOG)})
WHERE NOT feature:{_ev(nl.MUSIC_CATALOG)}
  AND toLower(base.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($keyword)
  AND base.{_ev(mc.TRACK_ID)} <> other.{_ev(mc.TRACK_ID)}
WITH other, count(DISTINCT feature) AS {_ev(rc.SHARED_FEATURE_COUNT)}
RETURN
  other.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  other.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  other.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  {_ev(rc.SHARED_FEATURE_COUNT)},
  coalesce(other.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)}
ORDER BY {_ev(rc.SHARED_FEATURE_COUNT)} DESC, {_ev(rc.POPULARITY)} DESC
LIMIT $limit
"""

    q_search_005 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WITH m,
  CASE toLower(toString($stat_type))
    WHEN 'genre' THEN toString(m.{_ev(mc.PLAYLIST_GENRE)})
    WHEN 'artist' THEN toString(m.{_ev(mc.TRACK_ARTIST)})
    WHEN 'year' THEN left(toString(m.{_ev(mc.TRACK_ALBUM_RELEASE_DATE)}), 4)
    ELSE null
  END AS {_ev(rc.GROUP_KEY)}
WHERE {_ev(rc.GROUP_KEY)} IS NOT NULL AND trim({_ev(rc.GROUP_KEY)}) <> ''
RETURN {_ev(rc.GROUP_KEY)}, count(*) AS {_ev(rc.MUSIC_COUNT)}
ORDER BY {_ev(rc.MUSIC_COUNT)} DESC
LIMIT $limit
"""

    q_search_006 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})-[r]-(n)
WHERE
  ($node_label_filter IS NULL OR $node_label_filter IN labels(n))
  AND ($relation_filter IS NULL OR type(r) = $relation_filter)
  AND any(k IN keys(n) WHERE toLower(toString(n[k])) CONTAINS toLower($node_value))
RETURN DISTINCT
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  labels(n) AS {_ev(rc.MATCHED_NODE_LABELS)},
  properties(n) AS {_ev(rc.MATCHED_NODE_PROPERTIES)}
LIMIT $limit
"""

    q_search_007 = f"""
MATCH (m1:{_ev(nl.MUSIC_CATALOG)})-[]-(n)-[]-(m2:{_ev(nl.MUSIC_CATALOG)})
WHERE NOT n:{_ev(nl.MUSIC_CATALOG)}
  AND toLower(m1.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($music1)
  AND toLower(m2.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($music2)
  AND m1.{_ev(mc.TRACK_ID)} <> m2.{_ev(mc.TRACK_ID)}
RETURN DISTINCT
  labels(n) AS {_ev(rc.COMMON_NODE_LABELS)},
  properties(n) AS {_ev(rc.COMMON_NODE_PROPERTIES)}
LIMIT $limit
"""

    q_search_008 = f"""
MATCH p=(m:{_ev(nl.MUSIC_CATALOG)})-[*1..$max_depth]-(n)
WHERE toLower(m.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($keyword)
  AND ($target_label IS NULL OR $target_label IN labels(n))
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  length(p) AS {_ev(rc.PATH_LENGTH)},
  [node IN nodes(p) | {{labels: labels(node), props: properties(node)}}] AS {_ev(rc.PATH_NODES)},
  [rel IN relationships(p) | type(rel)] AS {_ev(rc.PATH_REL_TYPES)}
ORDER BY {_ev(rc.PATH_LENGTH)} ASC
LIMIT $limit
"""

    q_search_010 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WHERE
  ($category_type = 'genre' AND toLower(m.{_ev(mc.PLAYLIST_GENRE)}) = toLower($category_value))
  OR ($category_type = 'subgenre' AND toLower(m.{_ev(mc.PLAYLIST_SUBGENRE)}) = toLower($category_value))
  OR ($category_type = 'artist' AND toLower(m.{_ev(mc.TRACK_ARTIST)}) CONTAINS toLower($category_value))
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)}
ORDER BY {_ev(rc.POPULARITY)} DESC
LIMIT $limit
"""

    q_search_012 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_GENRE)}]-(g:{_ev(nl.GENRE)})
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_MOOD)}]-(mood:{_ev(nl.MOOD)})
OPTIONAL MATCH (m)-[:{hysit}]-(s)
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_DIM_WEATHER)}]-(w:{_ev(nl.DIM_WEATHER)})
WITH m,
  max(CASE WHEN $genre IS NOT NULL AND toLower(g.{_ev(rg.GENRE)}) = toLower($genre) THEN 1 ELSE 0 END) AS genre_match,
  max(CASE WHEN $mood IS NOT NULL AND toLower(mood.{_ev(mm.MOOD)}) = toLower($mood) THEN 1 ELSE 0 END) AS mood_match,
  max(CASE WHEN $situation IS NOT NULL AND toLower(s.{_ev(dt.NAME)}) CONTAINS toLower($situation) THEN 1 ELSE 0 END) AS situation_match,
  max(CASE WHEN $weather IS NOT NULL AND toLower(w.{_ev(dt.NAME)}) CONTAINS toLower($weather) THEN 1 ELSE 0 END) AS weather_match
WITH m, genre_match + mood_match + situation_match + weather_match AS {_ev(rc.MATCHED_COUNT)}
WHERE {_ev(rc.MATCHED_COUNT)} > 0
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  {_ev(rc.MATCHED_COUNT)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)}
ORDER BY {_ev(rc.MATCHED_COUNT)} DESC, {_ev(rc.POPULARITY)} DESC
LIMIT $limit
"""

    q_search_013 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})-[r]-()
RETURN
  m.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  m.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  m.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  count(r) AS {_ev(rc.RELATION_COUNT)},
  coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)}
ORDER BY {_ev(rc.RELATION_COUNT)} DESC, {_ev(rc.POPULARITY)} DESC
LIMIT $limit
"""

    q_search_014 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})-[r]-()
WHERE toLower(m.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($keyword)
RETURN DISTINCT type(r) AS {_ev(rc.RELATION_TYPE)}
LIMIT $limit
"""

    q_rec_005 = f"""
MATCH (base:{_ev(nl.MUSIC_CATALOG)})-[]-(feature)<-[]-(rec:{_ev(nl.MUSIC_CATALOG)})
WHERE NOT feature:{_ev(nl.MUSIC_CATALOG)}
  AND toLower(base.{_ev(mc.TRACK_NAME)}) CONTAINS toLower($keyword)
  AND base.{_ev(mc.TRACK_ID)} <> rec.{_ev(mc.TRACK_ID)}
WITH rec, count(DISTINCT feature) AS {_ev(rc.MATCHED_FEATURE_COUNT)}
RETURN
  rec.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  rec.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  rec.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  {_ev(rc.MATCHED_FEATURE_COUNT)},
  coalesce(rec.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  {_ev(rc.MATCHED_FEATURE_COUNT)} * 10 + coalesce(rec.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    q_rec_007 = f"""
MATCH (m:{_ev(nl.MUSIC_CATALOG)})
WHERE ($genre IS NULL OR toLower(m.{_ev(mc.PLAYLIST_GENRE)}) = toLower($genre))
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_MOOD)}]-(mood:{_ev(nl.MOOD)})
OPTIONAL MATCH (m)-[:{hysit}]-(s)
OPTIONAL MATCH (m)-[:{_ev(rt.HAS_DIM_WEATHER)}]-(w:{_ev(nl.DIM_WEATHER)})
WITH m,
  max(CASE WHEN $mood IS NOT NULL AND toLower(mood.{_ev(mm.MOOD)}) CONTAINS toLower($mood) THEN 1 ELSE 0 END) AS mood_match,
  max(CASE WHEN $situation IS NOT NULL AND toLower(s.{_ev(dt.NAME)}) CONTAINS toLower($situation) THEN 1 ELSE 0 END) AS situation_match,
  max(CASE WHEN $weather IS NOT NULL AND toLower(w.{_ev(dt.NAME)}) CONTAINS toLower($weather) THEN 1 ELSE 0 END) AS weather_match
WITH m, mood_match + situation_match + weather_match AS ctx_match
WHERE ($mood IS NULL AND $situation IS NULL AND $weather IS NULL) OR ctx_match > 0
WITH m
ORDER BY coalesce(m.{_ev(mc.TRACK_POPULARITY)}, 0) DESC
WITH m.{_ev(mc.TRACK_ARTIST)} AS artist_key, collect(m)[0] AS top_music
RETURN
  top_music.{_ev(mc.TRACK_ID)} AS {_ev(rc.TRACK_ID)},
  top_music.{_ev(mc.TRACK_NAME)} AS {_ev(rc.TRACK_NAME)},
  top_music.{_ev(mc.TRACK_ARTIST)} AS {_ev(rc.TRACK_ARTIST)},
  top_music.{_ev(mc.PLAYLIST_GENRE)} AS {_ev(rc.GENRE)},
  coalesce(top_music.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.POPULARITY)},
  coalesce(top_music.{_ev(mc.TRACK_POPULARITY)}, 0) AS {_ev(rc.RECOMMENDATION_SCORE)}
ORDER BY {_ev(rc.RECOMMENDATION_SCORE)} DESC
LIMIT $limit
"""

    keys = KagQueryTemplateConstants
    return {
        keys.Q_SEARCH_001: q_search_001,
        keys.Q_SEARCH_002: q_search_002,
        keys.Q_SEARCH_003: q_search_003,
        keys.Q_SEARCH_004: q_search_004,
        keys.Q_SEARCH_005: q_search_005,
        keys.Q_SEARCH_006: q_search_006,
        keys.Q_SEARCH_007: q_search_007,
        keys.Q_SEARCH_008: q_search_008,
        keys.Q_SEARCH_009: q_search_009,
        keys.Q_SEARCH_010: q_search_010,
        keys.Q_SEARCH_011: q_search_011,
        keys.Q_SEARCH_012: q_search_012,
        keys.Q_SEARCH_013: q_search_013,
        keys.Q_SEARCH_014: q_search_014,
        keys.Q_REC_001: q_rec_001,
        keys.Q_REC_002: q_rec_002,
        keys.Q_REC_003: q_rec_003,
        keys.Q_REC_004: q_rec_004,
        keys.Q_REC_005: q_rec_005,
        keys.Q_REC_006: q_rec_006,
        keys.Q_REC_007: q_rec_007,
        keys.Q_REC_008: q_rec_008,
    }


class KagQueryTemplateConstants:
    """KAG Query 템플릿/파라미터 템플릿 상수.

    외부 Agent가 호출하는 Tool 함수는 이 레지스트리의 query_key를 기준으로
    Cypher 템플릿과 파라미터 기본값/허용범위를 조회해 실행한다.
    """

    Q_SEARCH_001 = "Q_SEARCH_001"
    Q_SEARCH_002 = "Q_SEARCH_002"
    Q_SEARCH_003 = "Q_SEARCH_003"
    Q_SEARCH_004 = "Q_SEARCH_004"
    Q_SEARCH_005 = "Q_SEARCH_005"
    Q_SEARCH_006 = "Q_SEARCH_006"
    Q_SEARCH_007 = "Q_SEARCH_007"
    Q_SEARCH_008 = "Q_SEARCH_008"
    Q_SEARCH_009 = "Q_SEARCH_009"
    Q_SEARCH_010 = "Q_SEARCH_010"
    Q_SEARCH_011 = "Q_SEARCH_011"
    Q_SEARCH_012 = "Q_SEARCH_012"
    Q_SEARCH_013 = "Q_SEARCH_013"
    Q_SEARCH_014 = "Q_SEARCH_014"
    Q_REC_001 = "Q_REC_001"
    Q_REC_002 = "Q_REC_002"
    Q_REC_003 = "Q_REC_003"
    Q_REC_004 = "Q_REC_004"
    Q_REC_005 = "Q_REC_005"
    Q_REC_006 = "Q_REC_006"
    Q_REC_007 = "Q_REC_007"
    Q_REC_008 = "Q_REC_008"

    CYPHER_TEMPLATES: ClassVar[dict[str, str]] = {}  # filled below
    PARAMETER_TEMPLATES: ClassVar[dict[str, dict]] = {
        Q_SEARCH_001: {
            "required": ["keyword"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_SEARCH_002: {
            "required": ["keyword"],
            "defaults": {"relation_filter": None, "node_label_filter": None, "limit": 50},
            "optional_nullable": ["relation_filter", "node_label_filter"],
        },
        Q_SEARCH_003: {
            "required": [],
            "defaults": {"genre": None, "subgenre": None, "artist": None, "release_year": None, "limit": 20},
            "optional_nullable": ["genre", "subgenre", "artist", "release_year"],
        },
        Q_SEARCH_004: {
            "required": ["keyword"],
            "defaults": {"limit": 20},
            "optional_nullable": [],
        },
        Q_SEARCH_005: {
            "required": ["stat_type"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_SEARCH_006: {
            "required": ["node_value"],
            "defaults": {"node_label_filter": None, "relation_filter": None, "limit": 20},
            "optional_nullable": ["node_label_filter", "relation_filter"],
        },
        Q_SEARCH_007: {
            "required": ["music1", "music2"],
            "defaults": {"limit": 20},
            "optional_nullable": [],
        },
        Q_SEARCH_008: {
            "required": ["keyword"],
            "defaults": {"target_label": None, "max_depth": 3, "limit": 10},
            "optional_nullable": ["target_label"],
        },
        Q_SEARCH_009: {
            "required": ["artist"],
            "defaults": {"limit": 30},
            "optional_nullable": [],
        },
        Q_SEARCH_010: {
            "required": ["category_type", "category_value"],
            "defaults": {"limit": 20},
            "optional_nullable": [],
        },
        Q_SEARCH_011: {
            "required": [],
            "defaults": {"year": None, "start_year": None, "end_year": None, "limit": 20},
            "optional_nullable": ["year", "start_year", "end_year"],
        },
        Q_SEARCH_012: {
            "required": [],
            "defaults": {"genre": None, "mood": None, "situation": None, "weather": None, "limit": 20},
            "optional_nullable": ["genre", "mood", "situation", "weather"],
        },
        Q_SEARCH_013: {
            "required": [],
            "defaults": {"limit": 20},
            "optional_nullable": [],
        },
        Q_SEARCH_014: {
            "required": ["keyword"],
            "defaults": {"limit": 20},
            "optional_nullable": [],
        },
        Q_REC_001: {
            "required": ["genre"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_REC_002: {
            "required": ["mood"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_REC_003: {
            "required": ["situation"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_REC_004: {
            "required": ["weather"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_REC_005: {
            "required": ["keyword"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_REC_006: {
            "required": [],
            "defaults": {"genre": None, "subgenre": None, "artist": None, "limit": 10},
            "optional_nullable": ["genre", "subgenre", "artist"],
        },
        Q_REC_007: {
            "required": [],
            "defaults": {"genre": None, "mood": None, "situation": None, "weather": None, "limit": 10},
            "optional_nullable": ["genre", "mood", "situation", "weather"],
        },
        Q_REC_008: {
            "required": [],
            "defaults": {"genre": None, "mood": None, "situation": None, "weather": None, "limit": 10},
            "optional_nullable": ["genre", "mood", "situation", "weather"],
        },
    }

    @classmethod
    def cypher_for(cls, query_key: str) -> str:
        if query_key not in cls.CYPHER_TEMPLATES:
            raise KeyError(f"unknown query_key: {query_key}")
        return cls.CYPHER_TEMPLATES[query_key].strip()

    @classmethod
    def parameter_template_for(cls, query_key: str) -> dict:
        if query_key not in cls.PARAMETER_TEMPLATES:
            raise KeyError(f"unknown parameter template query_key: {query_key}")
        return dict(cls.PARAMETER_TEMPLATES[query_key])


KagQueryTemplateConstants.CYPHER_TEMPLATES = _build_cypher_templates()
