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