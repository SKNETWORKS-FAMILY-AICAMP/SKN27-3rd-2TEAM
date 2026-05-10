INSERT INTO users (user_id, display_name)
VALUES
    ('user_001', 'user_001'),
    ('user_002', 'user_002'),
    ('user_003', 'user_003')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO music_catalog (
    content_id,
    track_id,
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
    'track_001',
    'Midnight Loop',
    'Nova Lane',
    'Night Sketch',
    ARRAY['rnb', 'indie']::TEXT[],
    ARRAY['calm', 'night']::TEXT[],
    'medium',
    'existing_catalog',
    'personalized_match',
    'rnb/indie 취향과 calm/night 분위기에 직접 연결되는 곡',
    'canonical_music_catalog',
    '{"match_reason": {"genre_match": true, "mood_match": true}}'::JSONB
),
(
    'track_002',
    'track_002',
    'Soft Orbit',
    'Luna Field',
    'Orbit Notes',
    ARRAY['dream_pop', 'ambient']::TEXT[],
    ARRAY['calm', 'night']::TEXT[],
    'slow',
    'existing_catalog',
    'discovery_candidate',
    '차분한 밤 분위기를 유지하면서 dream pop 계열로 확장 가능한 곡',
    'canonical_music_catalog',
    '{"match_reason": {"mood_match": true, "new_taste_expansion": true}}'::JSONB
),
(
    'track_003',
    'track_003',
    'Fresh Signal',
    'Mira Tone',
    'Updated Signal',
    ARRAY['indie', 'electro_pop']::TEXT[],
    ARRAY['bright', 'clean']::TEXT[],
    'medium',
    'new_release',
    'new_release',
    '최근 업데이트 곡 중 indie 선호와 일부 연결되는 신보 후보',
    'canonical_music_catalog',
    '{"match_reason": {"genre_match": true, "new_taste_expansion": true}}'::JSONB
)
ON CONFLICT (content_id) DO NOTHING;
