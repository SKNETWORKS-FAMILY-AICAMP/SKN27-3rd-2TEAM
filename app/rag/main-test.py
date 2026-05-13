"""
Simple local test entrypoint for the RAG MVP workflow.

Usage:
    bundled python:
    python.exe app\\rag\\main-test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.ragStateBuilder.builder import build_rag_graph, compile_graph
from app.rag.ragStateBuilder.schema import RagRequest, RagState


def build_sample_request(user_input:str = "발라드 추천해줘") -> RagRequest:
    return {
        "request_id": "req_001",
        "user_id": "user_001",
        "page_type": "chatbot_page",
        "user_input": user_input,
        "kag_state": {
            "status": "success",
            "user": {
                "user_id": "user_001",
            },
            "recommendation_goal": {
                "primary_goal": "new_taste_discovery",
                "secondary_goal": "personalized_recommendation",
                "goal_reason": "사용자의 취향을 기반으로 신나는 분위기의 곡을 추천함",
            },
            "curation_intent": {
                "intent_type": "new_taste_discovery",
                "intent_confidence": 0.9,
                "allowed_modes": [
                    "personalized_recommendation",
                    "new_taste_discovery",
                ],
            },
            "content_requirements": {
                "must_include": ["personalized_match"],
                "optional_include": [],
                "avoid": [],
            },
            "preference_tags": {
                "genres": ["Pop", "Electronic"],
                "artists": ["Mark Ronson"],
                "moods": ["Excited", "Happy"],
                "energy": "high",
                "tempo": "fast"
            },
            "routing": {
                "target_page": "chatbot_page",
                "primary_section": "discovery_section",
            },
        },
        "retrieval_constraints": {
            "max_candidates": 3,
            "max_display_recommendations": 3,
            "allowed_source_types": [
                "elasticsearch",
                "hybrid_search",
            ],
            "require_evidence_summary": True,
            "require_content_id": True,
        },
    }


def build_initial_state(request: RagRequest) -> RagState:
    return {
        "request": request,
        "request_id": request["request_id"],
        "user_id": request["user_id"],
        "page_type": request["page_type"],
        "user_input": request["user_input"],
        "kag_state": request["kag_state"],
        "retrieval_constraints": request["retrieval_constraints"],
        "status": "success",
        "validation_errors": [],
        "warnings": [],
    }


from app.rag.services.retrieval import retrieve_relevant_docs


def test_retrieval(query: str, k: int = 5) -> None:
    print(f"\n{'='*50}")
    print(f"🔍 [Direct Test] 검색 수행 중... (키워드: '{query}')")
    print(f"{'='*50}")

    try:
        results = retrieve_relevant_docs(query, k=k, search_type="hybrid")

        if not results:
            print("❌ 검색 결과가 없습니다.")
            return

        for i, doc in enumerate(results):
            score = doc.get("score", 0.0)
            metadata = doc.get("metadata", {})
            print(f"[{i+1}] 점수: {score:.4f} | 곡명: {metadata.get('song')} | 아티스트: {metadata.get('artist')}")

    except Exception as e:
        print(f"❌ 오류: {e}")


def main() -> None:
    # 1. 통합 RAG 워크플로우 테스트
    user_input = input("어떤 음악을 원하시나요? : ")
    
    request = build_sample_request(user_input)
    initial_state = build_initial_state(request)
    
    graph = build_rag_graph()
    runner = compile_graph(graph)
    result_state = runner.invoke(initial_state)
    
    output = result_state.get("output", {})
    
    # output.md 형식에 맞춰 순수 JSON 데이터만 출력합니다.
    print(json.dumps(output, ensure_ascii=False, indent=2))

    # 2. Elasticsearch 리트리버 직접 테스트 (비교용)
    # test_query = "신나는 팝 음악 추천해줘"
    # test_retrieval(test_query, k=3)

if __name__ == "__main__":
    main()
