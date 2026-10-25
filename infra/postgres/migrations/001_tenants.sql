-- =============================================================================
-- MousaviTax — 001: Tenants (multi-tenant foundation)
-- =============================================================================
-- Each tenant represents an organisation (a single advisor firm, a corporate
-- tax department, etc.). All user-owned tables get `tenant_id` and RLS.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'free'
                CHECK (plan IN ('free', 'ai_premium', 'ai_expert', 'enterprise')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON public.tenants (slug);

-- ============================================================================
-- Add tenant_id to users (Supabase auth.users extension via app metadata)
-- ============================================================================
-- NOTE: We do NOT modify auth.users directly. Instead, create a profile table
-- that joins one-to-one with auth.users and adds app-specific columns.

CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id         UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE RESTRICT,
    role            TEXT NOT NULL DEFAULT 'taxpayer'
                    CHECK (role IN ('taxpayer', 'advisor', 'auditor', 'admin', 'super_admin')),
    display_name    TEXT,
    email           TEXT,
    phone           TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_tenant ON public.user_profiles (tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_role   ON public.user_profiles (role);

-- ============================================================================
-- Audit trigger: keep updated_at fresh on every UPDATE
-- ============================================================================
CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_tenants_touch ON public.tenants;
CREATE TRIGGER trg_tenants_touch BEFORE UPDATE ON public.tenants
    FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

DROP TRIGGER IF EXISTS trg_user_profiles_touch ON public.user_profiles;
CREATE TRIGGER trg_user_profiles_touch BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
