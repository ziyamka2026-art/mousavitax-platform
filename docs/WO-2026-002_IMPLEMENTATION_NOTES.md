# WO-2026-002 — Implementation Notes

## Scope
This document records the initial security/data-integrity hardening findings for the MousaviTax platform. It is intentionally documentation-only; no production behavior is changed by this file.

## Current P0 findings to resolve

1. Authentication and RBAC must be enforced on all sensitive API endpoints.
2. Tax Case, Case Document, Note and Service Request access must be scoped to the authenticated actor; prevent IDOR/cross-user access.
3. Replace JSONL/file persistence for production with PostgreSQL and transactional constraints.
4. Secure document upload with bounded streaming, real MIME/magic-byte validation, safe storage, malware scanning and authorization.
5. Restrict CORS to configured trusted origins; never use wildcard origins with credentials.
6. Make audit logging append-only and attributable to actor, role, action, resource and request/correlation ID.
7. RAG failures must be distinguishable from empty retrieval; insufficient evidence must not become a confident answer.
8. Citation integrity must require resolvable trusted sources; placeholders must never count as evidence.
9. Validate service codes against the Service Catalog and validate Case references and ownership.
10. Add regression/security tests for all of the above before production use.

## Execution rule
Do not treat a finding as fixed merely because a related symbol or helper exists. Verify the complete request path and add a test demonstrating the security/correctness property.

## Production gate
Real taxpayer data and sensitive documents must not be enabled until P0 security, authorization, storage and evidence-gate requirements are verified by tests and review.
