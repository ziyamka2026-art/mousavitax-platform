# Contributing to MousaviTax AI Platform

First off, thanks for taking the time to contribute! 🎉

This document outlines how to get started and the standards we expect.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
be respectful, constructive, and inclusive. Personal attacks, harassment, or
discrimination will not be tolerated.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/mousavitax-platform.git
   cd mousavitax-platform
   ```
3. **Add upstream remote** (to stay in sync):
   ```bash
   git remote add upstream https://github.com/ziyamka2026-art/mousavitax-platform.git
   ```
4. **Install dependencies** (see [README.md](README.md#quick-start-۵-دقیقه))
5. **Create a feature branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```

## Branch Naming

Follow this convention:

| Prefix | Use |
|--------|-----|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `refactor/` | Code refactoring (no behavior change) |
| `test/` | Adding tests |
| `chore/` | Build, CI, tooling |
| `wo/` | Work order (internal: `wo/2026-NNN-description`) |

Examples:
- `feat/knowledge-approval-ui`
- `fix/audit-log-rls-policy`
- `docs/update-readme-quickstart`

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation
- `refactor` — code refactoring
- `test` — adding tests
- `chore` — build, tooling, dependencies
- `ci` — CI/CD changes
- `perf` — performance improvement
- `style` — formatting only (no logic change)

### Examples

```
feat(rbac): add super_admin bypass with audit hook

- super_admin role now bypasses all permission checks
- every bypass triggers an `admin.bypass` audit event
- updated tests in tests/unit/rbac.test.ts

Closes #142
```

```
fix(api): correct SUPABASE_URL format in env example

The example showed the dashboard URL, not the API URL. Now it shows
the correct format: https://<project-ref>.supabase.co
```

## Pull Request Process

1. **Ensure CI is green** — all jobs in `.github/workflows/ci.yml` must pass
2. **Update documentation** if your change affects user-facing behavior
3. **Add tests** — every PR should include tests for new functionality
4. **Keep PRs small** — ideally <500 lines of diff
5. **Write a clear description** — what, why, how

### PR Template

```markdown
## What does this PR do?
<!-- Brief description -->

## Why is this change needed?
<!-- Link to issue, business reason -->

## How was it tested?
- [ ] Unit tests added/updated
- [ ] Integration tests (if applicable)
- [ ] Manual testing (describe steps)

## Screenshots / Demo
<!-- If UI change -->

## Checklist
- [ ] CI is green
- [ ] Tests added
- [ ] Docs updated
- [ ] No secrets in code
- [ ] Commit messages follow Conventional Commits
```

## Code Style

### TypeScript

- **Strict mode** is on — no `any` without explicit reason
- **ESLint + Prettier** — run `npm run lint` before commit
- **Type imports** — use `import type { ... }` for type-only imports
- **Naming**: `camelCase` for vars, `PascalCase` for types/components
- **No `console.log`** in production code — use `logger.info()` from `@mousavitax/observability`

### Python

- **Ruff** for linting and formatting — run `ruff check . && ruff format .`
- **Type hints** required on all public functions
- **Pydantic** for data validation at API boundaries
- **Naming**: `snake_case` for functions and vars, `PascalCase` for classes
- **No `print()`** in production code — use `logging` module

### Shared

- **No commented-out code** in PRs
- **No `TODO` without an issue link** — `TODO(#142): ...`
- **Tests live next to source** — `tests/` mirrors `apps/` and `packages/`

## Testing

| Layer | Tool | Where |
|-------|------|-------|
| Unit (TS) | Vitest | `tests/unit/*.test.ts` |
| Unit (Python) | pytest | `tests/unit/test_*.py` |
| Integration | pytest + httpx | `tests/integration/` |
| E2E | Playwright | `tests/e2e/` |
| Load | k6 | `tests/load/` |
| Security | bandit, npm audit, pip-audit | CI runs automatically |

### Running Tests

```bash
# All unit tests
pytest tests/unit -v
npx vitest run

# With coverage
pytest tests/unit --cov=apps/api --cov=packages --cov-report=html
npx vitest run --coverage

# Watch mode (TS)
npx vitest
```

## Database Migrations

All schema changes go through versioned SQL files in `infra/postgres/migrations/`:

- Naming: `NNN_description.sql` (e.g., `004_add_audit_log_index.sql`)
- Each migration must be **idempotent** (use `IF NOT EXISTS`)
- Each migration must be **reversible** — include `-- DROP` comments
- Test locally before PR:
  ```bash
  psql "$DATABASE_URL" -f infra/postgres/migrations/004_your_migration.sql
  ```

## Adding a New LLM Provider

1. Implement `LLMProvider` interface in `apps/api/app/llm/factory.py`
2. Add provider option to `.env.example` and the factory `get_llm()` switch
3. Add unit tests in `tests/unit/test_llm_factory.py`
4. Update docs in `README.md` Quick Start section

## Adding a New RBAC Role

1. Add role to `Role` type in `packages/auth/src/rbac.ts`
2. Add `ROLE_PERMISSIONS[role]` mapping
3. Update `user_profiles.role` CHECK constraint in SQL migration
4. Add unit tests in `tests/unit/rbac.test.ts`
5. Update `docs/adr/` with a new ADR explaining the role's purpose

## Architecture Decision Records (ADRs)

For significant architectural decisions, create an ADR:

- Location: `docs/adr/ADR-NNN-<title>.md`
- Format: see `docs/adr/ADR-007-Hybrid-AI-Tax-Platform.md`
- Numbering: incremental, never reuse

## Release Process

1. Update `CHANGELOG.md` with changes since last release
2. Tag: `git tag -a v0.X.Y -m "Release v0.X.Y"`
3. Push tags: `git push --tags`
4. GitHub Release will auto-build

## Questions?

- **Discussions**: [GitHub Discussions](https://github.com/ziyamka2026-art/mousavitax-platform/discussions)
- **Email**: `ziya.mka2026@gmail.com`
- **Telegram channel**: to be announced

Thanks again for contributing! 🙏
