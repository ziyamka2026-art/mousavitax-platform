"""
Unit tests for the Oath Runtime Guards (TAXLAW-GROK Constitution v2.0).
"""

import pytest

from packages.oath.runtime_guards import (
    AnalysisResult,
    AnalysisStatus,
    Citation,
    OathViolation,
    PIIRedactor,
    enforce_oath,
    law_over_circular,
    require_ambiguity_flag,
    require_archival_record,
    require_citations,
    require_human_review,
)


def _valid_result(**overrides) -> AnalysisResult:
    """Returns a result that should pass all guards."""
    defaults = {
        "content": "تحلیل: بر اساس ماده ۲۵۱ مکرر ق.م.م، نفع مؤدی قابل استنباط است.",
        "citations": [
            Citation(
                source_type="law",
                source_id="qmm-251-m",
                title="ماده ۲۵۱ مکرر قانون مالیات‌های مستقیم",
            ),
        ],
        "case_id": "case-001",
        "status": AnalysisStatus.PENDING_HUMAN_REVIEW,
        "has_ambiguity": True,
        "reasoning_chain": [
            {"rule": "تفسیر مضیق", "applied": True, "favor": "taxpayer"},
        ],
    }
    defaults.update(overrides)
    return AnalysisResult(**defaults)


# ---------------------------------------------------------------------------
# Clause 1: PII Redaction
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_pii_redactor_redacts_national_id():
    text = "کد ملی مؤدی: 1234567890 است."
    redacted = PIIRedactor.redact(text)
    assert "1234567890" not in redacted
    assert "[NATIONAL_ID]" in redacted


@pytest.mark.unit
def test_pii_redactor_redacts_phone():
    text = "تماس: 09123456789"
    redacted = PIIRedactor.redact(text)
    assert "09123456789" not in redacted
    assert "[PHONE]" in redacted


@pytest.mark.unit
def test_pii_redactor_redacts_email():
    text = "ایمیل: user@example.com"
    redacted = PIIRedactor.redact(text)
    assert "user@example.com" not in redacted
    assert "[EMAIL]" in redacted


@pytest.mark.unit
def test_pii_redactor_redacts_bank_account():
    text = "حساب: 1234567890123456"
    redacted = PIIRedactor.redact(text)
    assert "1234567890123456" not in redacted
    assert "[BANK_ACCOUNT]" in redacted


@pytest.mark.unit
def test_pii_redactor_preserves_non_pii():
    text = "ماده ۲۵۱ مکرر ق.م.م درباره اعتراض مالیاتی است."
    redacted = PIIRedactor.redact(text)
    assert redacted == text  # no PII, no change


@pytest.mark.unit
def test_pii_redactor_handles_dict_recursively():
    data = {
        "user": "ali",
        "national_id": "1234567890",
        "nested": {"phone": "09123456789", "extra": "data"},
    }
    redacted = PIIRedactor.redact_dict(data)
    assert redacted["user"] == "ali"
    assert redacted["national_id"] == "[NATIONAL_ID]"
    assert redacted["nested"]["phone"] == "[PHONE]"
    assert redacted["nested"]["extra"] == "data"


# ---------------------------------------------------------------------------
# Clause 2: Require citations
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_require_citations_passes_with_citations():
    result = _valid_result()
    require_citations(result)  # should not raise


@pytest.mark.unit
def test_require_citations_fails_without_citations():
    result = _valid_result(citations=[])
    with pytest.raises(OathViolation, match="بدون مستند سخن نگویم"):
        require_citations(result)


# ---------------------------------------------------------------------------
# Clause 3: Law over circular
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_law_over_circular_passes_when_law_present():
    result = _valid_result(
        citations=[
            Citation(source_type="law", source_id="qmm-251-m", title="ماده ۲۵۱ مکرر"),
            Citation(source_type="circular", source_id="cir-2024-001", title="بخشنامه"),
        ]
    )
    law_over_circular(result)  # should not raise


@pytest.mark.unit
def test_law_over_circular_fails_when_only_circular():
    result = _valid_result(
        citations=[
            Citation(source_type="circular", source_id="cir-2024-001", title="بخشنامه"),
        ]
    )
    with pytest.raises(OathViolation, match="قانون را بر بخشنامه مقدم"):
        law_over_circular(result)


