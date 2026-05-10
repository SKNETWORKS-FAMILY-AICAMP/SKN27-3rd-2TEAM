import unittest
from enum import StrEnum
from pathlib import Path


CONTRACTS_DIR = Path(__file__).resolve().parents[1] / "app" / "contracts"

DEPRECATED_EMPTY_EXAMPLE_FILES = {
    "ml_output_example.json",
    "kag_state_example.json",
    "rag_state_example.json",
    "intent_result_example.json",
    "curation_plan_example.json",
    "selected_recommendations_example.json",
    "response_state_example.json",
    "interaction_log_example.json",
}


class ContractEnumTest(unittest.TestCase):
    def test_deprecated_empty_contract_examples_are_removed(self):
        existing_files = {
            path.name
            for path in CONTRACTS_DIR.glob("*_example.json")
            if path.stat().st_size == 0
        }

        self.assertFalse(existing_files & DEPRECATED_EMPTY_EXAMPLE_FILES)

    def test_contract_field_enums_are_string_enums(self):
        from app.contracts.fields import (
            CommonField,
            RecommendationField,
            SelectedRecommendationsField,
        )

        self.assertTrue(issubclass(CommonField, StrEnum))
        self.assertEqual(CommonField.STATUS, "status")
        self.assertEqual(
            SelectedRecommendationsField.SELECTED_RECOMMENDATIONS,
            "selected_recommendations",
        )
        self.assertEqual(RecommendationField.CONTENT_ID, "content_id")
        self.assertEqual(
            RecommendationField.RECOMMENDATION_CATEGORY,
            "recommendation_category",
        )

    def test_allowed_statuses_contain_documented_values(self):
        from app.common.constants import ALLOWED_STATUSES

        self.assertIn("success", ALLOWED_STATUSES)
        self.assertIn("error", ALLOWED_STATUSES)
        self.assertIn("partial_match", ALLOWED_STATUSES)
        self.assertIn("empty_result", ALLOWED_STATUSES)
        self.assertIn("timeout", ALLOWED_STATUSES)


if __name__ == "__main__":
    unittest.main()
