class RagStateBuilder:
    """RAG_STATE JSON 계약을 조립하는 순수 빌더."""

    @staticmethod
    def build(
        context_type: str,
        base_context: str,
        source_type: str,
        evidence: list[dict],
        reason_summary: str,
        reason_items: list[str],
        information_evidence: list[dict] | None = None,
        scripts: dict | None = None,
        query: str = "",
        normalized_query: str = "",
        retrieval_metadata: dict | None = None,
        retrieval_trace: dict | None = None,
    ) -> dict:
        return {
            "status": "success",
            "query": query,
            "normalized_query": normalized_query,
            "recommendation_context": {
                "context_type": context_type,
                "base_context": base_context,
                "source_type": source_type,
            },
            "recommended_content_evidence": evidence,
            "recommendation_reason": {
                "summary": reason_summary,
                "reason_items": reason_items,
            },
            "information_evidence": information_evidence or [],
            "retrieval_metadata": retrieval_metadata or {},
            "retrieval_trace": retrieval_trace or {},
            "recommendation_scripts": scripts or {
                "dj_intro": "기존에 좋아하던 분위기는 유지하면서 조금 새로운 결의 음악을 골라봤어요.",
                "personalized_message": "먼저 익숙하게 들을 수 있는 곡을 추천할게요.",
                "new_release_message": "최근 업데이트된 곡 중에서도 취향과 연결되는 곡을 함께 넣었어요.",
                "discovery_message": "새로운 취향을 시도하고 싶다면 이 곡부터 시작해볼 수 있어요.",
                "fallback_message": "지금은 충분한 추천 근거가 부족해 기본 안내만 제공할게요.",
            },
        }

    @staticmethod
    def failure(reason: str) -> dict:
        return {
            "status": "error",
            "query": "",
            "normalized_query": "",
            "error_reason": reason,
            "recommended_content_evidence": [],
            "recommendation_reason": {"summary": "", "reason_items": []},
            "information_evidence": [],
            "retrieval_metadata": {},
            "retrieval_trace": {},
            "recommendation_scripts": {},
        }
