from typing import get_args

from app.schemas.intent_state_schema import IntentType

DEFAULT_USER_ID = "user_001"

ALLOWED_STATUSES = {"success", "partial_match", "empty_result", "timeout", "error"}

# IntentType Literal에서 파생 — 두 곳에서 별도 관리하지 않는다.
ALLOWED_INTENT_TYPES: frozenset[str] = frozenset(get_args(IntentType))

ALLOWED_MOODS = {"calm", "night", "bright", "clean"}
ALLOWED_GENRES = {"indie", "dream_pop", "ambient", "rnb", "electro_pop"}
ALLOWED_SITUATIONS = {"late_night"}

MOOD_KEYWORD_MAP: dict[str, list[str]] = {
    "calm": ["calm", "잔잔", "차분"],
    "night": ["night", "밤", "야간"],
    "bright": ["bright", "밝은"],
    "clean": ["clean", "깔끔"],
}

GENRE_KEYWORD_MAP: dict[str, list[str]] = {
    "indie": ["indie", "인디"],
    "dream_pop": ["dream pop", "드림팝"],
    "ambient": ["ambient", "앰비언트"],
    "rnb": ["rnb", "알앤비"],
    "electro_pop": ["electro pop", "일렉트로"],
}
