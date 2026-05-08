SELECT 'users' AS table_name, count(*) FROM users
UNION ALL SELECT 'kkbox_user_features', count(*) FROM kkbox_user_features
UNION ALL SELECT 'spotify_tracks', count(*) FROM spotify_tracks
UNION ALL SELECT 'spotify_audio_features', count(*) FROM spotify_audio_features
UNION ALL SELECT 'spotify_lyrics', count(*) FROM spotify_lyrics
UNION ALL SELECT 'spotify_emotions', count(*) FROM spotify_emotions
UNION ALL SELECT 'music_catalog', count(*) FROM music_catalog
ORDER BY table_name;

SELECT count(*) AS missing_audio_feature_fk
FROM spotify_audio_features f
LEFT JOIN spotify_tracks t ON t.track_id = f.track_id
WHERE t.track_id IS NULL;

SELECT count(*) AS missing_lyrics_fk
FROM spotify_lyrics l
LEFT JOIN spotify_tracks t ON t.track_id = l.track_id
WHERE t.track_id IS NULL;

SELECT count(*) AS missing_emotions_fk
FROM spotify_emotions e
LEFT JOIN spotify_tracks t ON t.track_id = e.track_id
WHERE t.track_id IS NULL;

SELECT track_id AS duplicate_spotify_track_id, count(*) AS duplicate_count
FROM spotify_tracks
GROUP BY track_id
HAVING count(*) > 1;

SELECT count(*) AS invalid_music_catalog_content_id
FROM music_catalog
WHERE content_id IS NULL OR content_id = '';

SELECT count(*) AS invalid_music_catalog_track_id
FROM music_catalog
WHERE track_id IS NULL OR track_id = '';

SELECT count(*) AS invalid_music_catalog_content_id_rule
FROM music_catalog
WHERE track_id IS NOT NULL
AND content_id <> ('mc_' || track_id);
