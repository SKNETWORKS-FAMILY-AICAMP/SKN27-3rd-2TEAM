from app.schemas.music_detail_schema import MusicDetailViewModelSchema


class MusicDetailService:
    """최근 RAG_STATE를 우선 사용해 Music Detail ViewModel을 만든다."""

    def get_detail(self, content_id: str, recent_rag_state: dict | None = None) -> dict:
        evidence = self._find_rag_evidence(content_id, recent_rag_state or {})
        if evidence:
            return self._from_rag_evidence(evidence).model_dump()

        return MusicDetailViewModelSchema(
            content_id=content_id,
            title="",
            artist="",
            display_reason="",
            evidence_summary="",
            source="music_catalog",
        ).model_dump()

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
            display_reason=evidence.get("display_reason") or evidence.get("evidence_summary", ""),
            evidence_summary=evidence.get("evidence_summary", ""),
            source="rag_state",
        )
