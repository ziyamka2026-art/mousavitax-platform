#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/apps/api/app:$ROOT/packages/shared:$ROOT/packages/ai-gateway/app:$ROOT/packages/taxlaw-engine:$ROOT/packages/prompt-engine:$ROOT/packages/knowledge-core:$ROOT/packages/embedding-service/app:$ROOT/packages/retrieval-engine/app:$ROOT/packages/document-parser${PYTHONPATH:+:$PYTHONPATH}"
export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8000}"
export BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
export WEB_PUBLIC_URL="${WEB_PUBLIC_URL:-http://localhost:3000}"
export VECTOR_DB_PATH="${VECTOR_DB_PATH:-$ROOT/data/iran_tax_vectors.json}"
export EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER:-fallback}"

mkdir -p "$ROOT/data"

cleanup() {
  kill "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting MousaviTax API on :$API_PORT"
(
  cd "$ROOT/apps/api"
  python -m uvicorn app.main:app --host "$API_HOST" --port "$API_PORT"
) &
API_PID=$!

echo "Starting MousaviTax Web on :3000"
(
  cd "$ROOT/apps/web"
  npm run dev -- --hostname 0.0.0.0 --port 3000
) &
WEB_PID=$!

echo "MousaviTax is starting: Web=http://localhost:3000 API=http://localhost:8000"
wait -n "$API_PID" "$WEB_PID"
