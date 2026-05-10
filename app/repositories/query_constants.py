SELECT_MUSIC_BY_CATEGORIES = """
SELECT *
FROM music_catalog
WHERE recommendation_category = ANY(%(categories)s)
ORDER BY created_at DESC;
"""

SELECT_MUSIC_BY_RELEASE_TYPE = """
SELECT *
FROM music_catalog
WHERE release_type = %(release_type)s
ORDER BY created_at DESC;
"""

SELECT_MUSIC_BY_GENRES = """
SELECT *
FROM music_catalog
WHERE genres && %(genres)s::TEXT[]
ORDER BY created_at DESC;
"""

SELECT_MUSIC_BY_MOODS = """
SELECT *
FROM music_catalog
WHERE moods && %(moods)s::TEXT[]
ORDER BY created_at DESC;
"""

INSERT_INTERACTION_LOG = """
INSERT INTO interaction_logs (
    log_id,
    request_id,
    user_id,
    session_id,
    user_input,
    page_type,
    status,
    response_type,
    intent_type,
    validation_status,
    error_type,
    compact_kag_state_json,
    compact_rag_state_json,
    compact_response_state_json,
    validation_result_json,
    latency_ms
) VALUES (
    %(log_id)s,
    %(request_id)s,
    %(user_id)s,
    %(session_id)s,
    %(user_input)s,
    %(page_type)s,
    %(status)s,
    %(response_type)s,
    %(intent_type)s,
    %(validation_status)s,
    %(error_type)s,
    %(compact_kag_state_json)s,
    %(compact_rag_state_json)s,
    %(compact_response_state_json)s,
    %(validation_result_json)s,
    %(latency_ms)s
);
"""

SELECT_INTERACTION_LOGS_BY_USER_ID = """
SELECT *
FROM interaction_logs
WHERE user_id = %(user_id)s
ORDER BY created_at DESC;
"""

SELECT_RECENT_INTERACTION_LOGS = """
SELECT *
FROM interaction_logs
ORDER BY created_at DESC
LIMIT %(limit)s;
"""
