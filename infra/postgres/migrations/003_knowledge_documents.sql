-- =============================================================================
-- MousaviTax — 003: Knowledge Documents (RAG with approval workflow)
-- =============================================================================
-- Knowledge is the source of truth for the RAG system. Every document goes
-- through a review workflow before being indexed.
--
-- Lifecycle:  draft -> in_review -> approved | rejected -> (archived)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.knowledge_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,

    -- Identity
    title           TEXT NOT NULL,
    source_url      TEXT NOT NULL,                     -- official source URL
    source_type     TEXT NOT NULL DEFAULT 'web'
                    CHECK (source_type IN ('web', 'pdf', 'drive', 'manual')),

    -- Content
    content         TEXT NOT NULL,
    chunk_count     INT NOT NULL DEFAULT 0,
    embedding_model TEXT,                              -- e.g. 'text-embedding-3-small'

    -- Approval workflow
    status          TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'in_review', 'approved', 'rejected', 'archived')),
    submitted_by    UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    submitted_at    TIMESTAMPTZ,
    reviewed_by     UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reviewed_at     TIMESTAMPTZ,
    review_notes    TEXT,

    -- Versioning
    version         INT NOT NULL DEFAULT 1,
    supersedes_id   UUID REFERENCES public.knowledge_documents(id) ON DELETE SET NULL,

    -- Tags (array, indexed via GIN)
    tags            TEXT[] NOT NULL DEFAULT '{}',

    -- Embedding vector (1536 dims for OpenAI text-embedding-3-small)
    -- Adjust dimension if you use a different embedding model.
    embedding       VECTOR(1536),

    -- Metadata
    metadata        JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_kd_tenant      ON public.knowledge_documents (tenant_id);
CREATE INDEX IF NOT EXISTS idx_kd_status     ON public.knowledge_documents (status);
CREATE INDEX IF NOT EXISTS idx_kd_reviewed  ON public.knowledge_documents (reviewed_by);
CREATE INDEX IF NOT EXISTS idx_kd_tags       ON public.knowledge_documents USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_kd_metadata    ON public.knowledge_documents USING GIN (metadata);

-- HNSW index for fast ANN search (Postgres 16+)
CREATE INDEX IF NOT EXISTS idx_kd_embedding
    ON public.knowledge_documents
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- RLS: tenant-isolated; reviewers see all in_review within tenant
-- ============================================================================
ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY kd_read_own_tenant ON public.knowledge_documents
    FOR SELECT
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid()
        )
        AND status = 'approved'
        AND deleted_at IS NULL
    );

CREATE POLICY kd_advisor_insert ON public.knowledge_documents
    FOR INSERT
    WITH CHECK (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid()
        )
        AND submitted_by = auth.uid()
    );

CREATE POLICY kd_author_update ON public.knowledge_documents
    FOR UPDATE
    USING (
        submitted_by = auth.uid()
        AND status IN ('draft', 'in_review')
    );

CREATE POLICY kd_reviewer_update ON public.knowledge_documents
    FOR UPDATE
    USING (
        tenant_id = (
            SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid()
        )
        AND EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_id = auth.uid() AND role IN ('admin', 'super_admin')
        )
    );

-- ============================================================================
-- Search RPC — semantic search with permission filtering
-- ============================================================================
CREATE OR REPLACE FUNCTION public.search_knowledge(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    filter_tags TEXT[] DEFAULT '{}'
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    source_url TEXT,
    tags TEXT[],
    score FLOAT
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
    SELECT
        id,
        title,
        content,
        source_url,
        tags,
        1 - (embedding <=> query_embedding) AS score
    FROM public.knowledge_documents
    WHERE status = 'approved'
      AND deleted_at IS NULL
      AND tenant_id = (
          SELECT tenant_id FROM public.user_profiles WHERE user_id = auth.uid()
      )
      AND (
          filter_tags = '{}'::TEXT[]
          OR tags && filter_tags
      )
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- ============================================================================
-- Audit trigger: log every status transition
-- ============================================================================
CREATE OR REPLACE FUNCTION public.knowledge_status_change_audit()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO public.audit_logs
            (action, actor_id, tenant_id, resource_type, resource_id, metadata)
        VALUES (
            'knowledge_doc.status_change',
            auth.uid(),
            NEW.tenant_id,
            'knowledge_doc',
            NEW.id::TEXT,
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'reviewed_by', NEW.reviewed_by
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_kd_status_audit ON public.knowledge_documents;
CREATE TRIGGER trg_kd_status_audit AFTER UPDATE ON public.knowledge_documents
    FOR EACH ROW WHEN (NEW.status IS DISTINCT FROM OLD.status)
    EXECUTE FUNCTION public.knowledge_status_change_audit();
