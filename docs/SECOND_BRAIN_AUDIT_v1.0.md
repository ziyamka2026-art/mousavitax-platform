# SECOND-BRAIN-AUDIT v1.0

Private owner-only memory for MKA/TAXLAW-GROK.

## Trust boundary
- Google Drive / official source = source of record.
- Second Brain = private index, summary, relation and experience layer.
- TAXLAW-GROK Legal Validity Gate = authority and temporal validity control.
- Inference and experience are never promoted to legal authority automatically.

## Google Drive logical folders
MKA PRIVATE/
  SECOND-BRAIN/
    01_SOURCE_DOCUMENTS/
    02_EXTRACTED_IMPORTANT/
    03_CONCEPT_SUMMARIES/
    04_RELATIONS/
    05_INFERENCES/
    06_EXPERIENCES/
    07_AUDIT/
    08_SNAPSHOTS/

## Indexing pipeline
Drive -> text/OCR -> metadata extraction -> important passage extraction -> conceptual summary -> relation detection -> validity metadata -> hash/version check -> Second Brain -> audit event.

## Memory types
document, experience, inference, observation, hypothesis.

## Relation types
related_to, amends, supersedes, interprets, interpreted_by, cites, used_in, derived_from, contradicts, supports, same_subject.

## API
GET /v1/memory/health
POST /v1/memory/search
GET /v1/memory/{memory_id}
POST /v1/memory/feedback

All memory endpoints require X-Memory-Scope: owner or personal-bot in v1. Production must replace this header gate with authenticated identity and authorization.

## MKA integration
The API gateway exposes the private router. The store remains outside public Git. RAG may use Second Brain results as prior context, then re-check original sources through the legal validity gate.

## Security
No secrets, Drive tokens, client records, or real memory content belong in Git. Production requires authentication, encryption at rest, backups and a private deployment boundary.
