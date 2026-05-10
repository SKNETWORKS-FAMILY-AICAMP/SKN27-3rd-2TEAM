from fastapi.testclient import TestClient

from app.main import app


def test_music_detail_api_returns_contract_shape():
    client = TestClient(app)

    response = client.get("/api/music/detail/track_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["music_detail"]["content_id"] == "track_001"
    assert "source" in payload["music_detail"]
