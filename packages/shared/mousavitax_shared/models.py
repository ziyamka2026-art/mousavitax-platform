"""Shared data models for MousaviTax Platform (Pydantic).

Migrated from MKA-Core and extended per ADR-002 (Knowledge Data Model):
  - Temporal Validity (effective_from / effective_to)
  - official_ref for Iranian tax sources
  - SourceDocument entity
  - Tax-oriented SourceType values
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Origin or document category."""

    # Generic / ingestion
    GOOGLE_DRIVE = "google_drive"
    UPLOAD = "upload"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    HTML = "html"
    CSV = "csv"
    OCR = "ocr"
    MANUAL = "manual"

    # Iranian tax official categories (ADR-002)
    LAW = "law"
    CIRCULAR = "circular"
    RULING = "ruling"
    DIRECTIVE = "directive"
    REGULATION = "regulation"
    INSTRUCTION = "instruction"


class SourceDocument(BaseModel):
    """Canonical source document (law, circular, ruling, ...)."""

    source_id: str
    source_type: SourceType
    title: str
    official_ref: str | None = None  # e.g. section number, circular no.
    effective_from: date | None = None
    effective_to: date | None = None
    supersedes: str | None = None  # source_id of previous version
    superseded_by: str | None = None
    url: str | None = None
    storage_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Provenance for a retrieved chunk — mandatory for tax claims."""

    source_id: str
    source_type: SourceType
    title: str
    chunk_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    page: int | None = None
    section: str | None = None
    url: str | None = None
    official_ref: str | None = None
    effective_from: date | None = None


class RetrievedChunk(BaseModel):
    content: str
    citation: Citation
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    user_id: str | None = None
    session_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] | None = None
    # Optional as-of date for temporal filtering (ADR-002)
    as_of: date | None = None


class RAGResponse(BaseModel):
    answer: str
    citations: list[Citation]
    model: str
    latency_ms: int | None = None
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- Knowledge / Vector Query models ---


class DocumentChunk(BaseModel):
    """A chunk ready for embedding and storage."""

    chunk_id: str
    source_id: str
    source_type: SourceType
    title: str
    text: str
    page: int | None = None
    section: str | None = None
    url: str | None = None
    official_ref: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexRequest(BaseModel):
    chunks: list[DocumentChunk]
    collection: str = "iran_tax_official"


class IndexResponse(BaseModel):
    indexed: int
    collection: str
    errors: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] | None = None
    collection: str = "iran_tax_official"
    as_of: date | None = None  # temporal validity filter


class QueryHit(BaseModel):
    chunk_id: str
    text: str
    score: float
    citation: Citation


class QueryResponse(BaseModel):
    hits: list[QueryHit]
    query: str
    latency_ms: int | None = None
