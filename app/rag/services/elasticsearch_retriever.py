from dataclasses import dataclass
from typing import Any

from app.config import settings

CONTENT_ID_KEYWORD_FIELDS = (
    "content_id",
    "content_id.keyword",
    "track_id",
    "track_id.keyword",
    "metadata.content_id",
    "metadata.content_id.keyword",
    "metadata.track_id",
    "metadata.track_id.keyword",
    "metadata.doc_id",
    "metadata.doc_id.keyword",
)


@dataclass(frozen=True)
class ElasticsearchRagHit:
    content_id: str
    title: str
    artist: str
    album: str | None
    genre: list[str]
    mood: list[str]
    content: str
    score: float
    release_type: str = "existing_catalog"


class ElasticsearchRagRetriever:
    """Elasticsearch retriever boundary for KAG candidate-scoped RAG evidence."""

    def __init__(self, client=None, index_name: str | None = None):
        self._client = client
        self._index_name = index_name or settings.RIMAS_ELASTICSEARCH_INDEX

    def search(
        self,
        *,
        query_text: str,
        content_ids: list[str],
        max_evidence_per_track: int,
    ) -> list[ElasticsearchRagHit]:
        if not content_ids:
            return []

        client = self._client or self._build_client()
        if not client.indices.exists(index=self._index_name):
            raise RuntimeError(f"elasticsearch index not found: {self._index_name}")

        response = client.search(
            index=self._index_name,
            body=self._build_query(query_text, content_ids, max_evidence_per_track),
        )
        return self._map_hits(response.get("hits", {}).get("hits", []), set(content_ids))

    @staticmethod
    def _build_client():
        try:
            from elasticsearch import Elasticsearch
        except ImportError as exc:
            raise RuntimeError("elasticsearch package is required for Real RAG") from exc

        return Elasticsearch(
            settings.RIMAS_ELASTICSEARCH_URL,
            request_timeout=settings.RIMAS_ELASTICSEARCH_TIMEOUT,
        )

    @staticmethod
    def _build_query(query_text: str, content_ids: list[str], max_evidence_per_track: int) -> dict:
        size = max(1, len(content_ids) * max_evidence_per_track)
        return {
            "size": size,
            "query": {
                "bool": {
                    "filter": [
                        ElasticsearchRagRetriever._build_content_id_filter(content_ids)
                    ],
                    "should": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": [
                                    "content^2",
                                    "text",
                                    "metadata.text",
                                    "metadata.song",
                                    "metadata.track_name",
                                    "metadata.artist",
                                    "metadata.track_artist",
                                    "metadata.genre",
                                    "metadata.emotion",
                                ],
                            }
                        }
                    ],
                    "minimum_should_match": 0,
                }
            },
        }

    @staticmethod
    def _build_content_id_filter(content_ids: list[str]) -> dict:
        return {
            "bool": {
                "should": [
                    {"terms": {field: content_ids}}
                    for field in CONTENT_ID_KEYWORD_FIELDS
                ],
                "minimum_should_match": 1,
            }
        }

    def _map_hits(self, hits: list[dict[str, Any]], allowed_ids: set[str]) -> list[ElasticsearchRagHit]:
        mapped = []
        for hit in hits:
            source = hit.get("_source", {})
            metadata = source.get("metadata", {}) or {}
            content_id = self._first_text(
                source.get("content_id"),
                source.get("track_id"),
                metadata.get("content_id"),
                metadata.get("track_id"),
                metadata.get("doc_id"),
            )
            if not content_id or content_id not in allowed_ids:
                continue
            mapped.append(
                ElasticsearchRagHit(
                    content_id=content_id,
                    title=self._first_text(
                        source.get("title"),
                        source.get("song"),
                        source.get("track_name"),
                        metadata.get("title"),
                        metadata.get("song"),
                        metadata.get("track_name"),
                    ),
                    artist=self._first_text(
                        source.get("artist"),
                        source.get("track_artist"),
                        metadata.get("artist"),
                        metadata.get("track_artist"),
                        metadata.get("Artist(s)"),
                    ),
                    album=self._first_text(
                        source.get("album"),
                        source.get("track_album_name"),
                        metadata.get("album"),
                        metadata.get("Album"),
                        metadata.get("track_album_name"),
                    ),
                    genre=self._list_value(
                        source.get("genre"),
                        source.get("playlist_genre"),
                        metadata.get("genre"),
                        metadata.get("Genre"),
                        metadata.get("playlist_genre"),
                    ),
                    mood=self._list_value(
                        source.get("mood"),
                        source.get("emotion"),
                        metadata.get("mood"),
                        metadata.get("emotion"),
                    ),
                    content=self._first_text(source.get("content"), source.get("text"), metadata.get("text")),
                    score=float(hit.get("_score") or 0),
                    release_type=self._first_text(source.get("release_type"), metadata.get("release_type"))
                    or "existing_catalog",
                )
            )
        return mapped

    @staticmethod
    def _first_text(*values) -> str:
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    @staticmethod
    def _list_value(*values) -> list[str]:
        for value in values:
            if value is None:
                continue
            if isinstance(value, list):
                return [str(item) for item in value if str(item).strip()]
            text = str(value).strip()
            if text:
                return [text]
        return []
