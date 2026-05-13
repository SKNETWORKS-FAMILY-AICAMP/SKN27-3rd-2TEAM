# 패키지
from enum import Enum



###########################################################
# node 타입
###########################################################
class KagNodeLabel(str, Enum):
    """ 노드를 정의할 때 사용할 Node 타입을 정의한다. """
    MUSIC_CATALOG = "MusicCatalog"
    GENRE = "Genre"
    PLAYLIST_SUBGENRE = "PlaylistSubGenre"
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
    """엣지를 정의할 때 사용할 Relationship 타입을 정의한다."""

    HAS_GENRE = "HAS_GENRE"
    HAS_PLAYLIST_SUBGENRE = "HAS_PLAYLIST_SUBGENRE"
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


###########################################################
# 파생 라벨 타입
###########################################################
class KagMoodLabel(str, Enum):
    """Spotify audio feature 기반으로 파생되는 Mood 라벨"""

    CALM = "calm"
    ENERGETIC = "energetic"
    SENTIMENTAL = "sentimental"
    DANCE = "dance"
    ACOUSTIC = "acoustic"
    BRIGHT = "bright"
    FOCUS = "focus"


class KagTempoLabel(str, Enum):
    """Spotify tempo 값을 구간화해서 생성하는 Tempo 라벨"""

    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"


###########################################################
# 시나리오 분류 tag_id ↔ 한글 (spotify_music_recommendation_guide 기반)
###########################################################
TAG_LABELS_KO: dict[str, str] = {
    "weather_sunny": "맑음",
    "weather_rain": "비",
    "weather_snow": "눈",
    "weather_cloudy": "흐림",
    "season_spring": "봄",
    "season_summer": "여름",
    "season_autumn": "가을",
    "season_winter": "겨울",
    "emotion_lonely": "외로움",
    "emotion_melancholy": "우울함",
    "emotion_hyped": "신남(감정)",
    "emotion_thrill": "설렘",
    "time_morning": "아침",
    "time_afternoon": "오후",
    "time_evening": "저녁",
    "time_night": "밤",
    "time_dawn": "새벽",
    "energy_level_calm": "잔잔함",
    "energy_level_moderate": "보통",
    "energy_level_hyped": "신남(에너지)",
    "commute_to_work": "출근길",
    "commute_from_work": "퇴근길",
    "commute_public": "대중교통",
    "commute_drive": "드라이브",
    "home_chores": "집안일",
    "home_cooking": "요리",
    "home_shower": "샤워",
    "home_rest": "쉬는 중",
    "home_sleep": "잠들기 전",
    "focus_study": "공부/독서",
    "focus_office": "코딩/업무",
    "focus_deadline": "과제 마감",
    "exercise_gym": "운동",
    "exercise_walk": "산책",
    "exercise_stretch": "스트레칭/요가",
    "social_date": "데이트",
    "social_friends": "친구 모임",
    "social_celebration": "생일/기념일",
    "social_homeparty": "홈파티",
    "sit_breakup": "이별 후",
    "sit_comfort": "위로 필요",
    "sit_mood_lift": "기분 전환",
    "sit_nostalgia": "추억 회상",
    "travel_prep": "여행 준비",
    "travel_transit": "공항/기차",
    "travel_on_trip": "여행 중",
    "special_cafe": "카페",
    "special_club": "클럽",
    "special_festival": "페스티벌",
    "special_gaming": "게임",
    "special_dawn_mood": "감성/새벽 감성",
}


###########################################################
# 시나리오 분류 출력 스키마·파일명 (classified_catalog)
###########################################################
SCENARIO_KEY_COLUMN: str = "track_id"
SCENARIO_CSV_TAG_SEPARATOR: str = ";"
SCENARIO_DIM_COLUMNS: tuple[str, ...] = (
    "dim_weather",
    "dim_season",
    "dim_emotion",
    "dim_time_of_day",
    "dim_energy_level",
    "dim_ctx_commute",
    "dim_ctx_home",
    "dim_ctx_focus",
    "dim_ctx_exercise",
    "dim_ctx_social",
    "dim_ctx_emotion_sit",
    "dim_ctx_travel",
    "dim_ctx_special",
)

# CSV dim_* 컬럼명 → (값 노드 라벨, MusicCatalog에서 값 노드로 가는 관계 타입)
SCENARIO_DIM_TO_LABEL_AND_REL: dict[str, tuple[KagNodeLabel, KagRelationType]] = {
    "dim_weather": (KagNodeLabel.DIM_WEATHER, KagRelationType.HAS_DIM_WEATHER),
    "dim_season": (KagNodeLabel.DIM_SEASON, KagRelationType.HAS_DIM_SEASON),
    "dim_emotion": (KagNodeLabel.DIM_EMOTION, KagRelationType.HAS_DIM_EMOTION),
    "dim_time_of_day": (KagNodeLabel.DIM_TIME_OF_DAY, KagRelationType.HAS_DIM_TIME_OF_DAY),
    "dim_energy_level": (KagNodeLabel.DIM_ENERGY_LEVEL, KagRelationType.HAS_DIM_ENERGY_LEVEL),
    "dim_ctx_commute": (KagNodeLabel.DIM_CTX_COMMUTE, KagRelationType.HAS_DIM_CTX_COMMUTE),
    "dim_ctx_home": (KagNodeLabel.DIM_CTX_HOME, KagRelationType.HAS_DIM_CTX_HOME),
    "dim_ctx_focus": (KagNodeLabel.DIM_CTX_FOCUS, KagRelationType.HAS_DIM_CTX_FOCUS),
    "dim_ctx_exercise": (KagNodeLabel.DIM_CTX_EXERCISE, KagRelationType.HAS_DIM_CTX_EXERCISE),
    "dim_ctx_social": (KagNodeLabel.DIM_CTX_SOCIAL, KagRelationType.HAS_DIM_CTX_SOCIAL),
    "dim_ctx_emotion_sit": (
        KagNodeLabel.DIM_CTX_EMOTION_SIT,
        KagRelationType.HAS_DIM_CTX_EMOTION_SIT,
    ),
    "dim_ctx_travel": (KagNodeLabel.DIM_CTX_TRAVEL, KagRelationType.HAS_DIM_CTX_TRAVEL),
    "dim_ctx_special": (KagNodeLabel.DIM_CTX_SPECIAL, KagRelationType.HAS_DIM_CTX_SPECIAL),
}

if set(SCENARIO_DIM_TO_LABEL_AND_REL.keys()) != set(SCENARIO_DIM_COLUMNS):
    raise RuntimeError("SCENARIO_DIM_COLUMNS와 SCENARIO_DIM_TO_LABEL_AND_REL 키가 일치해야 합니다.")

SCENARIO_COL_TAGS_ALL: str = "scenario_tags_all"
SCENARIO_COL_TAG_COUNT: str = "scenario_tag_count"

# neo4j/data 내 CSV·neo4j 루트 MD 파일명
MUSIC_CATALOG_CSV_FILENAME: str = "music_catalog.csv"
MUSIC_CATALOG_SCENARIOS_CSV_FILENAME: str = "music_catalog_scenarios.csv"