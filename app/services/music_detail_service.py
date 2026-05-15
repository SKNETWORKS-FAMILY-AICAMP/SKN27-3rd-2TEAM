from app.agents.recommendation_agent import build_display_reason
from app.schemas.music_detail_schema import MusicDetailViewModelSchema
from app.validators.display_reason_validator import DisplayReasonValidator


class MusicDetailService:
    """최근 RAG_STATE를 우선 사용해 Music Detail ViewModel을 만든다."""

    def __init__(self, music_catalog_repository=None):
        self._music_catalog_repository = music_catalog_repository

    def get_detail(self, content_id: str, recent_rag_state: dict | None = None) -> dict:
        evidence = self._find_rag_evidence(content_id, recent_rag_state or {})
        if evidence:
            return self._from_rag_evidence(evidence).model_dump()

        catalog_item = self._find_catalog_item(content_id)
        if catalog_item:
            return self._from_catalog_item(catalog_item).model_dump()

        return MusicDetailViewModelSchema(
            content_id=content_id,
            title="",
            artist="",
            display_reason="",
            evidence_summary="",
            source="music_catalog",
        ).model_dump()

    def _find_catalog_item(self, content_id: str) -> dict | None:
        if self._music_catalog_repository is None:
            return None
        return self._music_catalog_repository.find_by_content_id(content_id)

    @staticmethod
    def _find_rag_evidence(content_id: str, rag_state: dict) -> dict | None:
        for item in rag_state.get("recommended_content_evidence", []):
            if item.get("content_id") == content_id:
                return item
        return None

    @staticmethod
    def _from_rag_evidence(evidence: dict) -> MusicDetailViewModelSchema:
        return MusicDetailViewModelSchema(
            content_id=evidence["content_id"],
            title=evidence.get("title", ""),
            artist=evidence.get("artist", ""),
            album=evidence.get("album"),
            genre=evidence.get("genre", []),
            mood=evidence.get("mood", []),
            display_reason=_safe_display_reason(evidence),
            evidence_summary=evidence.get("evidence_summary", ""),
            source="rag_state",
        )

    @staticmethod
    def _from_catalog_item(item: dict) -> MusicDetailViewModelSchema:
        return MusicDetailViewModelSchema(
            content_id=item["content_id"],
            title=item.get("title", ""),
            artist=item.get("artist", ""),
            album=item.get("album"),
            genre=item.get("genres", []),
            mood=item.get("moods", []),
            display_reason=_safe_display_reason({
                **item,
                "genre": item.get("genres", []),
                "mood": item.get("moods", []),
                "recommendation_category": item.get("recommendation_category", "personalized_match"),
            }),
            evidence_summary=item.get("evidence_summary", ""),
            source="music_catalog",
        )


def _safe_display_reason(item: dict) -> str:
    reason = item.get("display_reason", "")
    if DisplayReasonValidator().validate(reason, item).get("passed"):
        return reason
    return build_display_reason(item)
