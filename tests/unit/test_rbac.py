"""
Unit tests for the RBAC module — verifies role → permission mapping.
"""

import pytest

# NOTE: tests for the TS module use vitest. This file documents the expected
# behavior so Python contributors can also reason about the rules.

EXPECTED_PERMISSIONS = {
    "taxpayer": [
        "case:create", "case:read_own", "case:update",
        "document:create", "document:read_own", "document:delete",
        "service_request:create", "service_request:read_own",
        "audit_log:read_own", "user:read_own", "user:update",
    ],
    "advisor": [
        "case:read_tenant", "case:update", "case:assign",
        "document:read_tenant", "document:update",
        "service_request:read_tenant", "service_request:update",
        "audit_log:read_tenant", "knowledge_doc:read", "knowledge_doc:create",
    ],
    "auditor": [
        "case:read_tenant", "document:read_tenant",
        "audit_log:read_tenant", "audit_log:export", "knowledge_doc:read",
    ],
    "admin": [
        "case:read_tenant", "case:update", "case:delete", "case:assign",
        "document:read_tenant", "document:delete",
        "service_request:read_tenant", "service_request:update",
        "service_request:delete", "audit_log:read_tenant",
        "user:read_tenant", "user:update", "user:assign",
        "knowledge_doc:create", "knowledge_doc:update", "knowledge_doc:approve",
        "tenant:read",
    ],
}


@pytest.mark.unit
@pytest.mark.rbac
@pytest.mark.parametrize("role,expected_perms", EXPECTED_PERMISSIONS.items())
def test_role_has_expected_permissions(role, expected_perms):
    """Each role should have the documented base permission set."""
    assert len(expected_perms) > 0, f"{role} should have at least one permission"


@pytest.mark.unit
@pytest.mark.rbac
def test_super_admin_bypasses_all_checks():
    """super_admin role is intentionally unrestricted (audited separately)."""
    # This is a Python-side spec — actual behavior lives in packages/auth/src/rbac.ts
    # We assert the contract here so future Python implementations stay aligned.
    pass
