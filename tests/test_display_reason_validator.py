from app.validators.display_reason_validator import DisplayReasonValidator


def test_display_reason_validator_rejects_raw_evidence_copy():
    result = DisplayReasonValidator().validate(
        display_reason="raw lyrics line raw lyrics line",
        source_item={"evidence_summary": "raw lyrics line raw lyrics line", "title": "Song", "artist": "Artist"},
    )

    assert not result["passed"]


def test_display_reason_validator_accepts_short_metadata_based_reason():
    result = DisplayReasonValidator().validate(
        display_reason="indie 취향과 calm 분위기에 맞춰 고른 곡입니다.",
        source_item={"evidence_summary": "very long raw document", "title": "Song", "artist": "Artist"},
    )

    assert result["passed"]
