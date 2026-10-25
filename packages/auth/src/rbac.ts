/**
 * RBAC (Role-Based Access Control) — MousaviTax AI Platform
 *
 * Implements role → permissions mapping and helpers for guard checks
 * across API routes, server components, and bot commands.
 *
 * @package packages/auth
 * @see ADR-007 (Hybrid AI Tax Platform) — security requirements
 */

export type Role =
  | 'taxpayer'      // مودی — owns their cases
  | 'advisor'      // مشاور رسمی — handles assigned cases
  | 'auditor'      // حسابرس — read-only access to cases
  | 'admin'        // ادمین سیستم
  | 'super_admin'; // ادمین ارشد — full access

export type Resource =
  | 'case'
  | 'document'
  | 'service_request'
  | 'audit_log'
  | 'user'
  | 'knowledge_doc'
  | 'tenant'
  | 'system';

export type Action =
  | 'create'
  | 'read'
  | 'read_own'      // only own resources
  | 'read_tenant'   // only within own tenant
  | 'update'
  | 'delete'
  | 'approve'
  | 'assign'
  | 'export'
  | 'admin';

export type Permission = `${Resource}:${Action}`;

/**
 * Static role → permission map. In production, this should be hydrated from
 * a database-backed permission table for runtime updates without redeploy.
 */
export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  taxpayer: [
    'case:create',
    'case:read_own',
    'case:update',
    'document:create',
    'document:read_own',
    'document:delete',
    'service_request:create',
    'service_request:read_own',
    'audit_log:read_own',
    'user:read_own',
    'user:update',
  ],
  advisor: [
    'case:read_tenant',
    'case:update',
    'case:assign',
    'document:read_tenant',
    'document:update',
    'service_request:read_tenant',
    'service_request:update',
    'audit_log:read_tenant',
    'knowledge_doc:read',
    'knowledge_doc:create',
  ],
  auditor: [
    'case:read_tenant',
    'document:read_tenant',
    'audit_log:read_tenant',
    'audit_log:export',
    'knowledge_doc:read',
  ],
  admin: [
    'case:read_tenant',
    'case:update',
    'case:delete',
    'case:assign',
    'document:read_tenant',
    'document:delete',
    'service_request:read_tenant',
    'service_request:update',
    'service_request:delete',
    'audit_log:read_tenant',
    'user:read_tenant',
    'user:update',
    'user:assign',
    'knowledge_doc:create',
    'knowledge_doc:update',
    'knowledge_doc:approve',
    'tenant:read',
  ],
  super_admin: [
    // super_admin bypasses all checks — see `hasPermission()`
    'system:admin',
  ],
};

export interface UserContext {
  id: string;
  role: Role;
  tenantId: string;
  scopes?: string[];
}

export class AuthorizationError extends Error {
  constructor(
    public readonly required: Permission,
    public readonly userId: string,
  ) {
    super(`Permission denied: user ${userId} lacks ${required}`);
    this.name = 'AuthorizationError';
  }
}

/**
 * Check if a user has a specific permission.
 * super_admin always returns true (with audit hook — see packages/audit).
 *
 * @example
 *   if (!hasPermission(user, 'case:read_own')) {
 *     throw new AuthorizationError('case:read_own', user.id);
 *   }
 */
export function hasPermission(user: UserContext, permission: Permission): boolean {
  if (user.role === 'super_admin') {
    return true;
  }
  const allowed = ROLE_PERMISSIONS[user.role] ?? [];
  return allowed.includes(permission);
}

/**
 * Require a permission — throws AuthorizationError if not granted.
 */
export function requirePermission(user: UserContext, permission: Permission): void {
  if (!hasPermission(user, permission)) {
    throw new AuthorizationError(permission, user.id);
  }
}

/**
 * Check ownership: user can access resource if they own it OR have tenant-wide scope.
 */
export function canAccessResource(
  user: UserContext,
  permission: Permission,
  resourceOwnerId?: string,
  resourceTenantId?: string,
): boolean {
  if (!hasPermission(user, permission)) return false;

  // tenant-wide permissions: resourceTenant must match user.tenant
  if (permission.endsWith(':read_tenant') || permission.endsWith(':read')) {
    if (resourceTenantId && resourceTenantId !== user.tenantId) return false;
    return true;
  }

  // own-scoped permissions: resource must belong to user
  if (permission.endsWith(':read_own')) {
    return resourceOwnerId === user.id;
  }

  return true;
}

/**
 * Decorator for API routes — use with Next.js App Router handlers.
 *
 * @example
 *   export const POST = withAuth('case:create', async (req, ctx) => { ... });
 */
export function withAuth<T extends (...args: any[]) => any>(
  permission: Permission,
  handler: T,
): T {
  return (async (...args: Parameters<T>) => {
    // Import dynamically to avoid circular dependency in edge runtime
    const { getUserFromRequest } = await import('./session');
    const user = await getUserFromRequest(args[0]);
    if (!user) {
      return new Response('Unauthorized', { status: 401 });
    }
    try {
      requirePermission(user, permission);
    } catch (e) {
      if (e instanceof AuthorizationError) {
        return new Response('Forbidden', { status: 403 });
      }
      throw e;
    }
    return handler(...args);
  }) as T;
}

export default {
  ROLE_PERMISSIONS,
  hasPermission,
  requirePermission,
  canAccessResource,
  withAuth,
  AuthorizationError,
};
