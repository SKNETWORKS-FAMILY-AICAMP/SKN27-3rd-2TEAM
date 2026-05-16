from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_frontend_defines_music_detail_and_not_found_pages():
    music_detail = read_text("frontend/src/pages/MusicDetailPage.tsx")
    not_found = read_text("frontend/src/pages/NotFoundPage.tsx")
    app = read_text("frontend/src/App.tsx")

    assert "MusicDetailPage" in music_detail
    assert "NotFoundPage" in not_found
    assert '"/music"' in app
    assert "detail" in app
    assert "NotFoundPage" in app
