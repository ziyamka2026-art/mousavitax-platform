/**
 * Session helpers — extract authenticated user from request context.
 *
 * Currently uses Supabase Auth. Can be extended for SSO/OIDC later.
 *
 * @package packages/auth
 */

import type { UserContext, Role } from './rbac';

const ROLE_CLAIM = 'app_role' as const;
const TENANT_CLAIM = 'app_tenant_id' as const;

/**
 * Decode the Supabase access token from a Request and produce a UserContext.
 *
 * Note: This DOES NOT verify the JWT signature — verification MUST happen
 * at the Supabase API gateway or via `@supabase/supabase-js` server client
 * with the service role key.
 */
export async function getUserFromRequest(req: Request): Promise<UserContext | null> {
  const auth = req.headers.get('authorization');
  if (!auth?.startsWith('Bearer ')) return null;

  const token = auth.slice('Bearer '.length).trim();
  const payload = decodeJwtUnverified(token);
  if (!payload) return null;

  return {
    id: payload.sub as string,
    role: (payload[ROLE_CLAIM] as Role) ?? 'taxpayer',
    tenantId: (payload[TENANT_CLAIM] as string) ?? payload.sub as string,
  };
}

/**
 * Decode a JWT without verifying signature — for extracting claims only.
 * Use only when you've already validated the token upstream.
 */
function decodeJwtUnverified(token: string): Record<string, unknown> | null {
  try {
    const [, payloadB64] = token.split('.');
    if (!payloadB64) return null;
    const json = Buffer.from(payloadB64, 'base64url').toString('utf-8');
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export interface SetUserContextOptions {
  userId: string;
  role: Role;
  tenantId: string;
  metadata?: Record<string, unknown>;
}

/**
 * Helper to create a fresh UserContext (e.g., after sign-in).
 */
export function createUserContext(opts: SetUserContextOptions): UserContext {
  return {
    id: opts.userId,
    role: opts.role,
    tenantId: opts.tenantId,
    scopes: [],
  };
}
