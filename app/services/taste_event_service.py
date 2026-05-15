import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.cache import session_history_cache as _default_cache
from app.common.list_utils import merge_unique

logger = logging.getLogger("rimas.service.taste_event")


class TasteEventService:
    def __init__(self, detail_service=None, session_cache=None):
        self._detail_service = detail_service
        self._cache = session_cache or _default_cache

    def add_to_taste(
        self,
        *,
        user_id: str,
        session_id: str,
        content_id: str,
        source: str,
    ) -> dict:
        if not user_id:
            raise ValueError("user_id is required")
        if not session_id:
            raise ValueError("session_id is required")
        if not content_id:
            raise ValueError("content_id is required")

        detail = {}
        if self._detail_service:
            detail = self._detail_service.get_detail(content_id) or {}

        genre = detail.get("genre", [])
        mood = detail.get("mood", [])
        artist = detail.get("artist", "")
        title = detail.get("title", "")
        recommendation_category = detail.get("recommendation_category", "")

        ctx = self._update_context(
            session_id=session_id,
            genre=genre,
            mood=mood,
            artist=artist,
            content_id=content_id,
        )

        event = {
            "event_id": f"evt_{uuid4().hex}",
            "user_id": user_id,
            "session_id": session_id,
            "content_id": content_id,
            "event_type": "add_to_taste",
            "source": source,
            "title": title,
            "artist": artist,
            "genre": genre,
            "mood": mood,
            "recommendation_category": recommendation_category,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._cache.append_taste_event(session_id, event)

        logger.info("taste_event_added", extra={"user_id": user_id, "content_id": content_id})
        return {"status": "success", "session_context": ctx}

    def _update_context(
        self,
        *,
        session_id: str,
        genre: list,
        mood: list,
        artist: str,
        content_id: str,
    ) -> dict:
        if hasattr(self._cache, "update_context_from_taste"):
            return self._cache.update_context_from_taste(
                session_id,
                genre=genre,
                mood=mood,
                artist=artist,
                content_id=content_id,
            )

        ctx = self._cache.get_context(session_id)
        ctx["recent_genres"] = merge_unique(genre, ctx.get("recent_genres", []), limit=5)
        ctx["recent_moods"] = merge_unique(mood, ctx.get("recent_moods", []), limit=5)
        ctx["recent_artists"] = merge_unique(
            [artist] if artist else [],
            ctx.get("recent_artists", []),
            limit=5,
        )
        ctx["selected_tracks"] = merge_unique([content_id], ctx.get("selected_tracks", []), limit=50)
        self._cache.set_context(session_id, ctx)
        return ctx


