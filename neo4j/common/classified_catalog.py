"""
music_catalog.csv 오디오 피처를 spotify_music_recommendation_guide.md 조건으로 분류해
track_id + 차원별(dim_*) CSV를 생성한다.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from common.constant import (
    MUSIC_CATALOG_CSV_FILENAME,
    MUSIC_CATALOG_SCENARIOS_CSV_FILENAME,
    SCENARIO_COL_TAG_COUNT,
    SCENARIO_COL_TAGS_ALL,
    SCENARIO_CSV_TAG_SEPARATOR,
    SCENARIO_DIM_COLUMNS,
    SCENARIO_KEY_COLUMN,
)


####################################################################
# 데이터 경로·스칼라 (common.utils 의존 시 neo4j 드라이버 필요 — 단독 실행용 로컬 정의)
####################################################################
def get_filepath(file_name: str) -> Path:
    """`neo4j/data/` 아래 파일에 대한 절대 경로(`Path`)를 반환한다."""
    _DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    return _DATA_DIR / file_name


def scalar_or_none(value: object) -> object:
    """NaN·None·빈 문자열이면 None, 그 외에는 원값을 그대로 반환한다(스칼라 셀 정규화)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _f(row: pd.Series, name: str) -> float | None:
    """한 행에서 컬럼값을 float으로 읽고, 없거나 변환 불가면 None."""
    v = scalar_or_none(row.get(name))
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mode_bin(row: pd.Series) -> int | None:
    """`mode`를 장조 1 / 단조 0으로 정규화한다(0.5 미만→0). 결측이면 None."""
    m = _f(row, "mode")
    if m is None:
        return None
    return 1 if m >= 0.5 else 0


#################################################################################################
# 규칙 술어 타입: DataFrame 한 행(pd.Series)을 받아 해당 시나리오 조건 만족 여부(bool)를 반환하는 호출 가능 객체.
# ScenarioRule.predicate 필드에 아래 명명 함수를 지정한다. (DataFrame 자체를 정의하는 것은 아님)
#################################################################################################
RowPred = Callable[[pd.Series], bool]


@dataclass(frozen=True)
class ScenarioRule:
    """시나리오 규칙 한 줄: 차원(group), 출력 tag_id, 행 단위 참/거짓 술어(predicate)."""

    group: str
    tag_id: str
    predicate: RowPred


# ---- 가이드 표 기반 규칙 술어 ----


def _weather_sunny(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    mo = _mode_bin(row)
    return v is not None and e is not None and mo == 1 and v >= 0.6 and e >= 0.5


def _weather_rain(row: pd.Series) -> bool:
    va = _f(row, "valence")
    ac = _f(row, "acousticness")
    t = _f(row, "tempo")
    mo = _mode_bin(row)
    return (
        all(x is not None for x in (va, ac, t, mo))
        and va <= 0.4
        and ac >= 0.5
        and mo == 0
        and 60 <= t <= 90
    )


def _weather_snow(row: pd.Series) -> bool:
    ac = _f(row, "acousticness")
    v = _f(row, "valence")
    t = _f(row, "tempo")
    return (
        ac is not None
        and v is not None
        and t is not None
        and ac >= 0.6
        and 0.3 <= v <= 0.6
        and t <= 80
    )


def _weather_cloudy(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    mo = _mode_bin(row)
    return (
        v is not None
        and e is not None
        and mo == 0
        and 0.3 <= v <= 0.5
        and 0.3 <= e <= 0.5
    )


def _season_spring(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    ac = _f(row, "acousticness")
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (v, e, ac, t))
        and v >= 0.6
        and 0.4 <= e <= 0.7
        and ac >= 0.4
        and 90 <= t <= 120
    )


def _season_summer(row: pd.Series) -> bool:
    e = _f(row, "energy")
    d = _f(row, "danceability")
    v = _f(row, "valence")
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (e, d, v, t))
        and e >= 0.7
        and d >= 0.6
        and v >= 0.6
        and t >= 120
    )


def _season_autumn(row: pd.Series) -> bool:
    v = _f(row, "valence")
    ac = _f(row, "acousticness")
    mo = _mode_bin(row)
    return (
        v is not None
        and ac is not None
        and mo == 0
        and 0.3 <= v <= 0.5
        and ac >= 0.5
    )


def _season_winter(row: pd.Series) -> bool:
    ac = _f(row, "acousticness")
    v = _f(row, "valence")
    e = _f(row, "energy")
    return (
        ac is not None
        and v is not None
        and e is not None
        and ac >= 0.5
        and v <= 0.4
        and e <= 0.4
    )


