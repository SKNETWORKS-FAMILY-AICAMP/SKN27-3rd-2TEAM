from app.validators.contract_validator import ContractValidator


def _session_context():
    return {
        "session_id": "session_001",
        "recent_genres": [],
        "recent_artists": [],
        "recent_moods": [],
        "conversation_summary": "",
    }


def _minimal_kag_state():
    return {
        "status": "success",
        "recommendation_goal": {"primary_goal": "discovery_recommendation"},
        "recommended_content_ids": ["track_001"],
        "recommendation_category": "discovery_candidate",
        "route": "safe_discovery",
        "target_section": "discovery_section",
    }


def _minimal_rag_state():
    return {
        "status": "success",
        "recommended_content_evidence": [
            {
                "content_id": "track_001",
                "title": "Midnight Loop",
                "artist": "Nova Lane",
                "genre": ["indie"],
                "mood": ["night"],
                "evidence_summary": "차분한 밤 분위기와 연결되는 곡",
            }
        ],
        "recommendation_reason": {
            "summary": "사용자의 최근 선호 분위기와 연결되는 곡",
        },
    }


def test_contract_validator_accepts_v3_runtime_contracts():
    result = ContractValidator().validate(
        session_context=_session_context(),
        kag_state=_minimal_kag_state(),
        rag_state=_minimal_rag_state(),
    )

    assert result["passed"] is True
    assert result["errors"] == []


def test_contract_validator_rejects_missing_session_id():
    result = ContractValidator().validate(
        session_context={},
        kag_state=_minimal_kag_state(),
        rag_state=_minimal_rag_state(),
    )

    assert result["passed"] is False
    assert any("session_id" in e for e in result["errors"])


def test_contract_validator_rejects_missing_v3_kag_route():
    kag_state = _minimal_kag_state()
    kag_state.pop("route")

    result = ContractValidator().validate(
        session_context=_session_context(),
        kag_state=kag_state,
        rag_state=_minimal_rag_state(),
    )

    assert result["passed"] is False
    assert any("route" in error for error in result["errors"])


def test_contract_validator_rejects_missing_v3_rag_evidence():
    rag_state = _minimal_rag_state()
    rag_state.pop("recommended_content_evidence")

    result = ContractValidator().validate(
        session_context=_session_context(),
        kag_state=_minimal_kag_state(),
        rag_state=rag_state,
    )

    assert result["passed"] is False
    assert any("recommended_content_evidence" in error for error in result["errors"])


def test_contract_validator_rejects_invalid_kag_status():
    kag = _minimal_kag_state()
    kag["status"] = "unknown"

    result = ContractValidator().validate(
        session_context=_session_context(),
        kag_state=kag,
        rag_state=_minimal_rag_state(),
    )

    assert result["passed"] is False
