from app.validators.base_validator import BaseValidator


class ProvenanceValidator(BaseValidator):
    def validate(self, response_state, rag_state):
        rag_items = {
            item.get("content_id"): item
            for item in rag_state.get("recommended_content_evidence", [])
        }

        for content_id in response_state.get("used_content_ids", []):
            if content_id not in rag_items:
                return {
                    "passed": False,
                    "errors": [f"{content_id} is not present in RAG_STATE"],
                }

        for recommendation in response_state.get("display_recommendations", []):
            content_id = recommendation.get("content_id")
            rag_item = rag_items.get(content_id)
            if rag_item is None:
                return {
                    "passed": False,
                    "errors": [f"{content_id} is not present in RAG_STATE"],
                }
            if recommendation.get("title") != rag_item.get("title"):
                return {
                    "passed": False,
                    "errors": [f"{content_id} title does not match RAG_STATE"],
                }
            if recommendation.get("artist") != rag_item.get("artist"):
                return {
                    "passed": False,
                    "errors": [f"{content_id} artist does not match RAG_STATE"],
                }

        return {"passed": True, "errors": []}
