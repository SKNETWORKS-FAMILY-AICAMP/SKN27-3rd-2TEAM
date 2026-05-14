class DisplayReasonValidator:
    def validate(self, display_reason: str, source_item: dict) -> dict:
        reason = (display_reason or "").strip()
        if not reason:
            return {"passed": False, "errors": ["display_reason is empty"]}
        if len(reason) > 160:
            return {"passed": False, "errors": ["display_reason is too long"]}

        raw = str(source_item.get("evidence_summary") or "").strip()
        if raw and reason == raw:
            return {"passed": False, "errors": ["display_reason copies evidence_summary"]}
        if raw and len(raw) >= 20 and raw[:40] in reason:
            return {"passed": False, "errors": ["display_reason includes raw evidence"]}

        return {"passed": True, "errors": []}