def _emotion_lonely(row: pd.Series) -> bool:
    v = _f(row, "valence")
    ac = _f(row, "acousticness")
    mo = _mode_bin(row)
    return v is not None and ac is not None and mo == 0 and v <= 0.3 and ac >= 0.6


def _emotion_melancholy(row: pd.Series) -> bool:
    v = _f(row, "valence")
    mo = _mode_bin(row)
    e = _f(row, "energy")
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (v, mo, e, t))
        and v <= 0.3
        and mo == 0
        and e <= 0.4
        and t <= 80
    )


def _emotion_hyped(row: pd.Series) -> bool:
    e = _f(row, "energy")
    d = _f(row, "danceability")
    v = _f(row, "valence")
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (e, d, v, t))
        and e >= 0.8
        and d >= 0.7
        and v >= 0.7
        and t >= 120
    )


def _emotion_thrill(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    mo = _mode_bin(row)
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (v, e, mo, t))
        and v >= 0.6
        and 0.5 <= e <= 0.7
        and mo == 1
        and 100 <= t <= 130
    )


def _time_morning(row: pd.Series) -> bool:
    e = _f(row, "energy")
    v = _f(row, "valence")
    t = _f(row, "tempo")
    mo = _mode_bin(row)
    return (
        all(x is not None for x in (e, v, t, mo))
        and 0.5 <= e <= 0.7
        and v >= 0.6
        and 100 <= t <= 120
        and mo == 1
    )


def _time_afternoon(row: pd.Series) -> bool:
    e = _f(row, "energy")
    v = _f(row, "valence")
    return e is not None and v is not None and 0.5 <= e <= 0.8 and 0.5 <= v <= 0.8


def _time_evening(row: pd.Series) -> bool:
    v = _f(row, "valence")
    ac = _f(row, "acousticness")
    e = _f(row, "energy")
    return (
        v is not None
        and ac is not None
        and e is not None
        and 0.3 <= v <= 0.6
        and ac >= 0.4
        and e <= 0.5
    )


def _time_night(row: pd.Series) -> bool:
    ac = _f(row, "acousticness")
    e = _f(row, "energy")
    t = _f(row, "tempo")
    return (
        ac is not None
        and e is not None
        and t is not None
        and ac >= 0.5
        and e <= 0.4
        and t <= 90
    )


def _time_dawn(row: pd.Series) -> bool:
    i = _f(row, "instrumentalness")
    e = _f(row, "energy")
    l = _f(row, "loudness")
    return (
        i is not None
        and e is not None
        and l is not None
        and i >= 0.5
        and e <= 0.3
        and l <= -10
    )


def _energy_level_calm(row: pd.Series) -> bool:
    e = _f(row, "energy")
    t = _f(row, "tempo")
    ac = _f(row, "acousticness")
    l = _f(row, "loudness")
    return (
        all(x is not None for x in (e, t, ac, l))
        and e <= 0.4
        and t <= 90
        and ac >= 0.5
        and l <= -8
    )


def _energy_level_moderate(row: pd.Series) -> bool:
    e = _f(row, "energy")
    t = _f(row, "tempo")
    return e is not None and t is not None and 0.4 <= e <= 0.7 and 90 <= t <= 120


def _energy_level_hyped(row: pd.Series) -> bool:
    e = _f(row, "energy")
    d = _f(row, "danceability")
    t = _f(row, "tempo")
    return e is not None and d is not None and t is not None and e >= 0.7 and d >= 0.7 and t >= 120


def _commute_to_work(row: pd.Series) -> bool:
    e = _f(row, "energy")
    v = _f(row, "valence")
    t = _f(row, "tempo")
    mo = _mode_bin(row)
    return (
        all(x is not None for x in (e, v, t, mo))
        and 0.5 <= e <= 0.7
        and v >= 0.5
        and 100 <= t <= 120
        and mo == 1
    )


