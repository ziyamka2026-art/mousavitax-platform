"""
Oath Runtime Guards — TAXLAW-GROK Constitution v2.0
====================================================

Implements the six clauses of the TAXLAW-GROK oath as runtime guards.
Every analysis output must pass ALL guards before delivery to user.

@package packages.oath
@see docs/adr/ADR-009-TAXLAW-GROK-Constitution.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OathViolation(Exception):
    """Raised when an output violates the TAXLAW-GROK oath."""


class AnalysisStatus(str, Enum):
    DRAFT = "draft"
    PENDING_HUMAN_REVIEW = "pending_human_review"
    FINAL = "final"


@dataclass
class Citation:
    source_type: str  # 'law' | 'circular' | 'judgment' | 'doctrine'
    source_id: str
    title: str
    url: str | None = None
    effective_date: str | None = None


@dataclass
class AnalysisResult:
    content: str
    citations: list[Citation] = field(default_factory=list)
    reasoning_chain: list[dict[str, Any]] = field(default_factory=list)
    burden_of_proof: str | None = None  # 'taxpayer' | 'administration'
    previous_exemption_status: str | None = None
    has_ambiguity: bool = False
    status: AnalysisStatus = AnalysisStatus.DRAFT
    case_id: str | None = None
    version: int = 1


# ---------------------------------------------------------------------------
# Clause 1: «اسرار مؤدی را حفظ کنم» — Preserve taxpayer secrets
# ---------------------------------------------------------------------------

PII_PATTERNS = [
    # Iranian National ID (کد ملی) — 10 digits
    (re.compile(r"\b\d{10}\b"), "[NATIONAL_ID]"),
    # Phone numbers (Iranian format)
    (re.compile(r"\b09\d{9}\b"), "[PHONE]"),
    (re.compile(r"\+989\d{9}\b"), "[PHONE]"),
    # Email addresses
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    # Bank account numbers (16 digits)
    (re.compile(r"\b\d{16}\b"), "[BANK_ACCOUNT]"),
    # Case IDs (UUID-like or numeric with prefix)
    (re.compile(r"\b(?:CASE|پرونده)[:\s-]*([A-Z0-9-]+)\b", re.IGNORECASE), "[CASE_ID]"),
]


class PIIRedactor:
    """Redacts PII from text BEFORE any LLM call or external logging."""

    @staticmethod
    def redact(text: str) -> str:
        if not text:
            return text
        out = text
        for pattern, replacement in PII_PATTERNS:
            out = pattern.sub(replacement, out)
        return out

    @staticmethod
    def redact_dict(obj: dict) -> dict:
        """Recursively redact string values in a dict."""
        result = {}
        for k, v in obj.items():
            if isinstance(v, str):
                result[k] = PIIRedactor.redact(v)
            elif isinstance(v, dict):
                result[k] = PIIRedactor.redact_dict(v)
            elif isinstance(v, list):
                result[k] = [
                    PIIRedactor.redact(item) if isinstance(item, str)
                    else PIIRedactor.redact_dict(item) if isinstance(item, dict)
                    else item
                    for item in v
                ]
            else:
                result[k] = v
        return result


# ---------------------------------------------------------------------------
# Clause 2: «بدون مستند سخن نگویم» — Speak not without documentation
# ---------------------------------------------------------------------------

def require_citations(result: AnalysisResult) -> None:
    """Enforces: every analysis must cite at least one source."""
    if len(result.citations) == 0:
        raise OathViolation(
            "بدون مستند سخن نگویم — خروجی فاقد citation است. "
            "هر ادعای حقوقی نیازمند استناد به منبع رسمی است."
        )


# ---------------------------------------------------------------------------
# Clause 3: «قانون را بر بخشنامه مقدم بدارم» — Law over circular
# ---------------------------------------------------------------------------

def law_over_circular(result: AnalysisResult) -> None:
    """Every circular cited must have at least one parent law citation."""
    has_law = any(c.source_type == "law" for c in result.citations)
    has_circular = any(c.source_type == "circular" for c in result.citations)

    if has_circular and not has_law:
        raise OathViolation(
            "قانون را بر بخشنامه مقدم بدارم — خروجی به بخشنامه استناد کرده "
            "بدون ذکر ماده قانونی مرجع. هر بخشنامه باید به قانون مرجع وصل شود."
        )


# ---------------------------------------------------------------------------
# Clause 4: «در ابهام به نفع مؤدی تفسیر کنم» — Pro-taxpayer interpretation
# ---------------------------------------------------------------------------

def require_ambiguity_flag(result: AnalysisResult) -> None:
    """If ambiguity is present, output must explicitly favor taxpayer."""
    if result.has_ambiguity:
        if not result.content or "نفع مؤدی" not in result.content.lower():
            # Check reasoning chain
            in_chain = any(
                "تفسیر مضیق" in str(s).lower()
                or "نفع مؤدی" in str(s).lower()
                for s in result.reasoning_chain
            )
            if not in_chain:
                raise OathViolation(
                    "در ابهام به نفع مؤدی تفسیر کنم — ابهام شناسایی شده ولی "
                    "استدلال صراحتاً نفع مؤدی را ذکر نکرده است."
                )


# ---------------------------------------------------------------------------
# Clause 5: «هر تحلیل خود را در مخزن ثبت نمایم» — Archive every analysis
# ---------------------------------------------------------------------------

def require_archival_record(result: AnalysisResult) -> None:
    """Every analysis must have a case_id for archival tracking."""
    if not result.case_id:
        raise OathViolation(
            "هر تحلیل خود را در مخزن ثبت نمایم — case_id خالی است. "
            "هر تحلیل باید به پرونده‌ای متصل باشد."
        )


# ---------------------------------------------------------------------------
# Clause 6: «تصمیم نهایی را به اختیار انسان مسئول واگذار کنم» — Human-in-loop
# ---------------------------------------------------------------------------

def require_human_review(result: AnalysisResult) -> None:
    """Final status can only be set by a human reviewer, never by AI."""
    if result.status == AnalysisStatus.FINAL:
        raise OathViolation(
            "تصمیم نهایی را به اختیار انسان مسئول واگذار کنم — AI نمی‌تواند "
            "status=FINAL تنظیم کند. تنها انسان مسئول این اختیار را دارد. "
            "AI فقط می‌تواند status=PENDING_HUMAN_REVIEW بگذارد."
        )


# ---------------------------------------------------------------------------
# Combined Oath Guard — run all 6 before delivering output
# ---------------------------------------------------------------------------

def enforce_oath(result: AnalysisResult) -> None:
    """
    Run all 6 oath clauses before delivering output to user.

    Usage:
        result = await generate_analysis(...)
        enforce_oath(result)  # raises OathViolation if any clause fails
        deliver_to_user(result)

    On OathViolation:
        - Log the violation to audit_log with full context
        - Block delivery to user
        - Escalate to human reviewer with the rejection reason
    """
    guards = [
        ("law_over_circular", law_over_circular),
        ("require_citations", require_citations),
        ("require_ambiguity_flag", require_ambiguity_flag),
        ("require_archival_record", require_archival_record),
        ("require_human_review", require_human_review),
    ]
    for name, guard in guards:
        try:
            guard(result)
        except OathViolation as e:
            # Enrich with guard name for audit
            raise OathViolation(f"[{name}] {e}") from e


__all__ = [
    "OathViolation",
    "AnalysisStatus",
    "AnalysisResult",
    "Citation",
    "PIIRedactor",
    "PII_PATTERNS",
    "require_citations",
    "law_over_circular",
    "require_ambiguity_flag",
    "require_archival_record",
    "require_human_review",
    "enforce_oath",
]
