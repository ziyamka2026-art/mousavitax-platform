"""
Unit tests for the Fiqh Validator (TAXLAW-GROK Constitution Principle 3).
"""

import pytest

from packages.fiqh_validator.validator import (
    AnalysisContext,
    Citation,
    FiqhRule,
    FiqhValidationError,
    enforce_fiqh,
    validate_analysis,
    validate_asalat_al_barah,
    validate_asalat_al_sihhah,
    validate_istishab,
    validate_ladarar,
    validate_man_atf_bimassabaq,
    validate_nafy_eusr_wa_haraj,
    validate_tafsir_maddiq,
)


def _ctx(**overrides) -> AnalysisContext:
    """Returns a baseline context that should pass all rules."""
    defaults = {
        "content": "تحلیل حقوقی انجام شد. معافیت قبلی به‌درستی حفظ شده.",
        "citations": [
            Citation(
                source_type="law",
                source_id="qmm-251-m",
                title="ماده ۲۵۱ مکرر ق.م.م",
                effective_date="2008-01-01",
            ),
        ],
        "burden_of_proof": "administration",
        "has_prior_exemption": False,
        "has_ambiguity": False,
        "event_date": "2024-01-01",
        "proposed_tax_liability": None,
        "prior_tax_liability": None,
        "books_verified": False,
        "hardship_claim": False,
    }
    defaults.update(overrides)
    return AnalysisContext(**defaults)


# ---------------------------------------------------------------------------
# Rule 1: قاعده لاضرر (No harm)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_ladarar_passes_when_no_liability_claim():
    ctx = _ctx()
    result = validate_ladarar(ctx)
    assert result.passed
    assert result.rule == FiqhRule.LADARAR


@pytest.mark.unit
def test_ladarar_fails_when_liability_without_citation():
    ctx = _ctx(
        proposed_tax_liability=1_000_000,
        citations=[],
    )
    result = validate_ladarar(ctx)
    assert not result.passed
    assert "مضاعف" in result.reasoning or "بدون استناد" in result.reasoning


@pytest.mark.unit
def test_ladarar_fails_when_liability_spikes_more_than_2x():
    ctx = _ctx(
        proposed_tax_liability=10_000_000,
        prior_tax_liability=3_000_000,
        citations=[Citation(source_type="law", source_id="x", title="x")],
    )
    result = validate_ladarar(ctx)
    assert not result.passed
    # Check that the violation is mentioned (in reasoning or evidence)
    full_text = result.reasoning + " ".join(result.evidence)
    assert "نسبت مطالبه" in full_text or "نسبت" in full_text


@pytest.mark.unit
def test_ladarar_passes_when_liability_increase_is_reasonable():
    ctx = _ctx(
        proposed_tax_liability=4_000_000,
        prior_tax_liability=3_000_000,
        citations=[Citation(source_type="law", source_id="x", title="x")],
    )
    result = validate_ladarar(ctx)
    assert result.passed


# ---------------------------------------------------------------------------
# Rule 2: أصالةالبرائه (Burden of proof on administration)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_asalat_al_barah_passes_when_no_concealment_claim():
    ctx = _ctx(content="تحلیل ساده.", burden_of_proof=None)
    result = validate_asalat_al_barah(ctx)
    assert result.passed


@pytest.mark.unit
def test_asalat_al_barah_passes_when_burden_correctly_assigned():
    ctx = _ctx(
        content="مؤدی به کتمان درآمد متهم شده.",
        burden_of_proof="administration",
    )
    result = validate_asalat_al_barah(ctx)
    assert result.passed


@pytest.mark.unit
def test_asalat_al_barah_fails_when_burden_on_taxpayer():
    ctx = _ctx(
        content="مؤدی به کتمان درآمد متهم شده ولی بار اثبات روی اوست.",
        burden_of_proof="taxpayer",
    )
    result = validate_asalat_al_barah(ctx)
    assert not result.passed
    assert "اصل ۳۷" in result.reasoning


# ---------------------------------------------------------------------------
# Rule 3: استصحاب (Continuity)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_istishab_passes_when_no_prior_exemption():
    ctx = _ctx(has_prior_exemption=False, proposed_tax_liability=1_000_000)
    result = validate_istishab(ctx)
    assert result.passed


@pytest.mark.unit
def test_istishab_fails_when_prior_exemption_overridden_silently():
    ctx = _ctx(
        has_prior_exemption=True,
        proposed_tax_liability=5_000_000,
        content="تحلیل انجام شد و مطالبه‌ی جدیدی مطرح شده است.",
    )
    result = validate_istishab(ctx)
    assert not result.passed
    assert "اقامه" in result.reasoning


@pytest.mark.unit
def test_istishab_passes_when_explicit_removal_with_reason():
    ctx = _ctx(
        has_prior_exemption=True,
        proposed_tax_liability=5_000_000,
        content="با اقامه دلیل، رفع معافیت انجام شد.",
    )
    result = validate_istishab(ctx)
    assert result.passed


# ---------------------------------------------------------------------------
# Rule 4: أصالةالصحه (Presumption of validity)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_asalat_al_sihhah_passes_when_books_not_mentioned():
    ctx = _ctx(content="تحلیل درباره ارزش افزوده است.", books_verified=False)
    result = validate_asalat_al_sihhah(ctx)
    assert result.passed


@pytest.mark.unit
def test_asalat_al_sihhah_fails_when_books_rejected_without_evidence():
    ctx = _ctx(
        content="دفاتر مؤدی فاقد اعتبار است و نقص دفاتر مشهود است.",
        books_verified=False,
        citations=[],
    )
    result = validate_asalat_al_sihhah(ctx)
    assert not result.passed
    # Check the references in evidence (since they live in evidence list)
    full_text = result.reasoning + " " + " ".join(result.evidence)
    assert "۲۲۹" in full_text or "۲۳۷" in full_text


