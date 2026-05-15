from app.common.constants import ALLOWED_GENRES, ALLOWED_INTENT_TYPES, ALLOWED_MOODS, ALLOWED_SITUATIONS

SYSTEM_PROMPT = """\
당신은 음악 추천 시스템의 입력 분류기입니다.
사용자의 입력과 세션 컨텍스트를 분석하여 JSON으로만 응답합니다.

## 규칙
- intent_type은 반드시 허용 값 중 하나여야 합니다.
- detected_moods, detected_genres, detected_situations는 허용 값 목록에 있는 것만 포함합니다.
- 해당 없으면 빈 배열로 반환합니다.
- normalized_query는 사용자 입력을 검색에 적합한 짧은 문장으로 정규화합니다.
- confidence는 0.0~1.0 사이의 float입니다.
- 절대로 content_id, title, artist, KAG_STATE, RAG_STATE를 생성하지 않습니다.
- 부정 장르는 disliked_genres에 넣고, 부정 아티스트/곡과 분리합니다.

## 허용 값
intent_type: {intent_types}
detected_moods: {moods}
detected_genres: {genres}
detected_situations: {situations}
""".format(
    intent_types=", ".join(sorted(ALLOWED_INTENT_TYPES)),
    moods=", ".join(sorted(ALLOWED_MOODS)),
    genres=", ".join(sorted(ALLOWED_GENRES)),
    situations=", ".join(sorted(ALLOWED_SITUATIONS)),
)

OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "intent_type": {"type": "string", "enum": sorted(ALLOWED_INTENT_TYPES)},
        "confidence": {"type": "number"},
        "normalized_query": {"type": "string"},
        "detected_moods": {"type": "array", "items": {"type": "string", "enum": sorted(ALLOWED_MOODS)}},
        "detected_genres": {"type": "array", "items": {"type": "string", "enum": sorted(ALLOWED_GENRES)}},
        "detected_situations": {
            "type": "array",
            "items": {"type": "string", "enum": sorted(ALLOWED_SITUATIONS)},
        },
        "requested_count": {"type": ["integer", "null"], "minimum": 1},
        "disliked_artists": {"type": "array", "items": {"type": "string"}},
        "disliked_tracks": {"type": "array", "items": {"type": "string"}},
        "disliked_genres": {"type": "array", "items": {"type": "string", "enum": sorted(ALLOWED_GENRES)}},
    },
    "required": [
        "intent_type",
        "confidence",
        "normalized_query",
        "detected_moods",
        "detected_genres",
        "detected_situations",
        "requested_count",
        "disliked_artists",
        "disliked_tracks",
        "disliked_genres",
    ],
    "additionalProperties": False,
}
