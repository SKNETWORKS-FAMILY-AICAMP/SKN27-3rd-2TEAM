import json
import unittest
from pathlib import Path


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "app" / "json_templates"

EXPECTED_TEMPLATE_FIELDS = {
    "kag_state_template.json": {
        "status",
        "recommendation_goal",
        "recommended_content_ids",
        "recommendation_category",
        "route",
        "target_section",
    },
    "rag_state_template.json": {
        "status",
        "recommended_content_evidence",
        "recommendation_reason",
    },
    "intent_result_template.json": {
        "status",
        "intent_type",
        "confidence",
        "target_content_id",
        "requires_recommendation",
        "requires_information",
    },
    "selected_recommendations_template.json": {
        "status",
        "selected_recommendations",
    },
    "response_state_template.json": {
        "status",
        "response_type",
        "chatbot_response",
        "display_recommendations",
        "used_content_ids",
    },
    "interaction_log_template.json": {
        "log_id",
        "user_id",
        "session_id",
        "user_input",
        "session_context",
        "kag_state",
        "rag_state",
        "response_state",
        "validation_status",
        "error_type",
        "latency_ms",
        "created_at",
    },
}


class JsonTemplateTest(unittest.TestCase):
    def test_all_template_files_exist_and_have_required_top_level_fields(self):
        for filename, required_fields in EXPECTED_TEMPLATE_FIELDS.items():
            with self.subTest(filename=filename):
                template_path = TEMPLATE_DIR / filename

                with template_path.open(encoding="utf-8") as template_file:
                    template = json.load(template_file)

                self.assertEqual(set(template.keys()), required_fields)

    def test_kag_template_has_required_nested_sections(self):
        template = self._load_template("kag_state_template.json")

        self.assertEqual(set(template["recommendation_goal"].keys()), {"primary_goal"})
        self.assertIsInstance(template["recommended_content_ids"], list)
        self.assertEqual(template["route"], "safe_discovery")

    def test_rag_template_has_content_evidence_shape(self):
        template = self._load_template("rag_state_template.json")
        evidence = template["recommended_content_evidence"][0]

        self.assertEqual(
            set(evidence.keys()),
            {
                "content_id",
                "title",
                "artist",
                "album",
                "genre",
                "mood",
                "evidence_summary",
            },
        )

    def _load_template(self, filename):
        with (TEMPLATE_DIR / filename).open(encoding="utf-8") as template_file:
            return json.load(template_file)


if __name__ == "__main__":
    unittest.main()