@pytest.mark.unit
def test_asalat_al_sihhah_passes_when_books_rejected_with_evidence():
    ctx = _ctx(
        content="دفاتر مؤدی فاقد اعتبار است.",
        books_verified=False,
        citations=[Citation(source_type="judgment", source_id="r1", title="رأی هیئت")],
    )
    result = validate_asalat_al_sihhah(ctx)
    assert result.passed


# ---------------------------------------------------------------------------
# Rule 5: نفی عسر و حرج (No undue hardship)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_nafy_eusr_passes_when_no_hardship_claim():
    ctx = _ctx(hardship_claim=False)
    result = validate_nafy_eusr_wa_haraj(ctx)
    assert result.passed


@pytest.mark.unit
def test_nafy_eusr_fails_when_hardship_claim_ignored():
    ctx = _ctx(
        hardship_claim=True,
        content="تحلیل انجام شد بدون توجه به ادعا.",
    )
    result = validate_nafy_eusr_wa_haraj(ctx)
    assert not result.passed


@pytest.mark.unit
def test_nafy_eusr_passes_when_hardship_acknowledged():
    ctx = _ctx(
        hardship_claim=True,
        content="ادعای عسر و حرج مؤدی بررسی شد.",
    )
    result = validate_nafy_eusr_wa_haraj(ctx)
    assert result.passed


# ---------------------------------------------------------------------------
# Rule 6: تفسیر مضیق (Narrow interpretation in ambiguity)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_tafsir_maddiq_passes_when_no_ambiguity():
    ctx = _ctx(has_ambiguity=False)
    result = validate_tafsir_maddiq(ctx)
    assert result.passed


@pytest.mark.unit
def test_tafsir_maddiq_fails_when_ambiguity_without_pro_taxpayer():
    ctx = _ctx(
        has_ambiguity=True,
        content="قانون مبهم است و تحلیل انجام شد.",
    )
    result = validate_tafsir_maddiq(ctx)
    assert not result.passed


@pytest.mark.unit
def test_tafsir_maddiq_passes_when_pro_taxpayer_mentioned():
    ctx = _ctx(
        has_ambiguity=True,
        content="در ابهام، تفسیر به نفع مؤدی اعمال شد.",
    )
    result = validate_tafsir_maddiq(ctx)
    assert result.passed


@pytest.mark.unit
def test_tafsir_maddiq_passes_with_short_marker():
    ctx = _ctx(
        has_ambiguity=True,
        content="بر اساس تفسیر مضیق، نتیجه‌گیری شد.",
    )
    result = validate_tafsir_maddiq(ctx)
    assert result.passed


# ---------------------------------------------------------------------------
# Rule 7: منع عطفبماسببق (No retroactive application)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_man_atf_passes_when_no_event_date():
    ctx = _ctx(event_date=None)
    result = validate_man_atf_bimassabaq(ctx)
    assert result.passed


@pytest.mark.unit
def test_man_atf_passes_when_sources_predate_event():
    ctx = _ctx(
        event_date="2024-06-01",
        citations=[
            Citation(source_type="law", source_id="x", title="x", effective_date="2008-01-01"),
        ],
    )
    result = validate_man_atf_bimassabaq(ctx)
    assert result.passed


@pytest.mark.unit
def test_man_atf_fails_when_source_postdates_event():
    ctx = _ctx(
        event_date="2024-01-01",
        citations=[
            Citation(
                source_type="law",
                source_id="new-law",
                title="قانون جدید",
                effective_date="2024-12-01",
            ),
        ],
    )
    result = validate_man_atf_bimassabaq(ctx)
    assert not result.passed
    # The reasoning uses ZWNJ version عطف‌بماسببق — check both forms
    full_text = result.reasoning + " " + " ".join(result.evidence)
    assert "عطف" in full_text


@pytest.mark.unit
def test_man_atf_passes_when_source_date_unknown():
    ctx = _ctx(
        event_date="2024-01-01",
        citations=[
            Citation(source_type="law", source_id="x", title="x", effective_date=None),
        ],
    )
    result = validate_man_atf_bimassabaq(ctx)
    assert result.passed


# ---------------------------------------------------------------------------
# Combined validator
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_validate_analysis_returns_full_report_with_seven_rules():
    ctx = _ctx()
    report = validate_analysis(ctx)
    assert len(report.results) == 7
    assert report.overall_passed
    rule_names = {r.rule for r in report.results}
    assert FiqhRule.LADARAR in rule_names
    assert FiqhRule.MAN_ATF_BIMASABBAQ in rule_names


@pytest.mark.unit
def test_validate_analysis_overall_fails_when_one_rule_fails():
    ctx = _ctx(
        has_ambiguity=True,
        content="قانون مبهم است.",  # no pro-taxpayer marker
    )
    report = validate_analysis(ctx)
    assert not report.overall_passed
    assert len(report.failed_rules()) == 1
    assert report.failed_rules()[0].rule == FiqhRule.TAFSIR_MADDIQ


@pytest.mark.unit
def test_enforce_fiqh_passes_when_valid():
    ctx = _ctx()
    report = enforce_fiqh(ctx)
    assert report.overall_passed


@pytest.mark.unit
def test_enforce_fiqh_raises_on_violation():
    ctx = _ctx(
        has_ambiguity=True,
        content="قانون مبهم است و تحلیل انجام شد.",
    )
    with pytest.raises(FiqhValidationError, match="تفسیر مضیق"):
        enforce_fiqh(ctx)
