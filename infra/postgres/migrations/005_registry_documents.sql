-- =============================================================================
-- MousaviTax — 005: registry_documents table + RLS policies
-- =============================================================================
-- Fixes the critical "new row violates row-level security policy" error
-- reported in the Registry screen.
--
-- Before this migration, INSERT into registry_documents was rejected by RLS
-- because no INSERT policy existed for authenticated users.
-- =============================================================================

-- ============================================================================
-- 1. Create the table if it doesn't exist
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.registry_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Document identity
    code            TEXT NOT NULL UNIQUE,             -- MKA-LAW-001 format
    title           TEXT NOT NULL,                    -- dedicated title field
    source_type     TEXT NOT NULL DEFAULT 'web'
                    CHECK (source_type IN ('web', 'drive', 'upload', 'manual', 'api')),
    source_url      TEXT,                             -- URL or Drive file ID
    source_ref      TEXT,                             -- human-readable path / file name

    -- Document content
    content         TEXT,
    summary         TEXT,
    expert_notes    TEXT,
    extracted_text  TEXT,

    -- Workflow status
    status          TEXT NOT NULL DEFAULT 'unidentified'
                    CHECK (status IN (
                        'unidentified', 'identified', 'reviewed',
                        'approved', 'rejected', 'archived'
                    )),

    -- Type code (for auto-generated document code)
    type_code       TEXT,                             -- 'LAW' | 'CIR' | 'JUD' | 'CNT' | 'APL' | 'TAX'

    -- Sequential number per tenant+type (for code generation)
    sequence_num    INT NOT NULL,

    -- Metadata
    metadata        JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_registry_tenant       ON public.registry_documents (tenant_id);
CREATE INDEX IF NOT EXISTS idx_registry_user         ON public.registry_documents (user_id);
CREATE INDEX IF NOT EXISTS idx_registry_status       ON public.registry_documents (status);
CREATE INDEX IF NOT EXISTS idx_registry_type        ON public.registry_documents (type_code);
CREATE INDEX IF NOT EXISTS idx_registry_seq          ON public.registry_documents (tenant_id, type_code, sequence_num);
CREATE INDEX IF NOT EXISTS idx_registry_metadata     ON public.registry_documents USING GIN (metadata);

-- Search index on title + content + summary
CREATE INDEX IF NOT EXISTS idx_registry_search
    ON public.registry_documents
    USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, '') || ' ' || coalesce(summary, '')));

-- ============================================================================
-- 2. Sequence counter table — for auto-generating MKA-TYPE-001 codes
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.registry_sequences (
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    type_code       TEXT NOT NULL,
    next_seq        INT NOT NULL DEFAULT 1,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, type_code)
);

-- ============================================================================
-- 3. Function: generate_document_code(tenant_id, type_code)
--    Atomically allocates the next sequence number and returns "MKA-TYPE-NNN"
-- ============================================================================
CREATE OR REPLACE FUNCTION public.generate_document_code(
    p_tenant_id UUID,
    p_type_code TEXT
) RETURNS TEXT AS $$
DECLARE
    v_next INT;
    v_code TEXT;
BEGIN
    -- Upsert the sequence row and atomically increment
    INSERT INTO public.registry_sequences (tenant_id, type_code, next_seq)
    VALUES (p_tenant_id, p_type_code, 2)
    ON CONFLICT (tenant_id, type_code)
    DO UPDATE SET next_seq = registry_sequences.next_seq + 1,
                  updated_at = NOW()
    RETURNING next_seq - 1 INTO v_next;

    -- Format: MKA-LAW-001, MKA-CIR-002, ...
    v_code := 'MKA-' || UPPER(p_type_code) || '-' || LPAD(v_next::TEXT, 3, '0');
    RETURN v_code;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- 4. RLS Policies — THE CRITICAL FIX
-- ============================================================================
-- Before this migration, no INSERT policy existed → every INSERT failed
-- with "new row violates row-level security policy".
-- ============================================================================

ALTER TABLE public.registry_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registry_sequences  ENABLE ROW LEVEL SECURITY;

