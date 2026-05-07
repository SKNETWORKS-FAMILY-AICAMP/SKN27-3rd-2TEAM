\copy spotify_lyrics(track_id, lyrics, language, lyrics_available, source_type, raw_json) FROM '/workspace/data/load/spotify_lyrics_load.csv' WITH (FORMAT csv, HEADER true);
