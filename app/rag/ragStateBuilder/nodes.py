"""
Workflow nodes for building RAG state.

These nodes are designed for MVP use:
- They operate only on RagState
- They do not call an LLM directly
- They can run with mock data before real retrieval is connected
"""

from copy import deepcopy

from app.rag.ragStateBuilder.schema import (
    InformationEvidence,
    RagOutput,
    RagState,
    RecommendationContext,
    RecommendationReason,
    RecommendationScripts,
    RecommendedContentEvidence,
    RetrievalTrace,
)


def transform_query(state: RagState) -> RagState:
    """
    Build a retrieval-friendly query from user input and KAG hints.
    """
    next_state = deepcopy(state)
    user_input = next_state.get("user_input", "").strip()
    kag_state = next_state.get("kag_state", {})
    goal = kag_state.get("recommendation_goal", {})
    requirements = kag_state.get("content_requirements", {})
    preferences = kag_state.get("preference_tags", {})

    transformed_parts = [user_input] if user_input else []

    primary_goal = goal.get("primary_goal")
    if primary_goal:
        transformed_parts.append(f"goal:{primary_goal}")

    # 선호 태그 추가
    for genre in preferences.get("genres", []):
        transformed_parts.append(f"genre:{genre}")
    for artist in preferences.get("artists", []):
        transformed_parts.append(f"artist:{artist}")
    for mood in preferences.get("moods", []):
        transformed_parts.append(f"mood:{mood}")
    
    if preferences.get("energy"):
        transformed_parts.append(f"energy:{preferences['energy']}")
    if preferences.get("tempo"):
        transformed_parts.append(f"tempo:{preferences['tempo']}")

    for item in requirements.get("must_include", []):
        transformed_parts.append(f"must:{item}")

    for item in requirements.get("avoid", []):
        transformed_parts.append(f"avoid:{item}")

    next_state["transformed_query"] = " | ".join(transformed_parts)
    # 실제 검색에서 사용할 최종 쿼리는 transform_query 단계에서 완성된 문자열을 사용하게 됩니다.
    # 단, 현재 retrieve_documents 노드에서는 user_input을 직접 쓰고 있으므로, 
    # 거기서도 transformed_query를 쓰도록 수정이 필요할 수 있습니다.
    return next_state


from app.rag.services.retrieval import retrieve_relevant_docs


def _map_es_to_evidence(doc: dict) -> RecommendedContentEvidence:
    """
    Elasticsearch 검색 결과를 RecommendedContentEvidence 스키마로 매핑합니다.
    사용자 입력과 결과 데이터에 따라 동적으로 필드를 구성합니다.
    """
    metadata = doc.get("metadata", {})
    
    # 장르 추출 (다양한 필드명 대응)
    genre_raw = metadata.get("Genre") or metadata.get("genre", "N/A")
    if isinstance(genre_raw, list):
        genres = genre_raw
    else:
        genres = [g.strip() for g in str(genre_raw).split(",")] if genre_raw else ["N/A"]

    # 무드/감정 추출
    mood_raw = metadata.get("emotion") or metadata.get("mood", "N/A")
    if isinstance(mood_raw, list):
        moods = mood_raw
    else:
        moods = [m.strip() for m in str(mood_raw).split(",")] if mood_raw else ["N/A"]

    score = doc.get("score", 0.0)
    song = metadata.get("song", "알 수 없음")
    artist = metadata.get("Artist(s)") or metadata.get("artist", "알 수 없음")

    # 동적인 evidence_summary 생성
    # 사용자가 보고 싶어하는 장르와 무드 정보를 포함하여 생성합니다.
    evidence_summary = (
        f"이 곡은 {', '.join(genres)} 장르와 {', '.join(moods)} 분위기를 선호하는 사용자의 요청에 "
        f"{score:.4f}의 높은 유사도로 매칭되었습니다. {artist}의 대표적인 스타일을 경험할 수 있습니다."
    )

    return {
        "content_id": doc.get("doc_id", "unknown"),
        "title": song,
        "artist": artist,
        "album": metadata.get("Album") or metadata.get("album", "N/A"),
        "genre": genres,
        "mood": moods,
        "tempo": str(metadata.get("Tempo") or metadata.get("tempo", "N/A")),
        "release_type": "existing_catalog",
        "recommendation_category": "personalized_match",
        "evidence_summary": evidence_summary,
        "score": score,
        "raw_content": doc.get("content", ""),
        "match_reason": {
            "genre_match": True,
            "mood_match": True,
            "tempo_match": False,
            "new_taste_expansion": False,
        },
    }


