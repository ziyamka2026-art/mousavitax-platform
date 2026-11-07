"""APCS command models (Phase 1–3)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceLevel(str, Enum):
    E0 = "E0"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"


class OutputFormat(str, Enum):
    TEXT = "TEXT"
    TABLE = "TABLE"
    JSON = "JSON"
    MARKDOWN = "MARKDOWN"
    REPORT = "REPORT"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    CHECKLIST = "CHECKLIST"
    API_RESPONSE = "API_RESPONSE"
    STRUCTURED_TAX_REPORT = "STRUCTURED_TAX_REPORT"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class APCSCommand(BaseModel):
    role: str | None = None
    persona: str | None = None
    task: str | None = None
    objective: str | None = None
    success: str | None = None
    context: str | None = None
    input_text: str | None = Field(default=None, alias="input")
    evidence: str | None = None
    evidence_level: EvidenceLevel | None = None
    rules: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    guardrail: str | None = None
    method: str | None = None
    analyze: str | None = None
    perspectives: list[str] = Field(default_factory=list)
    compare: str | None = None
    risk: str | None = None
    pitfalls: str | None = None
    assumptions: str | None = None
    metrics: list[str] = Field(default_factory=list)
    verify: bool = False
    self_check: bool = False
    quality_gate: bool = False
    decision: str | None = None
    decision_rule: str | None = None
    format: OutputFormat = OutputFormat.MARKDOWN
    audience: str | None = None
    tone: str | None = None
    exec_summary: bool = False
    domain_id: str | None = None
    raw_blocks: dict[str, str] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ValidationResult(BaseModel):
    ok: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class QualityGateResult(BaseModel):
    passed: bool = True
    status: str | None = None  # INSUFFICIENT_DATA | CONFLICTING_EVIDENCE | ...
    reasons: list[str] = Field(default_factory=list)
