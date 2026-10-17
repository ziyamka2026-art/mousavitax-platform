# ADR-009: MKA-Core Security and Knowledge Boundaries

- Status: Proposed
- Date: 2026-10-17
- Scope: `apps/mka-core`

## Context

MKA-Core provides both an authenticated personal-memory interface and a service-to-service orchestration endpoint used by bots and the central Python platform. These callers have different trust boundaries. A shared search RPC may return both memory records and official circulars, so the public endpoint must not rely on database row-level security alone to define its source policy.

## Decision

1. The public `POST /api/public/v1/orchestrate` route calls orchestration in `official` scope. Before content reaches the model, results are explicitly filtered to `kind === "circular"`. The public response therefore does not include personal-memory records as model context or citations.
2. Authenticated `askBrain` uses `personal` scope and continues to rely on the authenticated Supabase client and database RLS for user-owned records.
3. Memory list and delete operations explicitly constrain rows by the authenticated `user_id`, in addition to RLS.
4. Browser CORS is disabled by default. If browser access is required, configure `MKA_CORE_ALLOWED_ORIGIN` to one exact origin. Server-to-server callers do not need CORS. CORS is not a replacement for the API key.
5. Public API error responses are generic; diagnostic detail is logged server-side with a trace identifier.

## Consequences

- The public endpoint may retrieve a larger candidate set before filtering so official circulars are not discarded solely because private-memory records ranked higher. It then limits the evidence set to six records.
- If the current database search RPC or RLS policy is not configured as expected, the explicit application-level source filter still prevents memory rows from being sent to the public model context.
- The authenticated personal experience remains dependent on the actual deployed RLS policies. Those policies must be reviewed in the connected Supabase project; this repository does not currently include the MKA-Core schema migrations.
- A single-origin allowlist supports at most one browser origin per deployment. Multi-origin support requires a separately reviewed configuration design.

## Validation and limitations

- Review the generated diff and CI checks in the Pull Request.
- Build/lint and authenticated cross-user tests must be run against the project's actual Bun/Supabase environment before merge.
- This ADR does not claim that database RLS has been independently verified, and it does not modify database schema or policies.
