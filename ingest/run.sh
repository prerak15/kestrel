#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

if [ $# -ne 1 ] || [ ! -d "$1" ]; then
    echo "usage: ingest/run.sh <folder containing Posts.xml>" >&2
    exit 1
fi

set -a; source deploy/.env; set +a
export PGPASSWORD="$POSTGRES_PASSWORD"


psql -h localhost -U prerak -d kestrel -v ON_ERROR_STOP=1 -f ingest/schema.sql
uv run python ingest/load_dump.py "$1"
psql -h localhost -U prerak -d kestrel -v ON_ERROR_STOP=1 -f ingest/indexes.sql
