# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| latest main  | ✅ |
| tagged releases | ✅ |
| older branches | ❌ |

## Reporting a Vulnerability

**DO NOT open public GitHub issues for security vulnerabilities.**

If you discover a security vulnerability, please report it privately:

1. **Email**: `ziya.mka2026@gmail.com`
2. **Subject**: `[SECURITY] <brief description>`
3. **Body must include**:
   - Type of vulnerability (e.g., XSS, SQL injection, auth bypass)
   - Full steps to reproduce
   - Affected files/components
   - Potential impact
   - Suggested fix (optional but appreciated)

### Response Timeline

| Stage | Target SLA |
|-------|-----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 7 days |
| Fix or mitigation | Within 30 days (severity-dependent) |
| Public disclosure | After fix is released, with credit to reporter |

### Recognition

We will publicly thank security researchers in our release notes (with their
permission) and provide a `Security Contributor` badge in the README.

## Security Architecture

This platform implements defense-in-depth:

### 1. Authentication
- Supabase Auth (JWT-based)
- Bot commands require signed telegram_id verification
- Service role keys NEVER exposed to client

### 2. Authorization (RBAC)
- Role-based: `taxpayer`, `advisor`, `auditor`, `admin`, `super_admin`
- Permission-based: enforced at API entry via `withAuth()` decorator
- See `packages/auth/src/rbac.ts`

### 3. Multi-tenancy
- Every table has `tenant_id`
- Row-Level Security (RLS) at the database layer
- Cross-tenant access blocked even if app code is buggy
- See `infra/postgres/migrations/001_tenants.sql`

### 4. Audit Trail
- Append-only `audit_logs` table
- UPDATE/DELETE blocked by RLS for non-super-admins
- See `infra/postgres/migrations/002_audit_logs.sql`

### 5. Knowledge Integrity
- Knowledge docs go through approval workflow
- Only `approved` docs are indexed in vector store
- Version tracking prevents silent content swaps
- See `infra/postgres/migrations/003_knowledge_documents.sql`

### 6. Secrets Management
- `.env.local` is in `.gitignore` (since v0.x)
- Production secrets in Vercel Environment Variables
- Service role keys rotated on schedule

## Security Best Practices for Contributors

- ✅ Use `process.env.SECRET_NAME` — never hardcode
- ✅ Mark client-side vars with `NEXT_PUBLIC_` prefix ONLY for non-sensitive
- ✅ Validate all user input with Zod / Pydantic
- ✅ Use parameterized queries — never string-concat SQL
- ✅ Sanitize HTML output (use DOMPurify in client)
- ✅ Test the negative path (unauthorized user should get 403, not 200)
- ❌ Never log secrets, tokens, PII at any log level
- ❌ Never disable RLS "for testing" — use a service role key instead
- ❌ Never commit `.env.*` files (only `.env.example` is allowed)

## Incident Response

If a security breach is suspected:

1. **Immediately rotate** all exposed secrets (Supabase, OpenAI, Google)
2. **Audit** `audit_logs` table for suspicious activity
3. **Notify** affected tenants within 72 hours (legal requirement in some jurisdictions)
4. **Post-mortem** written and shared within the team

## Dependency Security

- CI runs `npm audit` and `pip-audit` on every PR
- Dependabot alerts enabled on GitHub
- Critical CVEs must be patched within 7 days
- High CVEs within 14 days
- Medium CVEs within 30 days

## Contact

- **Security email**: `ziya.mka2026@gmail.com`
- **PGP key**: available on request
