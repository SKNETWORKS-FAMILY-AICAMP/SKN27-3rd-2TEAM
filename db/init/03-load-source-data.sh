#!/bin/sh
set -eu

echo "Loading RIMAS v4 minimal PostgreSQL seed"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /workspace/db/seed.sql