def _commute_from_work(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    ac = _f(row, "acousticness")
    return (
        v is not None
        and e is not None
        and ac is not None
        and 0.3 <= v <= 0.6
        and e <= 0.5
        and ac >= 0.3
    )


def _commute_public(row: pd.Series) -> bool:
    i = _f(row, "instrumentalness")
    e = _f(row, "energy")
    sp = _f(row, "speechiness")
    return (
        i is not None
        and e is not None
        and sp is not None
        and i >= 0.4
        and 0.3 <= e <= 0.6
        and sp <= 0.1
    )


def _commute_drive(row: pd.Series) -> bool:
    e = _f(row, "energy")
    t = _f(row, "tempo")
    d = _f(row, "danceability")
    v = _f(row, "valence")
    return (
        all(x is not None for x in (e, t, d, v))
        and 0.6 <= e <= 0.8
        and 110 <= t <= 140
        and d >= 0.6
        and v >= 0.5
    )


def _home_chores(row: pd.Series) -> bool:
    e = _f(row, "energy")
    d = _f(row, "danceability")
    v = _f(row, "valence")
    return (
        e is not None
        and d is not None
        and v is not None
        and 0.5 <= e <= 0.7
        and d >= 0.6
        and v >= 0.5
    )


def _home_cooking(row: pd.Series) -> bool:
    v = _f(row, "valence")
    t = _f(row, "tempo")
    d = _f(row, "danceability")
    return (
        v is not None
        and t is not None
        and d is not None
        and v >= 0.5
        and 100 <= t <= 130
        and 0.5 <= d <= 0.7
    )


def _home_shower(row: pd.Series) -> bool:
    e = _f(row, "energy")
    v = _f(row, "valence")
    return e is not None and v is not None and e >= 0.6 and v >= 0.6


def _home_rest(row: pd.Series) -> bool:
    ac = _f(row, "acousticness")
    e = _f(row, "energy")
    i = _f(row, "instrumentalness")
    return (
        ac is not None
        and e is not None
        and i is not None
        and ac >= 0.5
        and e <= 0.4
        and i >= 0.3
    )


def _home_sleep(row: pd.Series) -> bool:
    e = _f(row, "energy")
    t = _f(row, "tempo")
    ac = _f(row, "acousticness")
    l = _f(row, "loudness")
    return (
        all(x is not None for x in (e, t, ac, l))
        and e <= 0.3
        and t <= 70
        and ac >= 0.6
        and l <= -10
    )


def _focus_study(row: pd.Series) -> bool:
    i = _f(row, "instrumentalness")
    sp = _f(row, "speechiness")
    e = _f(row, "energy")
    return (
        i is not None
        and sp is not None
        and e is not None
        and i >= 0.7
        and sp <= 0.05
        and 0.3 <= e <= 0.5
    )


def _focus_office(row: pd.Series) -> bool:
    i = _f(row, "instrumentalness")
    e = _f(row, "energy")
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (i, e, t))
        and i >= 0.6
        and 0.4 <= e <= 0.6
        and 90 <= t <= 120
    )


def _focus_deadline(row: pd.Series) -> bool:
    e = _f(row, "energy")
    t = _f(row, "tempo")
    i = _f(row, "instrumentalness")
    return (
        all(x is not None for x in (e, t, i))
        and 0.6 <= e <= 0.8
        and t >= 120
        and i >= 0.5
    )


def _exercise_gym(row: pd.Series) -> bool:
    e = _f(row, "energy")
    t = _f(row, "tempo")
    d = _f(row, "danceability")
    l = _f(row, "loudness")
    return (
        all(x is not None for x in (e, t, d, l))
        and e >= 0.8
        and t >= 130
        and d >= 0.7
        and l >= -6
    )


def _exercise_walk(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    t = _f(row, "tempo")
    return (
        v is not None
        and e is not None
        and t is not None
        and v >= 0.5
        and 0.4 <= e <= 0.6
        and 90 <= t <= 110
    )


def _exercise_stretch(row: pd.Series) -> bool:
    e = _f(row, "energy")
    ac = _f(row, "acousticness")
    t = _f(row, "tempo")
    return (
        e is not None
        and ac is not None
        and t is not None
        and e <= 0.4
        and ac >= 0.5
        and t <= 80
    )


def _social_date(row: pd.Series) -> bool:
    v = _f(row, "valence")
    ac = _f(row, "acousticness")
    mo = _mode_bin(row)
    e = _f(row, "energy")
    return (
        all(x is not None for x in (v, ac, mo, e))
        and v >= 0.5
        and ac >= 0.3
        and mo == 1
        and 0.4 <= e <= 0.6
    )


def _social_friends(row: pd.Series) -> bool:
    d = _f(row, "danceability")
    e = _f(row, "energy")
    v = _f(row, "valence")
    return (
        d is not None
        and e is not None
        and v is not None
        and d >= 0.6
        and e >= 0.6
        and v >= 0.6
    )


def _social_celebration(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    mo = _mode_bin(row)
    return v is not None and e is not None and mo == 1 and v >= 0.7 and e >= 0.6


def _social_homeparty(row: pd.Series) -> bool:
    d = _f(row, "danceability")
    e = _f(row, "energy")
    v = _f(row, "valence")
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (d, e, v, t))
        and d >= 0.7
        and e >= 0.7
        and v >= 0.6
        and t >= 110
    )


