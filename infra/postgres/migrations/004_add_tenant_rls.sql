-- =============================================================================
-- MousaviTax — 004: Add tenant_id and RLS to existing tables
-- =============================================================================
-- This migration adds `tenant_id` to legacy tables and enables RLS.
-- Run AFTER 001_tenants.sql and 002_audit_logs.sql.
-- =============================================================================

-- ============================================================================
-- tax_cases — already exists from earlier migration; add tenant_id + RLS
-- ============================================================================
ALTER TABLE public.tax_cases
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES public.tenants(id);

ALTER TABLE public.tax_cases
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_tax_cases_tenant ON public.tax_cases (tenant_id);

ALTER TABLE public.tax_cases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tax_cases_read_own_tenant ON public.tax_cases;
CREATE POLICY tax_cases_read_own_tenant ON public.tax_cases
    FOR SELECT
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid()
        )
        AND deleted_at IS NULL
    );

DROP POLICY IF EXISTS tax_cases_insert_own_tenant ON public.tax_cases;
CREATE POLICY tax_cases_insert_own_tenant ON public.tax_cases
    FOR INSERT
    WITH CHECK (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS tax_cases_update_own_tenant ON public.tax_cases;
CREATE POLICY tax_cases_update_own_tenant ON public.tax_cases
    FOR UPDATE
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- legal_workflows, workflow_events, workflow_artifacts, workflow_gates
-- ============================================================================
ALTER TABLE public.legal_workflows
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES public.tenants(id);
ALTER TABLE public.workflow_events
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES public.tenants(id);
ALTER TABLE public.workflow_artifacts
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES public.tenants(id);
ALTER TABLE public.workflow_gates
    ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES public.tenants(id);

CREATE INDEX IF NOT EXISTS idx_legal_workflows_tenant ON public.legal_workflows (tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_events_tenant ON public.workflow_events (tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_artifacts_tenant ON public.workflow_artifacts (tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_gates_tenant ON public.workflow_gates (tenant_id);

-- Enable RLS on all workflow tables
ALTER TABLE public.legal_workflows    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_events     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_artifacts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_gates     ENABLE ROW LEVEL SECURITY;

-- Generic policy template — applies to all workflow tables
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'legal_workflows', 'workflow_events', 'workflow_artifacts', 'workflow_gates'
    ] LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I_read_own_tenant ON %I;', tbl, tbl);
        EXECUTE format(
            'CREATE POLICY %I_read_own_tenant ON %I FOR SELECT USING (
                tenant_id = (SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid())
            );',
            tbl, tbl
        );
        EXECUTE format('DROP POLICY IF EXISTS %I_insert_own_tenant ON %I;', tbl, tbl);
        EXECUTE format(
            'CREATE POLICY %I_insert_own_tenant ON %I FOR INSERT WITH CHECK (
                tenant_id = (SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid())
            );',
            tbl, tbl
        );
        EXECUTE format('DROP POLICY IF EXISTS %I_update_own_tenant ON %I;', tbl, tbl);
        EXECUTE format(
            'CREATE POLICY %I_update_own_tenant ON %I FOR UPDATE USING (
                tenant_id = (SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid())
            );',
            tbl, tbl
        );
    END LOOP;
END $$;
