"""Neo4j KAG 후보 쿼리 실행. 어댑터는 ``execute_kag_track_ids``만 호출하면 ``track_id`` 리스트를 받는다."""

from __future__ import annotations

import logging
from collections.abc import Callable

from app.kag.connection import Neo4j_Connection
from app.kag.querys import KagCypherQuery

logger = logging.getLogger("rimas.kag.execute_querys")

TrackIdExecutor = Callable[[Neo4j_Connection, dict], list[str]]


def _records_to_track_ids(records: list) -> list[str]:
    out: list[str] = []
    for rec in records:
        data = dict(rec)
        tid = data.get("track_id")
        if tid is None:
            continue
        s = str(tid).strip()
        if s:
            out.append(s)
    return out


def execute_personalized_track_ids(conn: Neo4j_Connection, row: dict) -> list[str]:
    query, parameters = KagCypherQuery.personalized_recommendation_candidates(row)
    return _records_to_track_ids(conn.execute_query(query, parameters))


def execute_new_release_track_ids(conn: Neo4j_Connection, row: dict) -> list[str]:
    query, parameters = KagCypherQuery.new_release_recommendation_candidates(row)
    return _records_to_track_ids(conn.execute_query(query, parameters))


def execute_discovery_track_ids(conn: Neo4j_Connection, row: dict) -> list[str]:
    query, parameters = KagCypherQuery.discovery_recommendation_candidates(row)
    return _records_to_track_ids(conn.execute_query(query, parameters))


def route_kag_query_executor(primary_goal: str) -> TrackIdExecutor:
    """
    primary_goal에 맞는 ``(conn, row) -> list[str]`` 실행 함수를 고른다.
    검색이 필요하지 않은 다른 타입이 왔을 경우 개인화 추천으로 동작하도록 예외처리만 적용 
    """
    table: dict[str, TrackIdExecutor] = {
        "personalized_recommendation": execute_personalized_track_ids,
        "new_release_recommendation": execute_new_release_track_ids,
        "discovery_recommendation": execute_discovery_track_ids,
        "recommendation_reason": execute_personalized_track_ids,
        "general_chat": execute_personalized_track_ids,
        "music_information": execute_personalized_track_ids,
    }
    return table.get(primary_goal, execute_personalized_track_ids)


def _query_row_from_session(session_context: dict | None) -> dict:
    """ 세션 데이터에서 쿼리에 필요한 정보만 모은다. """
    ctx = session_context or {}
    kag = ctx.get("kag_input_json") or {}
    if not isinstance(kag, dict):
        kag = {}
    qc = kag.get("query_context") or {}
    if not isinstance(qc, dict):
        qc = {}
    constraints = kag.get("constraints") or {}
    if not isinstance(constraints, dict):
        constraints = {}
    try:
        limit = int(constraints.get("max_candidates", 10))
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 500))

    return {
        "genre_candidates": list(qc.get("genre_candidates") or []),
        "mood_candidates": list(qc.get("mood_candidates") or []),
        "limit": limit,
        "exclude_genres": list(ctx.get("recent_genres") or []),
        "user_id": kag.get("user_id") or ctx.get("user_id"),
    }


def execute_kag_track_ids(
    primary_goal: str,
    session_context: dict,
    neo4j_connection: Neo4j_Connection,
) -> list[str]:
    """세션·kag_input_json에서 row를 만들고, primary_goal에 따라 쿼리를 실행해 ``track_id`` 리스트를 반환한다."""
    row = _query_row_from_session(session_context)
    executor = route_kag_query_executor(primary_goal)
    
    try:
        return executor(neo4j_connection, row)
    except Exception:
        logger.exception(
            "kag_neo4j_query_failed",
            extra={"primary_goal": primary_goal},
        )
        raise
