-- Source: docs/agent-workflow/API-POSTGRES-TEST-GUIDE.md
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE tax_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_case_id text NOT NULL UNIQUE,
  owner_id text NOT NULL,
  taxpayer_ref text NOT NULL,
  status text NOT NULL DEFAULT 'OPEN',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE legal_workflows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES tax_cases(id),
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

CREATE TABLE workflow_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES legal_workflows(id),
  event_type text NOT NULL,
  actor_id text,
  agent_id text NOT NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES legal_workflows(id),
  artifact_type text NOT NULL,
  storage_uri text,
  content_hash text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_gates (
  workflow_id uuid NOT NULL REFERENCES legal_workflows(id),
  gate_type text NOT NULL,
  state text NOT NULL DEFAULT 'OPEN',
  resolved_by text,
  resolution_note text,
  resolved_at timestamptz,
  PRIMARY KEY (workflow_id, gate_type)
);

CREATE INDEX workflow_events_workflow_time_idx
  ON workflow_events(workflow_id, created_at);
CREATE INDEX workflow_artifacts_workflow_type_idx
  ON workflow_artifacts(workflow_id, artifact_type);
