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
    LABEL_EMOTION = "LabelEmotion"
    LABEL_EMOTION_SITUATION = "LabelEmotionSituation"
    LABEL_TIME = "LabelTime"
    LABEL_FOCUS = "LabelFocus"
    LABEL_EXERCISE = "LabelExercise"
    LABEL_HOME = "LabelHome"
    LABEL_COMMUTE = "LabelCommute"
    LABEL_SPECIAL = "LabelSpecial"
    LABEL_WEATHER = "LabelWeather"
    LABEL_SEASON = "LabelSeason"

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
    HAS_LABEL_EMOTION = "HAS_LABEL_EMOTION"
    HAS_LABEL_EMOTION_SIT = "HAS_LABEL_EMOTION_SIT"
    HAS_LABEL_TIME = "HAS_LABEL_TIME"
    HAS_LABEL_FOCUS = "HAS_LABEL_FOCUS"
    HAS_LABEL_EXERCISE = "HAS_LABEL_EXERCISE"
    HAS_LABEL_HOME = "HAS_LABEL_HOME"
    HAS_LABEL_COMMUTE = "HAS_LABEL_COMMUTE"
    HAS_LABEL_SPECIAL = "HAS_LABEL_SPECIAL"
    HAS_LABEL_WEATHER = "HAS_LABEL_WEATHER"
    HAS_LABEL_SEASON = "HAS_LABEL_SEASON"


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
# 시나리오 라벨(tag_id) ↔ 한글 레거시 키 (가이드·옛 접두사 체계, 참고용)
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
# 카테고리 라벨 열 스키마·파일명 (classified_catalog.CATEGORY_PRIORITY 열 순)
###########################################################
LABEL_CSV_KEY_COLUMN: str = "track_id"
LABEL_CSV_TAG_SEPARATOR: str = ";"
LABEL_CATEGORY_COLUMNS: tuple[str, ...] = (
    "emotion",
    "emotion_situation",
    "time",
    "focus",
    "exercise",
    "home",
    "commute",
    "special",
    "weather",
    "season",
)

# music_catalog_scenarios.csv 열 이름 → (값 노드 Neo4j 라벨, MusicCatalog→값 노드 관계 타입)
LABEL_CATEGORY_TO_NODE_AND_REL: dict[str, tuple[KagNodeLabel, KagRelationType]] = {
    "emotion": (KagNodeLabel.LABEL_EMOTION, KagRelationType.HAS_LABEL_EMOTION),
    "emotion_situation": (
        KagNodeLabel.LABEL_EMOTION_SITUATION,
        KagRelationType.HAS_LABEL_EMOTION_SIT,
    ),
    "time": (KagNodeLabel.LABEL_TIME, KagRelationType.HAS_LABEL_TIME),
    "focus": (KagNodeLabel.LABEL_FOCUS, KagRelationType.HAS_LABEL_FOCUS),
    "exercise": (KagNodeLabel.LABEL_EXERCISE, KagRelationType.HAS_LABEL_EXERCISE),
    "home": (KagNodeLabel.LABEL_HOME, KagRelationType.HAS_LABEL_HOME),
    "commute": (KagNodeLabel.LABEL_COMMUTE, KagRelationType.HAS_LABEL_COMMUTE),
    "special": (KagNodeLabel.LABEL_SPECIAL, KagRelationType.HAS_LABEL_SPECIAL),
    "weather": (KagNodeLabel.LABEL_WEATHER, KagRelationType.HAS_LABEL_WEATHER),
    "season": (KagNodeLabel.LABEL_SEASON, KagRelationType.HAS_LABEL_SEASON),
}

if set(LABEL_CATEGORY_TO_NODE_AND_REL.keys()) != set(LABEL_CATEGORY_COLUMNS):
    raise RuntimeError("LABEL_CATEGORY_COLUMNS와 LABEL_CATEGORY_TO_NODE_AND_REL 키가 일치해야 합니다.")

LABEL_COL_TAGS_ALL: str = "scenario_tags_all"
LABEL_COL_TAG_COUNT: str = "scenario_tag_count"

# neo4j/data 내 CSV·neo4j 루트 MD 파일명
MUSIC_CATALOG_CSV_FILENAME: str = "music_catalog.csv"
MUSIC_CATALOG_SCENARIOS_CSV_FILENAME: str = "music_catalog_scenarios.csv"