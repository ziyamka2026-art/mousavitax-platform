// Vitest sample test for RBAC module
import { describe, expect, it } from 'vitest';
import {
  hasPermission,
  requirePermission,
  canAccessResource,
  AuthorizationError,
  ROLE_PERMISSIONS,
  type UserContext,
} from '../../packages/auth/src/rbac';

const user = (role: string, tenantId = 't1', id = 'u1'): UserContext => ({
  id, role: role as any, tenantId,
});

describe('RBAC', () => {
  describe('hasPermission', () => {
    it('taxpayer can create cases', () => {
      expect(hasPermission(user('taxpayer'), 'case:create')).toBe(true);
    });

    it('taxpayer cannot read other tenants cases', () => {
      expect(hasPermission(user('taxpayer'), 'case:read_tenant')).toBe(false);
    });

    it('advisor can read tenant-wide cases', () => {
      expect(hasPermission(user('advisor'), 'case:read_tenant')).toBe(true);
    });

    it('auditor cannot create cases', () => {
      expect(hasPermission(user('auditor'), 'case:create')).toBe(false);
    });

    it('admin can approve knowledge docs', () => {
      expect(hasPermission(user('admin'), 'knowledge_doc:approve')).toBe(true);
    });

    it('super_admin bypasses all checks', () => {
      expect(hasPermission(user('super_admin'), 'case:delete')).toBe(true);
      expect(hasPermission(user('super_admin'), 'system:admin')).toBe(true);
    });
  });

  describe('requirePermission', () => {
    it('throws AuthorizationError when permission missing', () => {
      expect(() => requirePermission(user('taxpayer'), 'admin:config'))
        .toThrow(AuthorizationError);
    });

    it('does not throw when permission granted', () => {
      expect(() => requirePermission(user('admin'), 'case:update'))
        .not.toThrow();
    });
  });

  describe('canAccessResource', () => {
    it('taxpayer can read own case', () => {
      expect(
        canAccessResource(
          { ...user('taxpayer', 't1', 'u1'), scopes: [] },
          'case:read_own',
          'u1',
          't1',
        )
      ).toBe(true);
    });

    it('taxpayer cannot read another user case via read_own', () => {
      expect(
        canAccessResource(
          { ...user('taxpayer', 't1', 'u1'), scopes: [] },
          'case:read_own',
          'u2',
          't1',
        )
      ).toBe(false);
    });

    it('advisor can read across tenant members', () => {
      expect(
        canAccessResource(
          { ...user('advisor', 't1', 'u_advisor'), scopes: [] },
          'case:read_tenant',
          'u_other_user',
          't1',
        )
      ).toBe(true);
    });

    it('advisor cannot cross tenant boundary', () => {
      expect(
        canAccessResource(
          { ...user('advisor', 't1', 'u_advisor'), scopes: [] },
          'case:read_tenant',
          'u_user',
          't2',
        )
      ).toBe(false);
    });
  });

  describe('role → permission map completeness', () => {
    it('all 5 roles defined', () => {
      const roles = Object.keys(ROLE_PERMISSIONS);
      expect(roles.sort()).toEqual(['admin', 'advisor', 'auditor', 'super_admin', 'taxpayer']);
    });

    it('taxpayer has 11 permissions', () => {
      expect(ROLE_PERMISSIONS.taxpayer).toHaveLength(11);
    });

    it('advisor has 10 permissions', () => {
      expect(ROLE_PERMISSIONS.advisor).toHaveLength(10);
    });

    it('auditor has 5 permissions', () => {
      expect(ROLE_PERMISSIONS.auditor).toHaveLength(5);
    });

    it('admin has 17 permissions', () => {
      expect(ROLE_PERMISSIONS.admin).toHaveLength(17);
    });
  });
});
