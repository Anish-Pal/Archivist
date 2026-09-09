#!/usr/bin/env bash
# Container entrypoint: validate config, resolve storage, migrate, then serve.
set -euo pipefail

PORT="${PORT:-7860}"

# ---------------------------------------------------------------------------
# Required secrets
# ---------------------------------------------------------------------------
missing=()
[ -n "${DB_URL:-}" ]        || missing+=("DB_URL")
[ -n "${GROQ_API_KEY:-}" ]  || missing+=("GROQ_API_KEY")

if [ ${#missing[@]} -gt 0 ]; then
    echo "FATAL: missing required environment variable(s): ${missing[*]}" >&2
    echo "Set them under Settings -> Variables and secrets in the Space." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Storage
#
# Persistent storage is mounted at /data. Without it the Space still runs, but
# uploads and the Chroma index are lost on every restart, so say so loudly.
# ---------------------------------------------------------------------------
export DATA_FOLDER="${DATA_FOLDER:-/data/uploads}"
export CHROMA_DB_PATH="${CHROMA_DB_PATH:-/data/chroma_db}"

if [ -d /data ] && [ -w /data ]; then
    echo "storage: persistent volume at /data"
else
    # Only paths under the missing mount are relocated; an explicit override
    # pointing somewhere else is left as the operator configured it.
    case "$DATA_FOLDER" in
        /data/*) DATA_FOLDER="$HOME/app-storage/uploads" ;;
    esac
    case "$CHROMA_DB_PATH" in
        /data/*) CHROMA_DB_PATH="$HOME/app-storage/chroma_db" ;;
    esac
    export DATA_FOLDER CHROMA_DB_PATH
    echo "storage: WARNING - no writable /data mount; falling back to ephemeral paths."
    echo "storage: uploaded documents and the vector index will be lost on restart."
fi

mkdir -p "$DATA_FOLDER" "$CHROMA_DB_PATH"
echo "storage: DATA_FOLDER=$DATA_FOLDER CHROMA_DB_PATH=$CHROMA_DB_PATH"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
echo "db: bootstrapping schema"
bootstrap_output="$(python docker/bootstrap_db.py)"
echo "$bootstrap_output"

if echo "$bootstrap_output" | grep -q "STRATEGY=stamp"; then
    alembic stamp head
else
    alembic upgrade head
fi
echo "db: schema ready"

# ---------------------------------------------------------------------------
# Serve
#
# Single worker only: the per-user BM25 indexes live in app.state and are built
# once at startup, so a second worker would serve a stale retrieval set.
# ---------------------------------------------------------------------------
exec uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1 \
    --timeout-keep-alive 75 \
    --proxy-headers \
    --forwarded-allow-ips '*'
