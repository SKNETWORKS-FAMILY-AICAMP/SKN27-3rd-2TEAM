import json
import unittest
from pathlib import Path


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "app" / "json_templates"

EXPECTED_TEMPLATE_FIELDS = {
    "ml_output_template.json": {
        "status",
        "user_id",
        "taste_profile",
        "behavior_profile",
        "recommendation_profile",
    },
    "kag_state_template.json": {
        "status",
        "user",
        "recommendation_goal",
        "user_context",
        "curation_intent",
        "curation_strategy",
        "content_requirements",
        "routing",
        "selected_path",
    },
    "rag_state_template.json": {
        "status",
        "recommendation_context",
        "recommended_content_evidence",
        "recommendation_reason",
        "information_evidence",
        "recommendation_scripts",
    },
    "intent_result_template.json": {
        "status",
        "intent_type",
        "confidence",
        "target_content_id",
        "requires_recommendation",
        "requires_information",
    },
    "curation_plan_template.json": {
        "status",
        "curation_mode",
        "response_focus",
        "tone",
        "allowed_content_ids",
        "primary_content_id",
        "use_information_evidence",
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
        "provenance",
        "validation",
    },
    "interaction_log_template.json": {
        "log_id",
        "user_id",
        "user_input",
        "ml_output",
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

        self.assertEqual(set(template["user"].keys()), {"user_id"})
        self.assertEqual(
            set(template["content_requirements"].keys()),
            {"must_include", "optional_include", "avoid"},
        )
        self.assertEqual(
            set(template["routing"].keys()),
            {"target_page", "primary_section", "secondary_sections"},
        )

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
                "tempo",
                "release_type",
                "recommendation_category",
                "evidence_summary",
                "match_reason",
            },
        )

    def _load_template(self, filename):
        with (TEMPLATE_DIR / filename).open(encoding="utf-8") as template_file:
            return json.load(template_file)


if __name__ == "__main__":
    unittest.main()
