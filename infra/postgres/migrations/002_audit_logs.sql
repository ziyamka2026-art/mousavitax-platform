-- =============================================================================
-- MousaviTax — 002: Audit Logs (append-only)
-- =============================================================================
-- Every security-relevant action writes a row here. RLS forbids UPDATE/DELETE
-- — only INSERT is permitted for non-super-admins.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    action          TEXT NOT NULL,
    actor_id        UUID,                       -- nullable for system/anonymous
    tenant_id       UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
    resource_type   TEXT,
    resource_id     TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::JSONB,
    ip_address      INET,
    user_agent      TEXT,
    request_id      TEXT,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor     ON public.audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant    ON public.audit_logs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action    ON public.audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource  ON public.audit_logs (resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ts       ON public.audit_logs (timestamp DESC);

-- ============================================================================
-- RLS: append-only at the database layer
-- ============================================================================

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Anyone can read their own tenant's audit log
CREATE POLICY audit_read_own_tenant ON public.audit_logs
    FOR SELECT
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles
            WHERE user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_id = auth.uid() AND role IN ('admin', 'super_admin')
        )
    );

-- Only allow INSERT (no UPDATE, no DELETE) for everyone except super_admin
CREATE POLICY audit_insert ON public.audit_logs
    FOR INSERT
    WITH CHECK (TRUE);

-- Super admins can UPDATE/DELETE (for data-correction scenarios only)
CREATE POLICY audit_admin_update ON public.audit_logs
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_id = auth.uid() AND role = 'super_admin'
        )
    );

CREATE POLICY audit_admin_delete ON public.audit_logs
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_id = auth.uid() AND role = 'super_admin'
        )
    );

-- Block UPDATE for everyone else (only super_admin policy above allows it)
REVOKE UPDATE ON public.audit_logs FROM PUBLIC;
GRANT INSERT, SELECT ON public.audit_logs TO authenticated;
