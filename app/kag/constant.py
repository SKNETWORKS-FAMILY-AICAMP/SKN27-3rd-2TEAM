"""KAG Query 템플릿/파라미터 템플릿 상수 모음."""

from typing import ClassVar

class KagQueryTemplateConstants:
    """KAG Query 템플릿/파라미터 템플릿 상수.

    외부 Agent가 호출하는 Tool 함수는 이 레지스트리의 query_key를 기준으로
    Cypher 템플릿과 파라미터 기본값/허용범위를 조회해 실행한다.
    """

    # query_key
    Q_SEARCH_001 = "Q_SEARCH_001"
    Q_SEARCH_003 = "Q_SEARCH_003"
    Q_SEARCH_009 = "Q_SEARCH_009"
    Q_SEARCH_011 = "Q_SEARCH_011"
    Q_REC_001 = "Q_REC_001"
    Q_REC_002 = "Q_REC_002"
    Q_REC_003 = "Q_REC_003"
    Q_REC_004 = "Q_REC_004"
    Q_REC_006 = "Q_REC_006"
    Q_REC_008 = "Q_REC_008"

    CYPHER_TEMPLATES: ClassVar[dict[str, str]] = {
        Q_SEARCH_001: """
MATCH (m:MusicCatalog)
WHERE toLower(m.track_name) CONTAINS toLower($keyword)
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_name AS album_name,
  m.track_album_release_date AS release_date,
  m.playlist_genre AS genre,
  m.playlist_subgenre AS subgenre,
  m.duration_ms AS duration_ms,
  m.track_popularity AS popularity
ORDER BY coalesce(m.track_popularity, 0) DESC
LIMIT $limit
""",
        Q_SEARCH_003: """
MATCH (m:MusicCatalog)
WHERE
  ($genre IS NULL OR toLower(m.playlist_genre) = toLower($genre))
  AND ($subgenre IS NULL OR toLower(m.playlist_subgenre) = toLower($subgenre))
  AND ($artist IS NULL OR toLower(m.track_artist) CONTAINS toLower($artist))
  AND ($release_year IS NULL OR toString(m.track_album_release_date) STARTS WITH toString($release_year))
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_name AS album_name,
  m.track_album_release_date AS release_date,
  m.playlist_genre AS genre,
  m.playlist_subgenre AS subgenre,
  m.track_popularity AS popularity
ORDER BY coalesce(m.track_popularity, 0) DESC
LIMIT $limit
""",
        Q_SEARCH_009: """
MATCH (m:MusicCatalog)
WHERE toLower(m.track_artist) CONTAINS toLower($artist)
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_name AS album_name,
  m.track_popularity AS popularity
ORDER BY coalesce(m.track_popularity, 0) DESC
LIMIT $limit
""",
        Q_SEARCH_011: """
MATCH (m:MusicCatalog)
WITH m, toInteger(left(toString(m.track_album_release_date), 4)) AS release_year
WHERE
  ($year IS NOT NULL AND release_year = $year)
  OR ($year IS NULL AND $start_year IS NOT NULL AND $end_year IS NOT NULL
      AND release_year >= $start_year AND release_year <= $end_year)
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_release_date AS release_date,
  coalesce(m.track_popularity, 0) AS popularity
ORDER BY popularity DESC
LIMIT $limit
""",
        Q_REC_001: """
MATCH (m:MusicCatalog)
WHERE toLower(m.playlist_genre) = toLower($genre)
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.playlist_genre AS genre,
  coalesce(m.track_popularity, 0) AS popularity,
  coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT $limit
""",
        Q_REC_002: """
MATCH (m:MusicCatalog)-[:HAS_MOOD]-(mood:Mood)
WHERE toLower(mood.mood) CONTAINS toLower($mood)
RETURN DISTINCT
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  mood.mood AS matched_mood,
  coalesce(m.track_popularity, 0) AS popularity,
  10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT $limit
""",
        Q_REC_003: """
MATCH (m:MusicCatalog)-[:HAS_DIM_CTX_EXERCISE|HAS_DIM_CTX_COMMUTE|HAS_DIM_CTX_HOME|HAS_DIM_CTX_SOCIAL|HAS_DIM_CTX_FOCUS|HAS_DIM_CTX_TRAVEL|HAS_DIM_CTX_SPECIAL]-(s)
WHERE toLower(s.name) CONTAINS toLower($situation)
RETURN DISTINCT
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  s.name AS matched_situation,
  coalesce(m.track_popularity, 0) AS popularity,
  10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT $limit
""",
        Q_REC_004: """
MATCH (m:MusicCatalog)-[:HAS_DIM_WEATHER]-(w:DimWeather)
WHERE toLower(w.name) CONTAINS toLower($weather)
RETURN DISTINCT
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  w.name AS matched_weather,
  coalesce(m.track_popularity, 0) AS popularity,
  10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT $limit
""",
        Q_REC_006: """
MATCH (m:MusicCatalog)
WHERE
  ($genre IS NULL OR toLower(m.playlist_genre) = toLower($genre))
  AND ($subgenre IS NULL OR toLower(m.playlist_subgenre) = toLower($subgenre))
  AND ($artist IS NULL OR toLower(m.track_artist) CONTAINS toLower($artist))
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.playlist_genre AS genre,
  coalesce(m.track_popularity, 0) AS popularity,
  coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT $limit
""",
        Q_REC_008: """
MATCH (m:MusicCatalog)
OPTIONAL MATCH (m)-[:HAS_GENRE]-(g:Genre)
OPTIONAL MATCH (m)-[:HAS_MOOD]-(mood:Mood)
OPTIONAL MATCH (m)-[:HAS_DIM_CTX_EXERCISE|HAS_DIM_CTX_COMMUTE|HAS_DIM_CTX_HOME|HAS_DIM_CTX_SOCIAL|HAS_DIM_CTX_FOCUS|HAS_DIM_CTX_TRAVEL|HAS_DIM_CTX_SPECIAL|HAS_DIM_CTX_EMOTION_SIT]-(s)
OPTIONAL MATCH (m)-[:HAS_DIM_WEATHER]-(w:DimWeather)
WITH m,
  max(CASE WHEN $genre IS NOT NULL AND toLower(g.genre) = toLower($genre) THEN 1 ELSE 0 END) AS genre_match,
  max(CASE WHEN $mood IS NOT NULL AND toLower(mood.mood) = toLower($mood) THEN 1 ELSE 0 END) AS mood_match,
  max(CASE WHEN $situation IS NOT NULL AND toLower(s.name) CONTAINS toLower($situation) THEN 1 ELSE 0 END) AS situation_match,
  max(CASE WHEN $weather IS NOT NULL AND toLower(w.name) CONTAINS toLower($weather) THEN 1 ELSE 0 END) AS weather_match
WITH m, genre_match + mood_match + situation_match + weather_match AS matched_count
WHERE matched_count > 0
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  matched_count,
  coalesce(m.track_popularity, 0) AS popularity,
  matched_count * 10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT $limit
""",
    }

    PARAMETER_TEMPLATES: ClassVar[dict[str, dict]] = {
        Q_SEARCH_001: {
            "required": ["keyword"],
            "defaults": {"limit": 10},
            "optional_nullable": [],
        },
        Q_SEARCH_003: {
            "required": [],
            "defaults": {"genre": None, "subgenre": None, "artist": None, "release_year": None, "limit": 20},
            "optional_nullable": ["genre", "subgenre", "artist", "release_year"],
        },
        Q_SEARCH_009: {
            "required": ["artist"],
            "defaults": {"limit": 30},
            "optional_nullable": [],
        },
        Q_SEARCH_011: {
            "required": [],
            "defaults": {"year": None, "start_year": None, "end_year": None, "limit": 20},
            "optional_nullable": ["year", "start_year", "end_year"],
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
        Q_REC_006: {
            "required": [],
            "defaults": {"genre": None, "subgenre": None, "artist": None, "limit": 10},
            "optional_nullable": ["genre", "subgenre", "artist"],
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
