SELECT_LATEST_ML_OUTPUT_BY_USER_ID = """
SELECT *
FROM ml_outputs
WHERE user_id = %(user_id)s
ORDER BY created_at DESC
LIMIT 1;
"""

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
    user_id,
    user_input,
    page_type,
    status,
    response_type,
    primary_goal,
    intent_type,
    target_page,
    primary_section,
    validation_status,
    error_type,
    ml_output_json,
    kag_state_json,
    rag_state_json,
    response_state_json,
    validation_result_json,
    latency_ms
) VALUES (
    %(log_id)s,
    %(user_id)s,
    %(user_input)s,
    %(page_type)s,
    %(status)s,
    %(response_type)s,
    %(primary_goal)s,
    %(intent_type)s,
    %(target_page)s,
    %(primary_section)s,
    %(validation_status)s,
    %(error_type)s,
    %(ml_output_json)s,
    %(kag_state_json)s,
    %(rag_state_json)s,
    %(response_state_json)s,
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

INSERT_LLM_CALL_LOG = """
INSERT INTO llm_call_logs (
    log_id,
    provider,
    model_name,
    request_json,
    response_json,
    status,
    error_message,
    latency_ms
) VALUES (
    %(log_id)s,
    %(provider)s,
    %(model_name)s,
    %(request_json)s,
    %(response_json)s,
    %(status)s,
    %(error_message)s,
    %(latency_ms)s
);
"""

INSERT_VALIDATION_LOG = """
INSERT INTO validation_logs (
    log_id,
    validation_type,
    validation_status,
    error_path,
    error_message,
    validation_detail_json
) VALUES (
    %(log_id)s,
    %(validation_type)s,
    %(validation_status)s,
    %(error_path)s,
    %(error_message)s,
    %(validation_detail_json)s
);
"""
