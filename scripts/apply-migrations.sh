#!/usr/bin/env bash
# اعمال migrationها به ترتیب (000 تا 005) روی دیتابیس Supabase/Postgres
# اجرا:  DATABASE_URL='postgresql://...' bash scripts/apply-migrations.sh
set -euo pipefail
cd "$(dirname "$0")/.."
: "${DATABASE_URL:?DATABASE_URL را تنظیم کنید (Supabase → Project Settings → Database → Connection string)}"
for f in $(ls infra/postgres/migrations/*.sql | sort); do
  echo "▶ $f"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
echo "✓ همه‌ی migrationها اعمال شد"
