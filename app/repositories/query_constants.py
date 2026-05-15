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

SELECT_MUSIC_BY_CONTENT_ID = """
SELECT *
FROM music_catalog
WHERE content_id = %(content_id)s
LIMIT 1;
"""

SELECT_MUSIC_IDENTITY_MATCHES = """
SELECT content_id, title, artist
FROM music_catalog
WHERE LOWER(title) = LOWER(%(text)s)
   OR LOWER(artist) = LOWER(%(text)s)
ORDER BY content_id ASC;
"""

SELECT_FALLBACK_NEW_RELEASES = """
SELECT *
FROM music_catalog
WHERE release_type = 'new_release'
  AND NOT (content_id = ANY(%(excluded_content_ids)s))
  AND NOT (artist = ANY(%(excluded_artists)s))
  AND NOT (genres && %(excluded_genres)s::TEXT[])
ORDER BY created_at DESC, content_id ASC
LIMIT %(limit)s;
"""

SELECT_FALLBACK_DISCOVERY = """
SELECT *
FROM music_catalog
WHERE recommendation_category = 'discovery_candidate'
  AND NOT (content_id = ANY(%(excluded_content_ids)s))
  AND NOT (artist = ANY(%(excluded_artists)s))
  AND NOT (genres && %(excluded_genres)s::TEXT[])
ORDER BY created_at DESC, content_id ASC
LIMIT %(limit)s;
"""

UPSERT_CHAT_SESSION = """
INSERT INTO chat_sessions (session_id, user_id, started_at)
VALUES (%(session_id)s, %(user_id)s, NOW())
ON CONFLICT (session_id) DO NOTHING;
"""

INSERT_CHAT_SESSION_TURN = """
INSERT INTO chat_session_turns
    (session_id, user_input, chatbot_response, created_at)
VALUES (
    %(session_id)s,
    %(user_input)s,
    %(chatbot_response)s,
    %(created_at)s
);
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

DELETE_INTERACTION_LOGS_BY_SESSION_ID = """
DELETE FROM interaction_logs
WHERE session_id = %(session_id)s;
"""

INSERT_USER_TASTE_EVENT = """
INSERT INTO user_taste_events (
    event_id,
    user_id,
    session_id,
    content_id,
    event_type,
    source,
    title,
    artist,
    genre_json,
    mood_json,
    recommendation_category,
    created_at
) VALUES (
    %(event_id)s,
    %(user_id)s,
    %(session_id)s,
    %(content_id)s,
    %(event_type)s,
    %(source)s,
    %(title)s,
    %(artist)s,
    %(genre_json)s,
    %(mood_json)s,
    %(recommendation_category)s,
    %(created_at)s
);
"""

UPSERT_USER_TASTE_PROFILE = """
INSERT INTO user_taste_profiles (
    user_id,
    preferred_genres_json,
    preferred_moods_json,
    preferred_artists_json,
    selected_content_ids_json,
    updated_at
) VALUES (
    %(user_id)s,
    %(preferred_genres_json)s,
    %(preferred_moods_json)s,
    %(preferred_artists_json)s,
    %(selected_content_ids_json)s,
    NOW()
)
ON CONFLICT (user_id) DO UPDATE SET
    preferred_genres_json = EXCLUDED.preferred_genres_json,
    preferred_moods_json = EXCLUDED.preferred_moods_json,
    preferred_artists_json = EXCLUDED.preferred_artists_json,
    selected_content_ids_json = EXCLUDED.selected_content_ids_json,
    updated_at = NOW();
"""

SELECT_USER_TASTE_PROFILE = """
SELECT
    user_id,
    preferred_genres_json,
    preferred_moods_json,
    preferred_artists_json,
    selected_content_ids_json,
    updated_at
FROM user_taste_profiles
WHERE user_id = %(user_id)s;
"""

UPSERT_USER_NEGATIVE_PREFERENCES = """
INSERT INTO user_negative_preferences (
    user_id,
    disliked_artists_json,
    disliked_tracks_json,
    disliked_genres_json,
    updated_at
) VALUES (
    %(user_id)s,
    %(disliked_artists_json)s,
    %(disliked_tracks_json)s,
    %(disliked_genres_json)s,
    NOW()
)
ON CONFLICT (user_id) DO UPDATE SET
    disliked_artists_json = EXCLUDED.disliked_artists_json,
    disliked_tracks_json = EXCLUDED.disliked_tracks_json,
    disliked_genres_json = EXCLUDED.disliked_genres_json,
    updated_at = NOW();
"""

SELECT_USER_NEGATIVE_PREFERENCES = """
SELECT
    user_id,
    disliked_artists_json,
    disliked_tracks_json,
    disliked_genres_json,
    updated_at
FROM user_negative_preferences
WHERE user_id = %(user_id)s;
"""

INSERT_DETAIL_VIEW_LOG = """
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
    'music_detail_page',
    'success',
    %(response_type)s,
    NULL,
    'success',
    NULL,
    '{}',
    %(compact_rag_state_json)s,
    '{}',
    '{}',
    0
);
"""