def _sit_breakup(row: pd.Series) -> bool:
    v = _f(row, "valence")
    mo = _mode_bin(row)
    ac = _f(row, "acousticness")
    e = _f(row, "energy")
    return (
        all(x is not None for x in (v, mo, ac, e))
        and v <= 0.3
        and mo == 0
        and ac >= 0.4
        and e <= 0.4
    )


def _sit_comfort(row: pd.Series) -> bool:
    v = _f(row, "valence")
    ac = _f(row, "acousticness")
    t = _f(row, "tempo")
    return (
        v is not None
        and ac is not None
        and t is not None
        and 0.3 <= v <= 0.5
        and ac >= 0.5
        and t <= 90
    )


def _sit_mood_lift(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    mo = _mode_bin(row)
    return v is not None and e is not None and mo == 1 and v >= 0.6 and e >= 0.6


def _sit_nostalgia(row: pd.Series) -> bool:
    v = _f(row, "valence")
    ac = _f(row, "acousticness")
    return v is not None and ac is not None and 0.4 <= v <= 0.7 and ac >= 0.4


def _travel_prep(row: pd.Series) -> bool:
    v = _f(row, "valence")
    e = _f(row, "energy")
    d = _f(row, "danceability")
    return (
        v is not None
        and e is not None
        and d is not None
        and v >= 0.6
        and e >= 0.6
        and d >= 0.5
    )


def _travel_transit(row: pd.Series) -> bool:
    i = _f(row, "instrumentalness")
    e = _f(row, "energy")
    return (
        i is not None
        and e is not None
        and i >= 0.4
        and 0.3 <= e <= 0.5
    )


def _travel_on_trip(row: pd.Series) -> bool:
    e = _f(row, "energy")
    v = _f(row, "valence")
    t = _f(row, "tempo")
    return (
        e is not None
        and v is not None
        and t is not None
        and 0.6 <= e <= 0.8
        and v >= 0.6
        and 110 <= t <= 130
    )


def _special_cafe(row: pd.Series) -> bool:
    ac = _f(row, "acousticness")
    e = _f(row, "energy")
    i = _f(row, "instrumentalness")
    t = _f(row, "tempo")
    return (
        all(x is not None for x in (ac, e, i, t))
        and ac >= 0.5
        and 0.2 <= e <= 0.5
        and i >= 0.4
        and 70 <= t <= 100
    )


def _special_club(row: pd.Series) -> bool:
    d = _f(row, "danceability")
    e = _f(row, "energy")
    t = _f(row, "tempo")
    l = _f(row, "loudness")
    return (
        all(x is not None for x in (d, e, t, l))
        and d >= 0.8
        and e >= 0.8
        and t >= 125
        and l >= -5
    )


def _special_festival(row: pd.Series) -> bool:
    e = _f(row, "energy")
    li = _f(row, "liveness")
    d = _f(row, "danceability")
    return (
        e is not None
        and li is not None
        and d is not None
        and e >= 0.8
        and li >= 0.5
        and d >= 0.7
    )


def _special_gaming(row: pd.Series) -> bool:
    e = _f(row, "energy")
    t = _f(row, "tempo")
    i = _f(row, "instrumentalness")
    return (
        all(x is not None for x in (e, t, i))
        and 0.6 <= e <= 0.9
        and t >= 120
        and i >= 0.5
    )


def _special_dawn_mood(row: pd.Series) -> bool:
    v = _f(row, "valence")
    ac = _f(row, "acousticness")
    mo = _mode_bin(row)
    e = _f(row, "energy")
    return (
        all(x is not None for x in (v, ac, mo, e))
        and v <= 0.4
        and ac >= 0.6
        and mo == 0
        and e <= 0.3
    )


def _rules() -> list[ScenarioRule]:
    """가이드 문서 표를 반영한 모든 `ScenarioRule`을 담은 리스트를 구성해 반환한다."""
    R: list[ScenarioRule] = []

    # —— 날씨 ——
    R.append(ScenarioRule("weather", "weather_sunny", _weather_sunny))
    R.append(ScenarioRule("weather", "weather_rain", _weather_rain))
    R.append(ScenarioRule("weather", "weather_snow", _weather_snow))
    R.append(ScenarioRule("weather", "weather_cloudy", _weather_cloudy))

    # —— 계절 ——
    R.append(ScenarioRule("season", "season_spring", _season_spring))
    R.append(ScenarioRule("season", "season_summer", _season_summer))
    R.append(ScenarioRule("season", "season_autumn", _season_autumn))
    R.append(ScenarioRule("season", "season_winter", _season_winter))

    # —— 감정 ——
    R.append(ScenarioRule("emotion", "emotion_lonely", _emotion_lonely))
    R.append(ScenarioRule("emotion", "emotion_melancholy", _emotion_melancholy))
    R.append(ScenarioRule("emotion", "emotion_hyped", _emotion_hyped))
    R.append(ScenarioRule("emotion", "emotion_thrill", _emotion_thrill))

    # —— 시간대 ——
    R.append(ScenarioRule("time_of_day", "time_morning", _time_morning))
    R.append(ScenarioRule("time_of_day", "time_afternoon", _time_afternoon))
    R.append(ScenarioRule("time_of_day", "time_evening", _time_evening))
    R.append(ScenarioRule("time_of_day", "time_night", _time_night))
    R.append(ScenarioRule("time_of_day", "time_dawn", _time_dawn))

    # —— 에너지 레벨 ——
    R.append(ScenarioRule("energy_level", "energy_level_calm", _energy_level_calm))
    R.append(ScenarioRule("energy_level", "energy_level_moderate", _energy_level_moderate))
    R.append(ScenarioRule("energy_level", "energy_level_hyped", _energy_level_hyped))

    # —— 이동 ——
    R.append(ScenarioRule("ctx_commute", "commute_to_work", _commute_to_work))
    R.append(ScenarioRule("ctx_commute", "commute_from_work", _commute_from_work))
    R.append(ScenarioRule("ctx_commute", "commute_public", _commute_public))
    R.append(ScenarioRule("ctx_commute", "commute_drive", _commute_drive))

    # —— 집 ——
    R.append(ScenarioRule("ctx_home", "home_chores", _home_chores))
    R.append(ScenarioRule("ctx_home", "home_cooking", _home_cooking))
    R.append(ScenarioRule("ctx_home", "home_shower", _home_shower))
    R.append(ScenarioRule("ctx_home", "home_rest", _home_rest))
    R.append(ScenarioRule("ctx_home", "home_sleep", _home_sleep))

    # —— 집중 ——
    R.append(ScenarioRule("ctx_focus", "focus_study", _focus_study))
    R.append(ScenarioRule("ctx_focus", "focus_office", _focus_office))
    R.append(ScenarioRule("ctx_focus", "focus_deadline", _focus_deadline))

    # —— 운동 ——
    R.append(ScenarioRule("ctx_exercise", "exercise_gym", _exercise_gym))
    R.append(ScenarioRule("ctx_exercise", "exercise_walk", _exercise_walk))
    R.append(ScenarioRule("ctx_exercise", "exercise_stretch", _exercise_stretch))

    # —— 관계 / 이벤트 ——
    R.append(ScenarioRule("ctx_social", "social_date", _social_date))
    R.append(ScenarioRule("ctx_social", "social_friends", _social_friends))
    R.append(ScenarioRule("ctx_social", "social_celebration", _social_celebration))
    R.append(ScenarioRule("ctx_social", "social_homeparty", _social_homeparty))

    # —— 감정 상황 ——
    R.append(ScenarioRule("ctx_emotion_sit", "sit_breakup", _sit_breakup))
    R.append(ScenarioRule("ctx_emotion_sit", "sit_comfort", _sit_comfort))
    R.append(ScenarioRule("ctx_emotion_sit", "sit_mood_lift", _sit_mood_lift))
    R.append(ScenarioRule("ctx_emotion_sit", "sit_nostalgia", _sit_nostalgia))

    # —— 여행 ——
    R.append(ScenarioRule("ctx_travel", "travel_prep", _travel_prep))
    R.append(ScenarioRule("ctx_travel", "travel_transit", _travel_transit))
    R.append(ScenarioRule("ctx_travel", "travel_on_trip", _travel_on_trip))

    # —— 특수 ——
    R.append(ScenarioRule("ctx_special", "special_cafe", _special_cafe))
    R.append(ScenarioRule("ctx_special", "special_club", _special_club))
    R.append(ScenarioRule("ctx_special", "special_festival", _special_festival))
    R.append(ScenarioRule("ctx_special", "special_gaming", _special_gaming))
    R.append(ScenarioRule("ctx_special", "special_dawn_mood", _special_dawn_mood))

    return R


SCENARIO_RULES: list[ScenarioRule] = _rules()


def collect_tags_by_group(row: pd.Series) -> dict[str, list[str]]:
    """한 트랙 행에 대해 `SCENARIO_RULES`를 평가해, 차원(group)별로 만족한 tag_id 목록을 모은다."""
    out: dict[str, list[str]] = {}
    for rule in SCENARIO_RULES:
        if rule.predicate(row):
            out.setdefault(rule.group, []).append(rule.tag_id)
    return out


def row_to_output_record(row: pd.Series, sep: str = SCENARIO_CSV_TAG_SEPARATOR) -> dict[str, str]:
    """CSV 출력 한 행에 해당하는 dict: `track_id`, 각 `dim_*`, `scenario_tags_all`, `scenario_tag_count`."""
    by_g = collect_tags_by_group(row)
    tid = scalar_or_none(row.get(SCENARIO_KEY_COLUMN))
    rec = {SCENARIO_KEY_COLUMN: str(tid).strip() if tid is not None else ""}
    for col in SCENARIO_DIM_COLUMNS:
        group = col.removeprefix("dim_")
        tags = by_g.get(group, [])
        rec[col] = sep.join(tags)
    all_tags = [t for tags in by_g.values() for t in tags]
    rec[SCENARIO_COL_TAGS_ALL] = sep.join(all_tags)
    rec[SCENARIO_COL_TAG_COUNT] = str(len(all_tags))
    return rec


def validate_track_ids(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """`track_id` 결측·공백·중복(동일 키 2행 이상)을 검사한다. (통과 여부, 경고 문구들) 반환."""
    msgs: list[str] = []
    if SCENARIO_KEY_COLUMN not in df.columns:
        msgs.append(f"입력에 {SCENARIO_KEY_COLUMN} 컬럼이 없습니다.")
        return False, msgs

    def norm(x: object) -> str | None:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return None
        s = str(x).strip()
        return s if s else None

    raw = df[SCENARIO_KEY_COLUMN].map(norm)
    nulls = raw.isna()
    if nulls.any():
        msgs.append(f"track_id 결측/공백 행: {int(nulls.sum())}건")
    valid = raw.dropna()
    dup_mask = valid.duplicated(keep=False)
    if dup_mask.any():
        msgs.append(f"track_id 중복 행(동일 키 2행 이상): {int(dup_mask.sum())}건")
    return len(msgs) == 0, msgs


def classify_catalog(
    input_path: str | Path,
    output_csv_path: str | Path,
    sep: str = SCENARIO_CSV_TAG_SEPARATOR,
) -> tuple[pd.DataFrame, bool, list[str], int]:
    """음원 카탈로그 CSV를 읽어 시나리오 분류 결과 DataFrame을 만들고 CSV로 저장한다.

    Returns:
        (결과 DataFrame, track_id 검증 통과 여부, 검증 메시지 목록, 입력 행 수)
    """
    df = pd.read_csv(input_path, dtype={SCENARIO_KEY_COLUMN: str}, low_memory=False)
    ok, issues = validate_track_ids(df)
    if not ok:
        for m in issues:
            print("경고:", m, file=sys.stderr)

    rows = [row_to_output_record(row, sep=sep) for _, row in df.iterrows()]
    out_df = pd.DataFrame(rows)
    column_order = [
        SCENARIO_KEY_COLUMN,
        *SCENARIO_DIM_COLUMNS,
        SCENARIO_COL_TAGS_ALL,
        SCENARIO_COL_TAG_COUNT,
    ]
    out_df = out_df[column_order]
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_csv_path, index=False)
    return out_df, ok, issues, len(df)


if __name__ == "__main__":
    in_path = get_filepath(MUSIC_CATALOG_CSV_FILENAME)
    out_path = get_filepath(MUSIC_CATALOG_SCENARIOS_CSV_FILENAME)

    out_df, _tid_ok, _tid_msgs, _n_in = classify_catalog(in_path, out_path)

    print(f"Wrote {out_path}")
