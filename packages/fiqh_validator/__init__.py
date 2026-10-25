"""Fiqh Validator package — Principle 3 of TAXLAW-GROK Constitution."""

from .validator import (
    AnalysisContext,
    Citation,
    FiqhRule,
    FiqhValidationError,
    RuleResult,
    ValidationReport,
    enforce_fiqh,
    validate_analysis,
    VALIDATORS,
)

__all__ = [
    "AnalysisContext",
    "Citation",
    "FiqhRule",
    "FiqhValidationError",
    "RuleResult",
    "ValidationReport",
    "VALIDATORS",
    "enforce_fiqh",
    "validate_analysis",
]