def retrieve_documents(state: RagState) -> RagState:
    """
    Populate retrieval candidates using Elasticsearch.
    """
    next_state = deepcopy(state)

    # 1. 상태에 이미 결과가 있는 경우 재사용
    existing_candidates = next_state.get("retrieved_candidates")
    if existing_candidates:
        next_state["filtered_candidates"] = existing_candidates
        next_state["retrieval_trace"] = _build_retrieval_trace(
            strategy="state_candidates",
            candidates=existing_candidates,
        )
        return next_state

    # 2. Elasticsearch를 통한 실제 검색 수행
    # user_input 대신 가공된 transformed_query를 사용합니다.
    query = next_state.get("transformed_query", next_state.get("user_input", ""))
    max_candidates = next_state.get("retrieval_constraints", {}).get("max_candidates", 5)
    
    try:
        # 하이브리드 검색 수행
        es_results = retrieve_relevant_docs(query, k=max_candidates, search_type="hybrid")
        
        # 결과를 RAG 스키마에 맞게 매핑
        candidates = [_map_es_to_evidence(doc) for doc in es_results]
        
        if not candidates:
            # 결과가 없을 경우 Mock 데이터로 폴백 (테스트 용도)
            candidates = _build_mock_candidates()
            strategy = "mock_fallback"
        else:
            strategy = "elasticsearch_hybrid"

    except Exception as e:
        print(f"[Retrieval] Error during ES retrieval: {e}")
        candidates = _build_mock_candidates()
        strategy = "error_fallback_mock"

    next_state["retrieved_candidates"] = candidates
    next_state["filtered_candidates"] = candidates
    next_state["retrieval_trace"] = _build_retrieval_trace(
        strategy=strategy,
        candidates=candidates,
    )
    return next_state



def grade_documents(state: RagState) -> RagState:
    """
    Trim candidates to the maximum display size.
    """
    next_state = deepcopy(state)
    candidates = next_state.get("filtered_candidates", [])
    max_display = next_state.get("retrieval_constraints", {}).get(
        "max_display_recommendations",
        len(candidates),
    )

    graded_candidates = candidates[:max_display]
    next_state["filtered_candidates"] = graded_candidates

    trace = next_state.get("retrieval_trace")
    if trace:
        trace["candidate_count"] = len(graded_candidates)
        next_state["retrieval_trace"] = trace

    if not graded_candidates:
        next_state["status"] = "fallback"
        next_state["validation_errors"] = [
            *next_state.get("validation_errors", []),
            "No recommendation candidates available after grading.",
        ]

    return next_state


def generate_answer(state: RagState) -> RagState:
    """
    Build structured RAG output from graded candidates.

    This function does not create the final natural-language chat response.
    It only assembles the structured RAG state and output payload.
    """
    next_state = deepcopy(state)
    candidates = next_state.get("filtered_candidates", [])

    if not candidates:
        next_state["status"] = "fallback"
        next_state["recommendation_context"] = _build_fallback_context()
        next_state["recommended_content_evidence"] = []
        next_state["recommendation_reason"] = {
            "summary": "Not enough recommendation evidence was found, so the flow switched to fallback.",
            "reason_items": [
                "Recommendation candidates were insufficient after retrieval and grading."
            ],
        }
        next_state["information_evidence"] = []
        next_state["recommendation_scripts"] = _build_default_scripts()
        next_state["output"] = _build_output(next_state)
        return next_state

    next_state["status"] = "success"
    next_state["recommendation_context"] = _build_recommendation_context(next_state)
    next_state["recommended_content_evidence"] = candidates
    next_state["recommendation_reason"] = _build_recommendation_reason(candidates)
    next_state["information_evidence"] = _build_information_evidence(candidates)
    next_state["recommendation_scripts"] = _build_default_scripts()
    next_state["output"] = _build_output(next_state)
    return next_state


def _build_mock_candidates() -> list[RecommendedContentEvidence]:
    return [
        {
            "content_id": "track_001",
            "title": "Midnight Loop",
            "artist": "Nova Lane",
            "album": "Night Sketch",
            "genre": ["rnb", "indie"],
            "mood": ["calm", "night"],
            "tempo": "medium",
            "release_type": "existing_catalog",
            "recommendation_category": "personalized_match",
            "evidence_summary": "사용자의 기존 rnb/indie 취향과 calm/night 분위기에 직접적으로 연결되는 곡",
            "match_reason": {
                "genre_match": True,
                "mood_match": True,
                "tempo_match": True,
                "new_taste_expansion": False,
            },
        },
        {
            "content_id": "track_002",
            "title": "Soft Orbit",
            "artist": "Luna Field",
            "album": "Orbit Notes",
            "genre": ["dream_pop", "ambient"],
            "mood": ["calm", "night", "soft"],
            "tempo": "slow",
            "release_type": "existing_catalog",
            "recommendation_category": "discovery_candidate",
            "evidence_summary": "기존 calm/night 분위기와 연결되지만 dream_pop/ambient 계열로 취향 확장이 가능한 곡",
            "match_reason": {
                "genre_match": False,
                "mood_match": True,
                "tempo_match": False,
                "new_taste_expansion": True,
            },
        },
    ]


