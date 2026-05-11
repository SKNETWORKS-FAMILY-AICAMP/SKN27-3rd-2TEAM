from fastapi.testclient import TestClient

from app.api.music_detail_routes import get_music_detail_service
from app.main import app


def test_music_detail_api_returns_contract_shape():
    client = TestClient(app)

    response = client.get("/api/music/detail/track_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["music_detail"]["content_id"] == "track_001"
    assert "source" in payload["music_detail"]


def test_music_detail_api_uses_injected_detail_service():
    class StubMusicDetailService:
        def get_detail(self, content_id):
            return {
                "content_id": content_id,
                "title": "Midnight Loop",
                "artist": "Nova Lane",
                "display_reason": "catalog fallback",
                "evidence_summary": "catalog fallback",
                "album": "Night Sketch",
                "genre": ["indie"],
                "mood": ["night"],
                "source": "music_catalog",
            }

    app.dependency_overrides[get_music_detail_service] = lambda: StubMusicDetailService()
    try:
        client = TestClient(app)
        response = client.get("/api/music/detail/track_001")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["music_detail"]["title"] == "Midnight Loop"
    assert payload["music_detail"]["source"] == "music_catalog"
