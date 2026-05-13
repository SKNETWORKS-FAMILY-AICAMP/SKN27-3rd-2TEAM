"""
music_classifier.py
====================
음악 분류 조건을 정의하고, DataFrame에서 조건에 맞는 track_id를 추출한다.

■ 사용법 (딱 두 줄)
    from music_classifier import get_track_ids
    ids = get_track_ids(df, category="weather", keyword="비")

■ 지원 카테고리 / 키워드
    weather          : 맑음, 비, 눈, 흐림
    season           : 봄, 여름, 가을, 겨울
    time             : 아침, 오후, 저녁, 밤, 새벽
    emotion          : 외로움, 쓸쓸함, 우울함, 신남, 설렘, 차분함, 잔잔함, 보통, 적당함, 활기참
    commute          : 출근, 퇴근, 대중교통, 운전
    home             : 집안일, 청소, 요리, 샤워, 휴식, 잠, 수면
    focus            : 공부, 학습, 사무실, 업무, 마감, 데드라인
    exercise         : 헬스, 운동, 산책, 스트레칭, 요가
    emotion_situation: 이별, 위로, 기분전환, 추억, 회상
    special          : 카페, 클럽, 페스티벌, 게임, 새벽감성, 여행
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ══════════════════════════════════════════════════════════════════════════════
# 1. 분류 조건 테이블
#    구조: { category: { alias(한글) -> { 오디오 피처 조건 } } }
#    각 조건 값은 (min, max) 튜플 또는 단일 float / int.
#    min/max 중 하나만 쓰려면 None으로 채운다.
#    특수 키: "_mode" → 0(단조) / 1(장조) / None(무관)
# ══════════════════════════════════════════════════════════════════════════════

# ── 내부 헬퍼: alias → English key ──────────────────────────────────────────
_ALIAS: dict[str, dict[str, str]] = {
    "weather": {
        "맑음": "sunny", "비": "rain", "눈": "snow", "흐림": "cloudy",
    },
    "season": {
        "봄": "spring", "여름": "summer", "가을": "autumn", "겨울": "winter",
    },
    "time": {
        "아침": "morning", "오후": "afternoon", "저녁": "evening", "밤": "night", "새벽": "dawn",
    },
    "emotion": {
        "외로움": "lonely", "쓸쓸함": "lonely",
        "우울함": "melancholy",
        "신남": "hyped",
        "설렘": "thrill",
        "차분함": "calm", "잔잔함": "calm",
        "보통": "moderate", "적당함": "moderate",
        "활기참": "energy_hyped",
    },
    "commute": {
        "출근": "to_work", "퇴근": "from_work", "대중교통": "public", "운전": "drive",
    },
    "home": {
        "집안일": "chores", "청소": "chores",
        "요리": "cooking",
        "샤워": "shower",
        "휴식": "rest",
        "잠": "sleep", "수면": "sleep",
    },
    "focus": {
        "공부": "study", "학습": "study",
        "사무실": "office", "업무": "office",
        "마감": "deadline", "데드라인": "deadline",
    },
    "exercise": {
        "헬스": "gym", "운동": "gym",
        "산책": "walk",
        "스트레칭": "stretch", "요가": "stretch",
    },
    "emotion_situation": {
        "이별": "breakup", "위로": "comfort",
        "기분전환": "mood_lift",
        "추억": "nostalgia", "회상": "nostalgia",
    },
    "special": {
        "카페": "cafe", "클럽": "club", "페스티벌": "festival",
        "게임": "gaming", "새벽감성": "dawn_mood", "여행": "travel",
    },
}

# ── 분류 조건 테이블 ─────────────────────────────────────────────────────────
# 각 항목: { 피처명: (min, max) }  ← None = 제한 없음
# 특수 키: "_mode" → 0 or 1 or None
# ─────────────────────────────────────────────────────────────────────────────
CONDITIONS: dict[str, dict[str, dict[str, tuple]]] = {

    # ── 날씨 ────────────────────────────────────────────────────────────────
    "weather": {
        "sunny": {
            "valence":      (0.6,  None),
            "energy":       (0.6,  None),
            "danceability": (0.5,  None),
        },
        "rain": {
            "valence":      (None, 0.4),
            "acousticness": (0.6,  None),
            "energy":       (None, 0.5),
            "_mode":        (0,    0),
        },
        "snow": {
            "acousticness": (0.6,  None),
            "energy":       (None, 0.4),
            "valence":      (0.2,  0.5),
        },
        "cloudy": {
            "valence":      (0.3,  0.6),
            "energy":       (0.3,  0.6),
            "acousticness": (0.4,  None),
        },
    },

    # ── 계절 ────────────────────────────────────────────────────────────────
    "season": {
        "spring": {
            "valence":      (0.6,  None),
            "energy":       (0.4,  0.7),
            "acousticness": (0.4,  None),
            "tempo":        (90,   120),
        },
        "summer": {
            "energy":       (0.7,  None),
            "danceability": (0.6,  None),
            "valence":      (0.6,  None),
            "tempo":        (120,  None),
        },
        "autumn": {
            "valence":      (0.3,  0.5),
            "acousticness": (0.5,  None),
            "_mode":        (0,    0),
        },
        "winter": {
            "acousticness": (0.5,  None),
            "valence":      (None, 0.4),
            "energy":       (None, 0.4),
        },
    },

    # ── 시간대 ──────────────────────────────────────────────────────────────
    "time": {
        "morning": {
            "energy":       (0.5,  0.7),
            "valence":      (0.6,  None),
            "tempo":        (100,  120),
            "_mode":        (1,    1),
        },
        "afternoon": {
            "energy":       (0.5,  0.8),
            "valence":      (0.5,  0.8),
        },
        "evening": {
            "valence":      (0.3,  0.6),
            "acousticness": (0.4,  None),
            "energy":       (None, 0.5),
        },
        "night": {
            "acousticness": (0.5,  None),
            "energy":       (None, 0.4),
            "tempo":        (None, 90),
        },
        "dawn": {
            "instrumentalness": (0.5,  None),
            "energy":           (None, 0.3),
            "loudness":         (None, -10),
        },
    },

    # ── 감정 ────────────────────────────────────────────────────────────────
    "emotion": {
        "lonely": {
            "valence":      (None, 0.3),
            "acousticness": (0.6,  None),
            "_mode":        (0,    0),
        },
        "melancholy": {
            "valence":      (None, 0.3),
            "energy":       (None, 0.4),
            "tempo":        (None, 80),
            "_mode":        (0,    0),
        },
        "hyped": {
            "energy":       (0.8,  None),
            "danceability": (0.7,  None),
            "valence":      (0.7,  None),
            "tempo":        (120,  None),
        },
        "thrill": {
            "valence":      (0.6,  None),
            "energy":       (0.5,  0.7),
            "tempo":        (100,  130),
            "_mode":        (1,    1),
        },
        "calm": {
            "energy":       (None, 0.4),
            "tempo":        (None, 90),
            "acousticness": (0.5,  None),
            "loudness":     (None, -8),
        },
        "moderate": {
            "energy":       (0.4,  0.7),
            "tempo":        (90,   120),
        },
        "energy_hyped": {
            "energy":       (0.7,  None),
            "danceability": (0.7,  None),
            "tempo":        (120,  None),
        },
    },

    # ── 이동 ────────────────────────────────────────────────────────────────
    "commute": {
        "to_work": {
            "energy":       (0.5,  0.7),
            "valence":      (0.5,  None),
            "tempo":        (100,  120),
            "_mode":        (1,    1),
        },
        "from_work": {
            "valence":      (0.3,  0.6),
            "energy":       (None, 0.5),
            "acousticness": (0.3,  None),
        },
        "public": {
            "instrumentalness": (0.4,  None),
            "energy":           (0.3,  0.6),
            "speechiness":      (None, 0.1),
        },
        "drive": {
            "energy":       (0.6,  0.8),
            "tempo":        (110,  140),
            "danceability": (0.6,  None),
            "valence":      (0.5,  None),
        },
    },

    # ── 집 ──────────────────────────────────────────────────────────────────
    "home": {
        "chores": {
            "energy":       (0.5,  0.7),
            "danceability": (0.6,  None),
            "valence":      (0.5,  None),
        },
        "cooking": {
            "valence":      (0.5,  None),
            "tempo":        (100,  130),
            "danceability": (0.5,  0.7),
        },
        "shower": {
            "energy":       (0.6,  None),
            "valence":      (0.6,  None),
        },
        "rest": {
            "acousticness":     (0.5,  None),
            "energy":           (None, 0.4),
            "instrumentalness": (0.3,  None),
        },
        "sleep": {
            "energy":       (None, 0.3),
            "tempo":        (None, 70),
            "acousticness": (0.6,  None),
            "loudness":     (None, -10),
        },
    },

    # ── 집중 ────────────────────────────────────────────────────────────────
    "focus": {
        "study": {
            "instrumentalness": (0.7,  None),
            "speechiness":      (None, 0.05),
            "energy":           (0.3,  0.5),
        },
        "office": {
            "instrumentalness": (0.6,  None),
            "energy":           (0.4,  0.6),
            "tempo":            (90,   120),
        },
        "deadline": {
            "energy":           (0.6,  0.8),
            "tempo":            (120,  None),
            "instrumentalness": (0.5,  None),
        },
    },

    # ── 운동 ────────────────────────────────────────────────────────────────
    "exercise": {
        "gym": {
            "energy":       (0.8,  None),
            "tempo":        (130,  None),
            "danceability": (0.7,  None),
            "loudness":     (-6,   None),
        },
        "walk": {
            "valence":      (0.5,  None),
            "energy":       (0.4,  0.6),
            "tempo":        (90,   110),
        },
        "stretch": {
            "energy":       (None, 0.4),
            "acousticness": (0.5,  None),
            "tempo":        (None, 80),
        },
    },

    # ── 감정 상황 ────────────────────────────────────────────────────────────
    "emotion_situation": {
        "breakup": {
            "valence":      (None, 0.3),
            "acousticness": (0.4,  None),
            "energy":       (None, 0.4),
            "_mode":        (0,    0),
        },
        "comfort": {
            "valence":      (0.3,  0.5),
            "acousticness": (0.5,  None),
            "tempo":        (None, 90),
        },
        "mood_lift": {
            "valence":      (0.6,  None),
            "energy":       (0.6,  None),
            "_mode":        (1,    1),
        },
        "nostalgia": {
            "valence":      (0.4,  0.7),
            "acousticness": (0.4,  None),
        },
    },

    # ── 특수 상황 ────────────────────────────────────────────────────────────
    "special": {
        "cafe": {
            "acousticness":     (0.5,  None),
            "energy":           (0.2,  0.5),
            "instrumentalness": (0.4,  None),
            "tempo":            (70,   100),
        },
        "club": {
            "danceability": (0.8,  None),
            "energy":       (0.8,  None),
            "tempo":        (125,  None),
            "loudness":     (-5,   None),
        },
        "festival": {
            "energy":       (0.8,  None),
            "liveness":     (0.5,  None),
            "danceability": (0.7,  None),
        },
        "gaming": {
            "energy":           (0.6,  0.9),
            "tempo":            (120,  None),
            "instrumentalness": (0.5,  None),
        },
        "dawn_mood": {
            "valence":      (None, 0.4),
            "acousticness": (0.6,  None),
            "energy":       (None, 0.3),
            "_mode":        (0,    0),
        },
        "travel": {
            "valence":      (0.6,  None),
            "energy":       (0.6,  None),
            "danceability": (0.5,  None),
        },
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 2. track_id 추출 함수
# ══════════════════════════════════════════════════════════════════════════════

def get_track_ids(
    df: pd.DataFrame,
    category: str,
    keyword: str,
    top_n: int = 10,
    sort_by: str = "track_popularity",
) -> list[str]:
    """
    DataFrame에서 분류 조건에 맞는 track_id 리스트를 반환한다.

    Parameters
    ----------
    df       : 오디오 피처가 포함된 pandas DataFrame
                (필수 컬럼: track_id, track_popularity, 각 피처)
    category : 분류 카테고리 (예: "weather", "season", ...)
    keyword  : 한글 키워드 (예: "비", "봄", "아침", ...)
    top_n    : 반환할 최대 트랙 수 (기본 10)
    sort_by  : 정렬 기준 컬럼 (기본 "track_popularity")

    Returns
    -------
    list[str]  — track_id 문자열 목록

    Raises
    ------
    ValueError : 지원하지 않는 category 또는 keyword
    """
    if df.empty:
        return []

    # ① alias → English key
    alias_map = _ALIAS.get(category)
    if alias_map is None:
        raise ValueError(
            f"지원하지 않는 카테고리: '{category}'\n"
            f"사용 가능: {list(_ALIAS.keys())}"
        )

    key = alias_map.get(keyword.strip())
    if key is None:
        raise ValueError(
            f"카테고리 '{category}'에서 지원하지 않는 키워드: '{keyword}'\n"
            f"사용 가능: {list(alias_map.keys())}"
        )

    # ② 조건 딕셔너리 조회
    cond_dict = CONDITIONS[category][key]

    # ③ mode 컬럼 이진화
    mode_bin = pd.to_numeric(df.get("mode", pd.Series(dtype=float)), errors="coerce").apply(
        lambda v: 1 if v >= 0.5 else 0 if pd.notna(v) else None
    )

    # ④ 조건 마스크 누적 AND
    mask = pd.Series(True, index=df.index)

    for feat, (lo, hi) in cond_dict.items():
        if feat == "_mode":
            # lo == hi == 원하는 mode 값 (0 or 1)
            mask &= mode_bin == lo
        else:
            col = pd.to_numeric(df.get(feat, pd.Series(dtype=float)), errors="coerce")
            if lo is not None:
                mask &= col >= lo
            if hi is not None:
                mask &= col <= hi

    # ⑤ 필터링 → 정렬 → ID 추출
    result = df[mask].copy()

    if sort_by in result.columns:
        result = result.sort_values(sort_by, ascending=False)

    return result.head(top_n)["track_id"].dropna().astype(str).tolist()


# ══════════════════════════════════════════════════════════════════════════════
# 3. 복수 키워드 처리 (충돌 감지 + 점수 기반 합산)
# ══════════════════════════════════════════════════════════════════════════════

# ── 카테고리 우선순위 (숫자가 낮을수록 우선) ─────────────────────────────────
# 이 상수만 수정하면 우선순위 정책이 바뀜.
CATEGORY_PRIORITY: dict[str, int] = {
    "emotion":           1,
    "emotion_situation": 2,
    "time":              3,
    "focus":             4,
    "exercise":          5,
    "home":              6,
    "commute":           7,
    "special":           8,
    "weather":           9,
    "season":            10,
}


def _get_cond_dict(category: str, keyword: str) -> dict:
    """alias 변환 후 CONDITIONS 딕셔너리를 반환하는 내부 헬퍼."""
    alias_map = _ALIAS.get(category, {})
    key = alias_map.get(keyword.strip())
    if key is None:
        raise ValueError(
            f"카테고리 '{category}'에서 지원하지 않는 키워드: '{keyword}'\n"
            f"사용 가능: {list(alias_map.keys())}"
        )
    return CONDITIONS[category][key]


def _has_conflict(cond_a: dict, cond_b: dict) -> bool:
    """
    두 조건 딕셔너리 사이에 같은 피처의 범위가 겹치지 않으면 True(충돌).

    예) energy: (None, 0.3)  vs  energy: (0.8, None)
        → 상한 0.3 < 하한 0.8  → 겹치는 구간 없음 → 충돌
    """
    shared_feats = set(cond_a) & set(cond_b) - {"_mode"}

    for feat in shared_feats:
        lo_a, hi_a = cond_a[feat]
        lo_b, hi_b = cond_b[feat]

        # 각 범위의 실질적인 하한/상한
        lo_a = lo_a if lo_a is not None else float("-inf")
        hi_a = hi_a if hi_a is not None else float("inf")
        lo_b = lo_b if lo_b is not None else float("-inf")
        hi_b = hi_b if hi_b is not None else float("inf")

        # 겹치는 구간: max(lo) <= min(hi)  →  거짓이면 충돌
        if max(lo_a, lo_b) > min(hi_a, hi_b):
            return True

    # _mode 충돌 검사 (둘 다 지정됐고 값이 다른 경우)
    if "_mode" in cond_a and "_mode" in cond_b:
        if cond_a["_mode"][0] != cond_b["_mode"][0]:
            return True

    return False


def _build_score_mask(df: pd.DataFrame, cond_dict: dict) -> pd.Series:
    """
    단일 조건 딕셔너리를 DataFrame에 적용해 bool 마스크를 반환한다.
    get_track_ids() 내부 로직과 동일하며, 점수 합산 시 재사용된다.
    """
    mode_bin = pd.to_numeric(
        df.get("mode", pd.Series(dtype=float)), errors="coerce"
    ).apply(lambda v: 1 if v >= 0.5 else 0 if pd.notna(v) else None)

    mask = pd.Series(True, index=df.index)
    for feat, (lo, hi) in cond_dict.items():
        if feat == "_mode":
            mask &= mode_bin == lo
        else:
            col = pd.to_numeric(df.get(feat, pd.Series(dtype=float)), errors="coerce")
            if lo is not None:
                mask &= col >= lo
            if hi is not None:
                mask &= col <= hi
    return mask


def get_track_ids_multi(
    df: pd.DataFrame,
    keywords: list[tuple[str, str]],
    top_n: int = 10,
    sort_by: str = "track_popularity",
) -> dict:
    """
    복수 키워드를 받아 충돌 감지 → 점수 기반 합산으로 track_id를 반환한다.

    Parameters
    ----------
    df       : 오디오 피처가 포함된 pandas DataFrame
    keywords : [(category, keyword), ...] 형태의 리스트
                예) [("time", "새벽"), ("exercise", "헬스")]
    top_n    : 반환할 최대 트랙 수
    sort_by  : 동점일 때 2차 정렬 기준 컬럼

    Returns
    -------
    dict {
        "track_ids"    : list[str]             — 추천 track_id 목록
        "applied"      : list[(category, kw)]  — 실제 적용된 키워드
        "dropped"      : list[(category, kw)]  — 충돌로 제외된 키워드
        "conflict"     : bool                  — 충돌 발생 여부
        "score_counts" : dict[str, int]        — track_id별 만족 조건 수
    }

    Raises
    ------
    ValueError : keywords가 비어있거나 지원하지 않는 카테고리/키워드
    """
    if not keywords:
        raise ValueError("keywords가 비어있습니다.")

    if df.empty:
        return {"track_ids": [], "applied": [], "dropped": [], "conflict": False, "score_counts": {}}

    # ── Step 1. 각 키워드의 조건 딕셔너리 로드 ─────────────────────────────
    loaded: list[tuple[str, str, dict]] = []   # (category, keyword, cond_dict)
    for category, keyword in keywords:
        cond_dict = _get_cond_dict(category, keyword)
        loaded.append((category, keyword, cond_dict))

    # ── Step 2. 충돌 감지 → 우선순위 낮은 쪽 제거 ─────────────────────────
    conflict_detected = False
    dropped: list[tuple[str, str]] = []

    # 우선순위 순으로 정렬 (낮은 번호 = 높은 우선순위)
    loaded.sort(key=lambda x: CATEGORY_PRIORITY.get(x[0], 99))

    # 앞에서부터 확정된 조건들과 신규 조건을 비교, 충돌 시 신규를 제거
    confirmed: list[tuple[str, str, dict]] = []
    for cat, kw, cond in loaded:
        conflicted_with = next(
            (c_cat for c_cat, c_kw, c_cond in confirmed if _has_conflict(cond, c_cond)),
            None,
        )
        if conflicted_with:
            conflict_detected = True
            dropped.append((cat, kw))
        else:
            confirmed.append((cat, kw, cond))

    applied = [(cat, kw) for cat, kw, _ in confirmed]

    # ── Step 3. 점수 합산 ────────────────────────────────────────────────────
    score = pd.Series(0, index=df.index, dtype=int)
    for _, _, cond in confirmed:
        score += _build_score_mask(df, cond).astype(int)

    # 점수 0인 트랙 제외
    scored_df = df[score > 0].copy()
    scored_df["_score"] = score[score > 0]

    # 고득점 → sort_by 컬럼 순으로 정렬
    sort_cols = ["_score"]
    if sort_by in scored_df.columns:
        sort_cols.append(sort_by)
    scored_df = scored_df.sort_values(sort_cols, ascending=False)

    result_ids = scored_df.head(top_n)["track_id"].dropna().astype(str).tolist()

    # track_id별 점수 요약
    score_counts = (
        scored_df.head(top_n)
        .set_index("track_id")["_score"]
        .astype(int)
        .to_dict()
    )

    return {
        "track_ids":    result_ids,
        "applied":      applied,
        "dropped":      dropped,
        "conflict":     conflict_detected,
        "score_counts": score_counts,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. 지원 카테고리 / 키워드 조회 헬퍼 (선택)
# ══════════════════════════════════════════════════════════════════════════════

def list_categories() -> list[str]:
    """지원하는 카테고리 목록을 반환한다."""
    return list(_ALIAS.keys())


def list_keywords(category: str) -> list[str]:
    """해당 카테고리에서 사용 가능한 한글 키워드 목록을 반환한다."""
    alias_map = _ALIAS.get(category)
    if alias_map is None:
        raise ValueError(f"지원하지 않는 카테고리: '{category}'")
    return list(alias_map.keys())


def get_condition(category: str, keyword: str) -> dict:
    """
    특정 카테고리/키워드의 분류 조건 딕셔너리를 그대로 반환한다.
    조건을 확인하거나 외부에서 수정할 때 사용.
    """
    alias_map = _ALIAS.get(category)
    if alias_map is None:
        raise ValueError(f"지원하지 않는 카테고리: '{category}'")
    key = alias_map.get(keyword.strip())
    if key is None:
        raise ValueError(f"카테고리 '{category}'에서 지원하지 않는 키워드: '{keyword}'")
    return CONDITIONS[category][key]


########################################################
# 음악 데이터 분류를 컬럼으로 추가하는 함수 by 김경수
########################################################
def build_music_catalog_labels_df(
    df: pd.DataFrame,
    *,
    tag_sep: str = ";",
) -> pd.DataFrame:
    """
    `music_catalog` 피처가 담긴 DataFrame에서 트랙별로 카테고리 라벨 키를 집계한다.

    - 행: 입력과 동일한 순서의 `track_id`
    - 열: `CATEGORY_PRIORITY`에 등장하는 카테고리명을 우선순위(값이 작을수록 앞) 순으로 배치
    - 셀: 해당 카테고리의 `CONDITIONS` 영문 키 중 조건을 만족하는 것만 모아 `tag_sep`로 이어붙임
          (예: home 열 → ``chores`` 또는 ``chores;cooking``). 하나도 없으면 빈 문자열.
    """
    categories_ordered = sorted(CATEGORY_PRIORITY.keys(), key=lambda c: CATEGORY_PRIORITY[c])

    if df.empty:
        return pd.DataFrame(columns=["track_id", *categories_ordered])

    work = df.reset_index(drop=True)
    n = len(work)
    out: dict[str, object] = {"track_id": work["track_id"].dropna().astype(str).tolist()}

    for cat in categories_ordered:
        buckets: list[set[str]] = [set() for _ in range(n)]
        for eng_key, cond_dict in CONDITIONS[cat].items():
            mask = _build_score_mask(work, cond_dict)
            for pos, ok in enumerate(mask.tolist()):
                if ok:
                    buckets[pos].add(eng_key)
        out[cat] = [tag_sep.join(sorted(s)) if s else "" for s in buckets]

    return pd.DataFrame(out)


if __name__ == "__main__":
    ########################################################
    # 실행 시 음악 데이터 읽어서 분류로 추출 
    ########################################################
    _DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    _catalog_csv = _DATA_DIR / "music_catalog.csv"
    _out_csv = _DATA_DIR / "music_catalog_scenarios.csv"

    df_catalog = pd.read_csv(_catalog_csv)
    df_labels = build_music_catalog_labels_df(df_catalog)
    df_labels.to_csv(_out_csv, index=False)