def _build_recommendation_context(state: RagState) -> RecommendationContext:
    kag_state = state.get("kag_state", {})
    goal = kag_state.get("recommendation_goal", {})

    context_type = goal.get("primary_goal", "personalized_recommendation")
    if context_type == "new_taste_discovery":
        base_context = (
            "사용자의 기존 취향을 기반으로 안전한 새 취향 확장 후보를 제공합니다."
        )
    else:
        base_context = (
            "사용자의 알려진 선호도와 연결된 개인화된 추천 후보를 제공합니다."
        )

    trace = state.get("retrieval_trace", {})
    source_type = trace.get("retrieval_strategy", "mock_music_catalog")

    return {
        "context_type": context_type,
        "base_context": base_context,
        "source_type": source_type,
    }


def _build_fallback_context() -> RecommendationContext:
    return {
        "context_type": "fallback",
        "base_context": "추천 근거가 부족하여 기본 안내 컨텍스트만 제공 가능합니다.",
        "source_type": "fallback",
    }


def _build_recommendation_reason(
    candidates: list[RecommendedContentEvidence],
) -> RecommendationReason:
    has_personalized = any(
        item["recommendation_category"] == "personalized_match"
        for item in candidates
    )
    has_discovery = any(
        item["recommendation_category"] == "discovery_candidate"
        for item in candidates
    )

    reason_items: list[str] = []
    if has_personalized:
        reason_items.append(
            "사용자의 기존 선호도와 직접적으로 연결되는 곡들을 포함하고 있습니다."
        )
    if has_discovery:
        reason_items.append(
            "취향 확장을 위한 낮은 위험도의 탐색 후보곡들을 포함하고 있습니다."
        )
    if not reason_items:
        reason_items.append(
            "가용한 근거 요약을 바탕으로 추천 리스트를 구성했습니다."
        )

    return {
        "summary": "익숙한 선호도 매칭과 단계적인 취향 발견 사이의 균형을 유지합니다.",
        "reason_items": reason_items,
    }


def _build_information_evidence(
    candidates: list[RecommendedContentEvidence],
) -> list[InformationEvidence]:
    info_items: list[InformationEvidence] = []
    seen_genres: set[str] = set()

    for candidate in candidates:
        for genre in candidate.get("genre", []):
            if genre in seen_genres:
                continue
            seen_genres.add(genre)

            info_items.append(
                {
                    "info_id": f"genre_{genre}_001",
                    "info_type": "genre",
                    "title": genre,
                    "summary": f"{genre} 장르의 특성을 바탕으로 한 추천 근거가 확보되었습니다.",
                }
            )

    return info_items


def _build_default_scripts() -> RecommendationScripts:
    return {
        "dj_intro": "익숙한 분위기는 유지하면서 살짝 새로운 결의 음악도 함께 골라봤어요.",
        "personalized_message": "먼저 편안하게 들으실 수 있는 곡부터 추천해 드릴게요.",
        "new_release_message": "최근 업데이트된 곡 중에서도 사용자님 취향에 맞는 곡들을 골라봤어요.",
        "discovery_message": "새로운 시도를 해보고 싶으시다면 이 곡으로 시작해보는 걸 추천해요.",
        "fallback_message": "지금은 충분한 추천 근거가 부족해 기본 안내만 제공해 드릴게요.",
    }


def _build_retrieval_trace(
    strategy: str,
    candidates: list[RecommendedContentEvidence],
) -> RetrievalTrace:
    categories = [
        f"recommendation_category:{candidate['recommendation_category']}"
        for candidate in candidates
    ]

    matched_fields = {"genre", "mood", "tempo"}

    return {
        "retrieval_strategy": strategy,
        "retrieval_filters": categories,
        "matched_fields": sorted(matched_fields),
        "candidate_count": len(candidates),
    }


def _build_output(state: RagState) -> RagOutput:
    return {
        "status": state["status"],
        "recommendation_context": state["recommendation_context"],
        "recommended_content_evidence": state["recommended_content_evidence"],
        "recommendation_reason": state["recommendation_reason"],
        "information_evidence": state["information_evidence"],
        "recommendation_scripts": state["recommendation_scripts"],
        "retrieval_trace": state["retrieval_trace"],
    }
