from app.services.main_recommendation_service import MainRecommendationService


def test_main_recommendation_service_returns_page_view_model():
    view_model = MainRecommendationService().get_page_view_model("user_001")

    assert view_model["page_type"] == "main_recommendation_page"
    assert view_model["status"] == "success"
    assert view_model["taste_badges"]
    assert view_model["recommendation_groups"]["personalized_match"]
    assert view_model["recommendation_groups"]["discovery_candidate"]
    assert "debug" in view_model
