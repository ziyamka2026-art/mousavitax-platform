/**
 * Audit Log — MousaviTax AI Platform
 *
 * Append-only audit event sink. Writes to Supabase table `audit_logs`
 * with RLS policies preventing UPDATE and DELETE.
 *
 * @package packages/audit
 * @see infra/postgres/migrations/005_audit_logs.sql
 */

import type { UserContext } from '../auth/src/rbac';

export type AuditAction =
  | 'auth.login'
  | 'auth.logout'
  | 'auth.failed_login'
  | 'case.create'
  | 'case.read'
  | 'case.update'
  | 'case.delete'
  | 'case.assign'
  | 'case.status_change'
  | 'document.upload'
  | 'document.read'
  | 'document.delete'
  | 'service_request.create'
  | 'service_request.update'
  | 'knowledge_doc.create'
  | 'knowledge_doc.update'
  | 'knowledge_doc.approve'
  | 'knowledge_doc.reject'
  | 'user.create'
  | 'user.role_change'
  | 'user.tenant_change'
  | 'admin.config_change'
  | 'admin.export_data'
  | 'admin.impersonate'
  | 'ai.triage_invoked'
  | 'ai.rag_query'
  | 'ai.citation_followed'
  | 'ai.expert_escalation'
  | (string & {}); // allow custom actions

export interface AuditEvent {
  /** Required */
  action: AuditAction;
  actorId: string;          // user_id (or 'system' / 'anonymous')
  tenantId: string;         // tenant scope

  /** Resource (optional but recommended) */
  resourceType?: string;     // 'case' | 'document' | 'knowledge_doc' | ...
  resourceId?: string;       // UUID

  /** Optional context */
  metadata?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  requestId?: string;        // for cross-correlation with logs

  /** Auto-populated — do not set manually */
  timestamp?: string;       // ISO 8601
}

export interface AuditSink {
  write(event: AuditEvent): Promise<void>;
}

/**
 * Console sink — for local development.
 */
export class ConsoleAuditSink implements AuditSink {
  async write(event: AuditEvent): Promise<void> {
    const enriched = enrichEvent(event);
    // eslint-disable-next-line no-console
    console.log('[audit]', JSON.stringify(enriched));
  }
}

/**
 * Supabase sink — writes to `audit_logs` table.
 * RLS policies prevent UPDATE/DELETE — append-only guarantee at the DB layer.
 */
export class SupabaseAuditSink implements AuditSink {
  constructor(
    private readonly supabaseUrl: string,
    private readonly supabaseServiceRoleKey: string,
  ) {
    if (!supabaseUrl) throw new Error('AUDIT: SUPABASE_URL is required');
    if (!supabaseServiceRoleKey) throw new Error('AUDIT: SUPABASE_SERVICE_ROLE_KEY is required');
  }

  async write(event: AuditEvent): Promise<void> {
    const enriched = enrichEvent(event);

    const res = await fetch(`${this.supabaseUrl}/rest/v1/audit_logs`, {
      method: 'POST',
      headers: {
        apikey: this.supabaseServiceRoleKey,
        Authorization: `Bearer ${this.supabaseServiceRoleKey}`,
        'Content-Type': 'application/json',
        Prefer: 'return=minimal',
      },
      body: JSON.stringify({
        action: enriched.action,
        actor_id: enriched.actorId,
        tenant_id: enriched.tenantId,
        resource_type: enriched.resourceType ?? null,
        resource_id: enriched.resourceId ?? null,
        metadata: enriched.metadata ?? null,
        ip_address: enriched.ipAddress ?? null,
        user_agent: enriched.userAgent ?? null,
        request_id: enriched.requestId ?? null,
        timestamp: enriched.timestamp,
      }),
    });

    if (!res.ok) {
      // Audit failures should NOT silently swallow — log loudly.
      // eslint-disable-next-line no-console
      console.error('[audit] FAILED to write event', {
        status: res.status,
        action: enriched.action,
        actorId: enriched.actorId,
      });
    }
  }
}

function enrichEvent(event: AuditEvent): Required<AuditEvent> {
  return {
    ...event,
    timestamp: event.timestamp ?? new Date().toISOString(),
    metadata: event.metadata ?? {},
    ipAddress: event.ipAddress ?? null,
    userAgent: event.userAgent ?? null,
    requestId: event.requestId ?? null,
  } as Required<AuditEvent>;
}

/**
 * Lazy singleton — picks sink based on env. Falls back to console in dev.
 */
let _sink: AuditSink | null = null;

export function getAuditSink(): AuditSink {
  if (_sink) return _sink;

  const url = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (url && key && process.env.NODE_ENV === 'production') {
    _sink = new SupabaseAuditSink(url, key);
  } else {
    _sink = new ConsoleAuditSink();
  }
  return _sink;
}

/**
 * Log an audit event from a UserContext (preferred entry point).
 *
 * @example
 *   await logAudit({
 *     user, action: 'case.create', resourceType: 'case', resourceId: case.id,
 *   });
 */
export async function logAudit(
  event: Omit<AuditEvent, 'actorId' | 'tenantId'> & { user?: UserContext },
): Promise<void> {
  const { user, ...rest } = event;
  await getAuditSink().write({
    ...rest,
    actorId: user?.id ?? 'system',
    tenantId: user?.tenantId ?? 'system',
  });
}