@pytest.mark.unit
def test_law_over_circular_passes_when_only_law():
    result = _valid_result(
        citations=[
            Citation(source_type="law", source_id="qmm-251-m", title="ماده ۲۵۱ مکرر"),
        ]
    )
    law_over_circular(result)  # should not raise


# ---------------------------------------------------------------------------
# Clause 4: Ambiguity favoring taxpayer
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_require_ambiguity_flag_passes_when_favor_taxpayer_in_content():
    result = _valid_result(
        has_ambiguity=True,
        content="در این مورد ابهام وجود دارد. تفسیر به نفع مؤدی می‌باشد.",
    )
    require_ambiguity_flag(result)  # should not raise


@pytest.mark.unit
def test_require_ambiguity_flag_passes_when_in_reasoning_chain():
    result = _valid_result(
        has_ambiguity=True,
        content="تحلیل انجام شد.",
        reasoning_chain=[{"rule": "تفسیر مضیق به نفع مؤدی", "applied": True}],
    )
    require_ambiguity_flag(result)  # should not raise


@pytest.mark.unit
def test_require_ambiguity_flag_fails_when_no_taxpayer_mention():
    result = _valid_result(
        has_ambiguity=True,
        content="تحلیل انجام شد ولی ابهام وجود دارد.",
        reasoning_chain=[{"rule": "L心想事成", "applied": False}],
    )
    with pytest.raises(OathViolation, match="در ابهام به نفع مؤدی"):
        require_ambiguity_flag(result)


@pytest.mark.unit
def test_require_ambiguity_flag_skips_when_no_ambiguity():
    result = _valid_result(has_ambiguity=False, content="تحلیل قطعی.")
    require_ambiguity_flag(result)  # should not raise


# ---------------------------------------------------------------------------
# Clause 5: Archival record
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_require_archival_record_passes_with_case_id():
    result = _valid_result(case_id="case-001")
    require_archival_record(result)


@pytest.mark.unit
def test_require_archival_record_fails_without_case_id():
    result = _valid_result(case_id=None)
    with pytest.raises(OathViolation, match="هر تحلیل خود را در مخزن ثبت"):
        require_archival_record(result)


# ---------------------------------------------------------------------------
# Clause 6: Human review required
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_require_human_review_passes_when_pending():
    result = _valid_result(status=AnalysisStatus.PENDING_HUMAN_REVIEW)
    require_human_review(result)


@pytest.mark.unit
def test_require_human_review_passes_when_draft():
    result = _valid_result(status=AnalysisStatus.DRAFT)
    require_human_review(result)


@pytest.mark.unit
def test_require_human_review_fails_when_final_set_by_ai():
    result = _valid_result(status=AnalysisStatus.FINAL)
    with pytest.raises(OathViolation, match="تصمیم نهایی را به اختیار انسان"):
        require_human_review(result)


# ---------------------------------------------------------------------------
# Combined enforce_oath
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_enforce_oath_passes_valid_result():
    result = _valid_result()
    enforce_oath(result)  # should not raise


@pytest.mark.unit
def test_enforce_oath_blocks_when_circular_only():
    result = _valid_result(
        citations=[
            Citation(source_type="circular", source_id="c1", title="بخشنامه"),
        ]
    )
    with pytest.raises(OathViolation, match="law_over_circular"):
        enforce_oath(result)


@pytest.mark.unit
def test_enforce_oath_blocks_when_no_citations():
    result = _valid_result(citations=[])
    with pytest.raises(OathViolation, match="require_citations"):
        enforce_oath(result)


@pytest.mark.unit
def test_enforce_oath_blocks_when_ai_sets_final():
    result = _valid_result(status=AnalysisStatus.FINAL)
    with pytest.raises(OathViolation, match="require_human_review"):
        enforce_oath(result)


@pytest.mark.unit
def test_enforce_oath_blocks_when_no_case_id():
    result = _valid_result(case_id=None)
    with pytest.raises(OathViolation, match="require_archival_record"):
        enforce_oath(result)
