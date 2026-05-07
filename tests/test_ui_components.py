import unittest

from app.ui.components.developer_debug_panel import render_developer_debug_panel
from app.ui.components.recommendation_card_section import (
    render_recommendation_card_section,
)


class FakeRenderer:
    def __init__(self):
        self.calls = []

    def subheader(self, value):
        self.calls.append(("subheader", value))

    def markdown(self, value, unsafe_allow_html=False):
        self.calls.append(("markdown", value, unsafe_allow_html))

    def json(self, value):
        self.calls.append(("json", value))

    def caption(self, value):
        self.calls.append(("caption", value))


class UiComponentTest(unittest.TestCase):
    def test_recommendation_section_renders_card_titles(self):
        renderer = FakeRenderer()

        render_recommendation_card_section(
            renderer,
            "개인화 추천",
            [
                {
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "display_reason": "기존 취향과 연결되는 곡",
                    "genre": ["rnb", "indie"],
                    "mood": ["calm"],
                }
            ],
        )

        rendered_text = " ".join(str(call) for call in renderer.calls)
        self.assertIn("개인화 추천", rendered_text)
        self.assertIn("Midnight Loop", rendered_text)
        self.assertIn("Nova Lane", rendered_text)

    def test_debug_panel_renders_only_in_developer_mode(self):
        renderer = FakeRenderer()

        render_developer_debug_panel(renderer, {"error_type": None}, False)

        self.assertEqual(renderer.calls, [])

        render_developer_debug_panel(renderer, {"error_type": None}, True)

        rendered_text = " ".join(str(call) for call in renderer.calls)
        self.assertIn("Developer Debug Panel", rendered_text)


if __name__ == "__main__":
    unittest.main()
