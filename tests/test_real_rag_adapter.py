import pytest

from app.rag.adapters.rag_real_adapter import RealRagAdapter
from app.rag.services.elasticsearch_retriever import ElasticsearchRagHit, ElasticsearchRagRetriever


class StubRetriever:
    def __init__(self, hits=None, exc=None):
        self.hits = hits or []
        self.exc = exc
        self.calls = []

    def search(self, *, query_text, content_ids, max_evidence_per_track):
        self.calls.append(
            {
                "query_text": query_text,
                "content_ids": content_ids,
                "max_evidence_per_track": max_evidence_per_track,
            }
        )
        if self.exc:
            raise self.exc
        return self.hits


def _rag_input(content_ids=None):
    return {
        "request_id": "req_001",
        "user_id": "user_001",
        "session_id": "session_001",
        "intent_type": "personalized_recommendation",
        "kag_recommended_content_ids": content_ids or ["track_001"],
        "target_section": "personalized_section",
        "query_text": "calm indie night",
        "evidence_need": ["track_description", "recommendation_reason"],
        "retrieval_constraints": {
            "max_evidence_per_track": 2,
            "require_content_id_match": True,
        },
    }


def test_real_rag_adapter_maps_elasticsearch_hits_to_rag_state():
    retriever = StubRetriever(
        hits=[
            ElasticsearchRagHit(
                content_id="track_001",
                title="Midnight Loop",
                artist="Nova Lane",
                album="Night Sketch",
                genre=["indie"],
                mood=["calm"],
                content="A calm indie song for late night listening.",
                score=9.5,
            )
        ]
    )

    result = RealRagAdapter(retriever=retriever).build_state(
        kag_state={"recommended_content_ids": ["track_001"]},
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "success"
    assert result["recommended_content_evidence"][0]["content_id"] == "track_001"
    assert result["recommended_content_evidence"][0]["title"] == "Midnight Loop"
    assert result["retrieval_metadata"]["source"] == "elasticsearch"
    assert retriever.calls[0]["content_ids"] == ["track_001"]


def test_real_rag_adapter_filters_hits_outside_kag_candidates():
    retriever = StubRetriever(
        hits=[
            ElasticsearchRagHit(
                content_id="track_999",
                title="Outside",
                artist="Other",
                album=None,
                genre=[],
                mood=[],
                content="Outside candidate.",
                score=1.0,
            )
        ]
    )

    result = RealRagAdapter(retriever=retriever).build_state(
        kag_state={"recommended_content_ids": ["track_001"]},
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "fallback"
    assert result["recommended_content_evidence"] == []
    assert result["retrieval_metadata"]["reason"] == "no_candidate_matched_evidence"


def test_real_rag_adapter_returns_fallback_without_kag_candidates():
    result = RealRagAdapter(retriever=StubRetriever()).build_state(
        kag_state={"recommended_content_ids": []},
        rag_input_json=_rag_input([]),
    )

    assert result["status"] == "fallback"
    assert result["recommended_content_evidence"] == []
    assert result["retrieval_metadata"]["reason"] == "empty_kag_candidates"


def test_real_rag_adapter_returns_failed_when_retriever_raises():
    result = RealRagAdapter(retriever=StubRetriever(exc=RuntimeError("index missing"))).build_state(
        kag_state={"recommended_content_ids": ["track_001"]},
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "failed"
    assert result["recommended_content_evidence"] == []
    assert result["retrieval_metadata"]["reason"] == "retriever_error"


def test_real_rag_adapter_filters_excluded_artist():
    retriever = StubRetriever(
        hits=[
            ElasticsearchRagHit(
                content_id="track_001",
                title="Bad Fit",
                artist="Billie Eilish",
                album=None,
                genre=["pop"],
                mood=["night"],
                content="raw evidence",
                score=1.0,
                release_type="existing_catalog",
            )
        ]
    )

    result = RealRagAdapter(retriever=retriever).build_state(
        kag_state={
            "recommended_content_ids": ["track_001"],
            "excluded_nodes": [{"type": "artist", "value": "Billie Eilish"}],
        },
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "fallback"
    assert result["recommended_content_evidence"] == []


def test_real_rag_adapter_filters_excluded_genre():
    retriever = StubRetriever(
        hits=[
            ElasticsearchRagHit(
                content_id="track_001",
                title="Bad Genre",
                artist="Artist",
                album=None,
                genre=["pop"],
                mood=["bright"],
                content="raw evidence",
                score=1.0,
                release_type="existing_catalog",
            )
        ]
    )

    result = RealRagAdapter(retriever=retriever).build_state(
        kag_state={
            "recommended_content_ids": ["track_001"],
            "excluded_nodes": [{"type": "genre", "value": "pop"}],
        },
        rag_input_json=_rag_input(["track_001"]),
    )

    assert result["status"] == "fallback"
    assert result["recommended_content_evidence"] == []


def test_elasticsearch_query_filters_all_supported_content_id_fields_and_uses_query_text():
    query = ElasticsearchRagRetriever._build_query(
        query_text="calm indie night",
        content_ids=["track_001", "track_002"],
        max_evidence_per_track=2,
    )

    bool_query = query["query"]["bool"]
    content_id_filter = bool_query["filter"][0]["bool"]
    filter_fields = {
        next(iter(terms["terms"].keys()))
        for terms in content_id_filter["should"]
    }

    assert query["size"] == 4
    assert content_id_filter["minimum_should_match"] == 1
    assert filter_fields == {
        "content_id",
        "content_id.keyword",
        "track_id",
        "track_id.keyword",
        "metadata.content_id",
        "metadata.content_id.keyword",
        "metadata.track_id",
        "metadata.track_id.keyword",
        "metadata.doc_id",
        "metadata.doc_id.keyword",
    }
    assert bool_query["should"][0]["multi_match"]["query"] == "calm indie night"
