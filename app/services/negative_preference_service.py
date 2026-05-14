class NegativePreferenceService:
    def __init__(self, repository=None):
        self._repository = repository

    def merge_and_save(
        self,
        *,
        user_id: str,
        existing_artists: list[str],
        existing_tracks: list[str],
        new_artists: list[str],
        new_tracks: list[str],
    ) -> dict:
        disliked_artists = _merge_unique(new_artists, existing_artists, limit=50)
        disliked_tracks = _merge_unique(new_tracks, existing_tracks, limit=50)
        if self._repository and (new_artists or new_tracks):
            self._repository.upsert(
                user_id=user_id,
                disliked_artists=disliked_artists,
                disliked_tracks=disliked_tracks,
            )
        return {
            "disliked_artists": disliked_artists,
            "disliked_tracks": disliked_tracks,
        }


def _merge_unique(new_items: list[str], existing_items: list[str], limit: int) -> list[str]:
    merged = []
    seen = set()
    for value in list(new_items) + list(existing_items):
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            merged.append(text)
    return merged[:limit]
