# WO-2026-005 — MKA-Core database baseline

## Decision record

- Canonical Supabase project reference confirmed by the owner: `jdvlzgljfodltmzvdpld`.
- `apps/mka-core/supabase/config.toml` previously pointed at `lcrqjykxjtyrlnpkzpxi`; this work branch changes the local project ID to the owner-confirmed canonical reference.
- This config edit does **not** link the CLI, push migrations, or modify the remote database.
- Production database writes and migration application are explicitly out of scope.

## Repository evidence inspected

- `apps/mka-core/src/integrations/supabase/types.ts` declares `circulars`, `memory_items`, `memory_links`, `user_roles`, `has_role`, and `search_knowledge`.
- `apps/mka-core/supabase/` currently contains only `config.toml`; no versioned migration files were found in that directory.
- The root `supabase/migrations` path was not found during repository inspection.
- The generated TypeScript types are application expectations, not proof that those tables/functions exist remotely.
- Owner-run read-only SQL for the canonical project reported the four expected tables absent and one migration record, `20260809193345`, with statements for `public.reviews`. These observations must be rechecked using the SQL companion file before schema changes are designed.

## Security issues requiring verification

1. Verify table existence, RLS and FORCE RLS state, policies, grants, and ownership for the canonical project.
2. Inspect definitions and execution grants for `search_knowledge` and `has_role`; verify `SECURITY DEFINER`, fixed `search_path`, and underlying row filtering as applicable.
3. Ensure official-knowledge retrieval cannot access private-memory rows before application-level filtering.
4. Verify memory links cannot point across users' private memories and that all write paths use authenticated identity.
5. Add integration tests only after actual schema and function definitions are known.

## Safe sequence

1. Run the read-only SQL in `WO-2026-005-live-supabase-verification.sql` in the confirmed project's SQL Editor.
2. Review the results and reconcile any manually created objects not represented in migration history.
3. Design a baseline migration against verified live state and repository conventions; do not blindly create tables based on generated types.
4. Add automated authorization/isolation tests and documentation.
5. Submit a draft PR for review. Do not merge or apply migrations without a separate explicit approval.

## Current status

Repository configuration change and read-only verification script are preparation only. Live catalog verification, migration implementation, CI, and RLS integration tests remain pending. No remote database has been changed.
