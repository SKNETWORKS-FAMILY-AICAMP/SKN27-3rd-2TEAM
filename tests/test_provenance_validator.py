from app.validators.provenance_validator import ProvenanceValidator


def test_provenance_validator_rejects_content_id_not_in_rag_state():
    rag_state = {
        "recommended_content_evidence": [
            {"content_id": "track_001", "title": "Midnight Loop", "artist": "Nova Lane"}
        ]
    }
    response_state = {
        "used_content_ids": ["track_999"],
        "display_recommendations": [],
    }

    result = ProvenanceValidator().validate(response_state, rag_state)

    assert result["passed"] is False
    assert "track_999" in result["errors"][0]


def test_provenance_validator_accepts_titles_and_artists_from_rag_state():
    rag_state = {
        "recommended_content_evidence": [
            {"content_id": "track_001", "title": "Midnight Loop", "artist": "Nova Lane"}
        ]
    }
    response_state = {
        "used_content_ids": ["track_001"],
        "display_recommendations": [
            {"content_id": "track_001", "title": "Midnight Loop", "artist": "Nova Lane"}
        ],
    }

    result = ProvenanceValidator().validate(response_state, rag_state)

    assert result["passed"] is True
