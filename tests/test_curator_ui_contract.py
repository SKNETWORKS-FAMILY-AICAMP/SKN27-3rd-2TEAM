from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_music_detail_modal_exposes_existing_source_and_evidence_summary():
    source = read_text("frontend/src/components/recommendation/MusicDetailModal.tsx")

    assert "큐레이션 근거" in source
    assert "detail.evidence_summary" in source
    assert "detail.source" in source


def test_chatbot_recommendation_cards_use_curator_language():
    source = read_text("frontend/src/components/chatbot/RelatedRecommendationCards.tsx")

    assert "큐레이터 추천" in source
    assert "related-cards__title" in source


def test_readme_marks_user_visible_source_limit_as_resolved_without_kag_rag_changes():
    source = read_text("README.md")

    assert "| 사용자 노출 출처 | 해결 |" in source
    assert "KAG/RAG 후보 생성과 검색 계약은 변경하지 않고" in source
