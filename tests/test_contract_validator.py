from app.validators.contract_validator import ContractValidator


def test_contract_validator_accepts_minimal_docs_contracts():
    validator = ContractValidator()

    result = validator.validate_all(
        ml_output={
            "status": "success",
            "user_id": "user_001",
            "taste_profile": {},
            "behavior_profile": {},
            "recommendation_profile": {},
        },
        kag_state={
            "status": "success",
            "user": {"user_id": "user_001"},
            "recommendation_goal": {},
            "user_context": {},
            "curation_intent": {},
            "curation_strategy": {},
            "content_requirements": {},
            "routing": {},
            "selected_path": "personalized_to_safe_discovery",
        },
        rag_state={
            "status": "success",
            "recommendation_context": {},
            "recommended_content_evidence": [],
            "recommendation_reason": {},
            "recommendation_scripts": {},
        },
    )

    assert result["passed"] is True
    assert result["errors"] == []


def test_contract_validator_rejects_missing_required_fields():
    result = ContractValidator().validate_kag({"status": "success"})

    assert result["passed"] is False
    assert "user" in result["errors"][0]
