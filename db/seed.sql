INSERT INTO users (user_id, display_name)
VALUES
    ('user_001', 'user_001'),
    ('user_002', 'user_002'),
    ('user_003', 'user_003')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO ml_outputs (
    user_id,
    status,
    preferred_genres,
    preferred_artists,
    preferred_moods,
    preferred_tempo,
    recent_listening_level,
    recent_discovery_level,
    repeat_listening_ratio,
    new_artist_acceptance,
    personalization_strength,
    discovery_readiness,
    new_release_affinity,
    ml_output_json
) VALUES
(
    'user_001',
    'success',
    ARRAY['rnb', 'indie']::TEXT[],
    ARRAY['artist_a', 'artist_b']::TEXT[],
    ARRAY['calm', 'night']::TEXT[],
    'medium',
    'medium',
    'low',
    0.7200,
    0.3400,
    'high',
    'medium',
    'medium',
    '{
        "status": "success",
        "user_id": "user_001",
        "taste_profile": {
            "preferred_genres": ["rnb", "indie"],
            "preferred_artists": ["artist_a", "artist_b"],
            "preferred_moods": ["calm", "night"],
            "preferred_tempo": "medium"
        },
        "behavior_profile": {
            "recent_listening_level": "medium",
            "recent_discovery_level": "low",
            "repeat_listening_ratio": 0.72,
            "new_artist_acceptance": 0.34
        },
        "recommendation_profile": {
            "personalization_strength": "high",
            "discovery_readiness": "medium",
            "new_release_affinity": "medium"
        }
    }'::JSONB
),
(
    'user_002',
    'success',
    ARRAY['pop', 'dance']::TEXT[],
    ARRAY['artist_c', 'artist_d']::TEXT[],
    ARRAY['bright', 'energetic']::TEXT[],
    'fast',
    'high',
    'medium',
    0.4100,
    0.6800,
    'medium',
    'medium',
    'high',
    '{
        "status": "success",
        "user_id": "user_002",
        "taste_profile": {
            "preferred_genres": ["pop", "dance"],
            "preferred_artists": ["artist_c", "artist_d"],
            "preferred_moods": ["bright", "energetic"],
            "preferred_tempo": "fast"
        },
        "behavior_profile": {
            "recent_listening_level": "high",
            "recent_discovery_level": "medium",
            "repeat_listening_ratio": 0.41,
            "new_artist_acceptance": 0.68
        },
        "recommendation_profile": {
            "personalization_strength": "medium",
            "discovery_readiness": "medium",
            "new_release_affinity": "high"
        }
    }'::JSONB
),
(
    'user_003',
    'success',
    ARRAY['ballad', 'acoustic']::TEXT[],
    ARRAY['artist_e', 'artist_f']::TEXT[],
    ARRAY['soft', 'calm']::TEXT[],
    'slow',
    'low',
    'low',
    0.8200,
    0.1800,
    'high',
    'low',
    'low',
    '{
        "status": "success",
        "user_id": "user_003",
        "taste_profile": {
            "preferred_genres": ["ballad", "acoustic"],
            "preferred_artists": ["artist_e", "artist_f"],
            "preferred_moods": ["soft", "calm"],
            "preferred_tempo": "slow"
        },
        "behavior_profile": {
            "recent_listening_level": "low",
            "recent_discovery_level": "low",
            "repeat_listening_ratio": 0.82,
            "new_artist_acceptance": 0.18
        },
        "recommendation_profile": {
            "personalization_strength": "high",
            "discovery_readiness": "low",
            "new_release_affinity": "low"
        }
    }'::JSONB
);

INSERT INTO music_catalog (
    content_id,
    title,
    artist,
    album,
    genres,
    moods,
    tempo,
    release_type,
    recommendation_category,
    evidence_summary,
    source_type,
    metadata_json
) VALUES
(
    'track_001',
    'Midnight Loop',
    'Nova Lane',
    'Night Sketch',
    ARRAY['rnb', 'indie']::TEXT[],
    ARRAY['calm', 'night']::TEXT[],
    'medium',
    'existing_catalog',
    'personalized_match',
    'user_001의 rnb/indie 취향과 calm/night 분위기에 직접 연결되는 곡',
    'mock_music_catalog',
    '{"match_reason": {"genre_match": true, "mood_match": true}}'::JSONB
),
(
    'track_002',
    'Velvet Echo',
    'June Park',
    'Echo Room',
    ARRAY['rnb', 'soul']::TEXT[],
    ARRAY['calm', 'soft']::TEXT[],
    'medium',
    'existing_catalog',
    'similar_taste',
    '기존 rnb 취향과 가까운 분위기의 유사 취향 후보',
    'mock_music_catalog',
    '{"match_reason": {"genre_match": true, "mood_match": true}}'::JSONB
),
(
    'track_003',
    'Fresh Signal',
    'Mira Tone',
    'Updated Signal',
    ARRAY['indie', 'electro_pop']::TEXT[],
    ARRAY['bright', 'clean']::TEXT[],
    'medium',
    'new_release',
    'new_release',
    '최근 업데이트 곡이며 indie 취향과 일부 연결되는 신보 후보',
    'mock_music_catalog',
    '{"match_reason": {"genre_match": true, "new_taste_expansion": true}}'::JSONB
),
(
    'track_004',
    'Soft Orbit',
    'Luna Field',
    'Orbit Notes',
    ARRAY['dream_pop', 'ambient']::TEXT[],
    ARRAY['calm', 'night', 'soft']::TEXT[],
    'slow',
    'existing_catalog',
    'discovery_candidate',
    'calm/night 분위기와 연결되면서 dream_pop 계열로 확장 가능한 곡',
    'mock_music_catalog',
    '{"match_reason": {"mood_match": true, "new_taste_expansion": true}}'::JSONB
),
(
    'info_dream_pop_001',
    'dream_pop',
    'genre_information',
    NULL,
    ARRAY['dream_pop']::TEXT[],
    ARRAY['calm', 'soft']::TEXT[],
    'unknown',
    'unknown',
    'information_related',
    'dream_pop 장르 설명에 사용할 수 있는 정보성 메타데이터',
    'mock_music_catalog',
    '{"info_type": "genre", "summary": "soft and atmospheric pop style"}'::JSONB
)
ON CONFLICT (content_id) DO NOTHING;
