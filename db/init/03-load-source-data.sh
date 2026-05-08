#!/bin/sh
set -eu

required_files="
/workspace/seed/users.csv
/workspace/seed/kkbox_user_features.csv
/workspace/data/load/spotify_tracks_load.csv
/workspace/data/load/spotify_audio_features_load.csv
/workspace/data/load/music_catalog_load.csv
"

for file_path in $required_files; do
  if [ ! -f "$file_path" ]; then
    echo "Skipping Source Layer data load: missing $file_path"
    exit 0
  fi
done

echo "Loading KKBOX Source Layer data"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/load_kkbox_seed.sql

echo "Loading Spotify Source Layer data"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/load_spotify_catalog.sql

if [ -f "/workspace/data/load/spotify_lyrics_load.csv" ]; then
  echo "Loading optional Spotify lyrics data"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/load_spotify_lyrics.sql
else
  echo "Skipping optional Spotify lyrics data: missing /workspace/data/load/spotify_lyrics_load.csv"
fi

if [ -f "/workspace/data/load/spotify_emotions_load.csv" ]; then
  echo "Loading optional Spotify emotions data"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/load_spotify_emotions.sql
else
  echo "Skipping optional Spotify emotions data: missing /workspace/data/load/spotify_emotions_load.csv"
fi

echo "Verifying Source Layer data load"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/load/verify_source_load.sql
