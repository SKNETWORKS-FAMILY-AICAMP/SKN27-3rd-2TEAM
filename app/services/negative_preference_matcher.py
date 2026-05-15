class NegativePreferenceMatcher:
    def __init__(self, music_catalog_repository):
        self._music_catalog_repository = music_catalog_repository

    def resolve(self, value: str) -> dict:
        text = (value or "").strip()
        if not text:
            return _empty_result()

        rows = self._music_catalog_repository.find_identity_matches(text)
        normalized = _normalize(text)

        artists = []
        for row in rows:
            artist = str(row.get("artist") or "").strip()
            if artist and _normalize(artist) == normalized:
                artists.append(artist)

        if artists:
            return {"disliked_artists": _dedupe(artists), "disliked_tracks": []}

        tracks = []
        for row in rows:
            title = str(row.get("title") or "").strip()
            content_id = str(row.get("content_id") or "").strip()
            if title and content_id and _normalize(title) == normalized:
                tracks.append(content_id)

        return {"disliked_artists": [], "disliked_tracks": _dedupe(tracks)}


def _empty_result() -> dict:
    return {"disliked_artists": [], "disliked_tracks": []}


def _normalize(value: str) -> str:
    return " ".join(str(value or "").casefold().split())


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
