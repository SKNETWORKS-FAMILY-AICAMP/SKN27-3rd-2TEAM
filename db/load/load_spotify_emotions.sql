\copy spotify_emotions(track_id, primary_emotion, secondary_emotions, emotion_score_json, source_type, raw_json) FROM '/workspace/data/load/spotify_emotions_load.csv' WITH (FORMAT csv, HEADER true);
