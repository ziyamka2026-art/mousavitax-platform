-- 000: Legal workflow tables (required by 004_add_tenant_rls.sql). Idempotent.
-- Source: docs/agent-workflow/API-POSTGRES-TEST-GUIDE.md
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.tax_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_case_id text NOT NULL UNIQUE,
  owner_id text NOT NULL,
  taxpayer_ref text NOT NULL,
  status text NOT NULL DEFAULT 'OPEN',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.legal_workflows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES public.tax_cases(id),
  owner_id text NOT NULL,
  status text NOT NULL,
  current_stage text NOT NULL,
  version integer NOT NULL DEFAULT 1,
  data jsonb NOT NULL DEFAULT '{}'::jsonb,
  pending_gates jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (case_id)
);

CREATE TABLE IF NOT EXISTS public.workflow_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES public.legal_workflows(id),
  event_type text NOT NULL,
  actor_id text,
  agent_id text NOT NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.workflow_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES public.legal_workflows(id),
  artifact_type text NOT NULL,
  storage_uri text,
  content_hash text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.workflow_gates (
  workflow_id uuid NOT NULL REFERENCES public.legal_workflows(id),
  gate_type text NOT NULL,
  state text NOT NULL DEFAULT 'OPEN',
  resolved_by text,
  resolution_note text,
  resolved_at timestamptz,
  PRIMARY KEY (workflow_id, gate_type)
);

CREATE INDEX IF NOT EXISTS workflow_events_workflow_time_idx
  ON public.workflow_events(workflow_id, created_at);
CREATE INDEX IF NOT EXISTS workflow_artifacts_workflow_type_idx
  ON public.workflow_artifacts(workflow_id, artifact_type);
