#!/usr/bin/env bash
# راه‌اندازی محلی MousaviTax: API (FastAPI) + وب (Next.js)
# اجرا از ریشه‌ی مخزن:  bash scripts/start-local.sh
set -euo pipefail
cd "$(dirname "$0")/.."

[ -f .env ] || { cp .env.example .env; echo "⚠ فایل .env از .env.example ساخته شد؛ مقادیر Supabase را در آن وارد کنید."; }
set -a; . ./.env; set +a

export EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER:-fallback}"
export VECTOR_DB_PATH="${VECTOR_DB_PATH:-$PWD/data/iran_tax_vectors.json}"
export PYTHONPATH="$PWD/packages/shared:$PWD/packages/ai-gateway/app:$PWD/packages:$PWD/services"

python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
pip install -q -r apps/api/requirements.txt
python scripts/seed_knowledge.py

( cd apps/web && [ -d node_modules ] || npm install --no-audit --no-fund )

echo "▶ API  : http://localhost:8000/health"
echo "▶ Web  : http://localhost:3000"
( cd apps/api && uvicorn app.main:app --port 8000 ) &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT
cd apps/web && npm run dev