-- Drop existing policies (idempotent)
DROP POLICY IF EXISTS registry_read_own_tenant      ON public.registry_documents;
DROP POLICY IF EXISTS registry_insert_own_tenant    ON public.registry_documents;
DROP POLICY IF EXISTS registry_update_own_tenant    ON public.registry_documents;
DROP POLICY IF EXISTS registry_delete_own_tenant    ON public.registry_documents;
DROP POLICY IF EXISTS registry_seq_read             ON public.registry_sequences;
DROP POLICY IF EXISTS registry_seq_upsert           ON public.registry_sequences;

-- 4.1 SELECT — users can read documents in their own tenant
CREATE POLICY registry_read_own_tenant ON public.registry_documents
    FOR SELECT
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles
            WHERE user_id = auth.uid()
        )
        AND deleted_at IS NULL
    );

-- 4.2 INSERT — THE FIX: authenticated users can insert into their own tenant
CREATE POLICY registry_insert_own_tenant ON public.registry_documents
    FOR INSERT
    WITH CHECK (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles
            WHERE user_id = auth.uid()
        )
        AND user_id = auth.uid()
    );

-- 4.3 UPDATE — owner can update their own docs, admins can update any in tenant
CREATE POLICY registry_update_own_tenant ON public.registry_documents
    FOR UPDATE
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles
            WHERE user_id = auth.uid()
        )
        AND (
            user_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM public.user_profiles
                WHERE user_id = auth.uid() AND role IN ('admin', 'super_admin')
            )
        )
    );

-- 4.4 DELETE — only admin+ can delete (soft delete recommended)
CREATE POLICY registry_delete_own_tenant ON public.registry_documents
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_id = auth.uid()
            AND role IN ('admin', 'super_admin')
            AND tenant_id = registry_documents.tenant_id
        )
    );

-- 4.5 Sequence policies — any authenticated user in the tenant can read/upsert
CREATE POLICY registry_seq_read ON public.registry_sequences
    FOR SELECT
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY registry_seq_upsert ON public.registry_sequences
    FOR INSERT
    WITH CHECK (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY registry_seq_update ON public.registry_sequences
    FOR UPDATE
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles
            WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- 5. Trigger: auto-update timestamp
-- ============================================================================
DROP TRIGGER IF EXISTS trg_registry_touch ON public.registry_documents;
CREATE TRIGGER trg_registry_touch BEFORE UPDATE ON public.registry_documents
    FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

-- ============================================================================
-- 6. Trigger: auto-fill sequence_num + code on INSERT (if not provided)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.auto_fill_registry_code()
RETURNS TRIGGER AS $$
DECLARE
    v_code TEXT;
BEGIN
    IF NEW.code IS NULL OR NEW.code = '' THEN
        -- Use type_code (default 'GEN' for general)
        v_code := public.generate_document_code(
            NEW.tenant_id,
            COALESCE(NEW.type_code, 'GEN')
        );
        NEW.code := v_code;
        NEW.type_code := COALESCE(NEW.type_code, 'GEN');
        NEW.sequence_num := (
            SELECT next_seq - 1 FROM public.registry_sequences
            WHERE tenant_id = NEW.tenant_id AND type_code = NEW.type_code
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_registry_auto_code ON public.registry_documents;
CREATE TRIGGER trg_registry_auto_code BEFORE INSERT ON public.registry_documents
    FOR EACH ROW EXECUTE FUNCTION public.auto_fill_registry_code();

-- ============================================================================
-- 7. Audit trigger: log every status transition
-- ============================================================================
CREATE OR REPLACE FUNCTION public.registry_status_audit()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO public.audit_logs
            (action, actor_id, tenant_id, resource_type, resource_id, metadata)
        VALUES (
            'registry.status_change',
            auth.uid(),
            NEW.tenant_id,
            'registry_document',
            NEW.id::TEXT,
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'code', NEW.code
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_registry_status_audit ON public.registry_documents;
CREATE TRIGGER trg_registry_status_audit AFTER UPDATE ON public.registry_documents
    FOR EACH ROW WHEN (NEW.status IS DISTINCT FROM OLD.status)
    EXECUTE FUNCTION public.registry_status_audit();

-- ============================================================================
-- 8. Grant permissions
-- ============================================================================
GRANT SELECT, INSERT, UPDATE ON public.registry_documents TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.registry_sequences  TO authenticated;
GRANT EXECUTE ON FUNCTION public.generate_document_code(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.auto_fill_registry_code()         TO authenticated;
GRANT EXECUTE ON FUNCTION public.registry_status_audit()          TO authenticated;
