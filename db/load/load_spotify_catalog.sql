\copy spotify_tracks(track_id, title, artist, album, genres, release_date, popularity, source_dataset, raw_json) FROM '/workspace/data/load/spotify_tracks_load.csv' WITH (FORMAT csv, HEADER true);

\copy spotify_audio_features(track_id, danceability, energy, valence, tempo_bpm, acousticness, instrumentalness, liveness, speechiness, loudness, duration_ms, raw_json) FROM '/workspace/data/load/spotify_audio_features_load.csv' WITH (FORMAT csv, HEADER true);

\copy music_catalog(content_id, track_id, title, artist, album, genres, moods, tempo, release_type, recommendation_category, evidence_summary, source_type, metadata_json) FROM '/workspace/data/load/music_catalog_load.csv' WITH (FORMAT csv, HEADER true);
