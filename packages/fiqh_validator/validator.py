"""
Fiqh Validator — TAXLAW-GROK Constitution v2.0
================================================

Implements Principle 3 (انطباق استدلال با قواعد فقهی) of the charter.

Validates every AI analysis output against seven canonical fiqh/legal rules:
  1. قاعده لاضرر         — No harm principle
  2. أصالةالبرائه        — Burden of proof on administration
  3. استصحاب              — Continuity of prior status
  4. أصالةالصحه          — Presumption of validity
  5. نفی عسر و حرج         — No undue hardship
  6. تفسیر مضیق           — Narrow interpretation in ambiguity
  7. منع عطفبماسببق        — No retroactive application

Each rule produces a ValidationResult with: pass/fail + reasoning + evidence.
The combined report is consumed by the LegalAnalysisPipeline Stage 2.

@package packages.fiqh_validator
@see docs/adr/ADR-009-TAXLAW-GROK-Constitution.md (Principle 3)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class FiqhRule(str, Enum):
    LADARAR = "لاضرر"                       # No harm
    ASALAT_AL_BARAH = "أصالةالبرائه"          # Burden of proof on admin
    ISTISHAB = "استصحاب"                    # Continuity
    ASALAT_AL_SIHHAH = "أصالةالصحه"          # Presumption of validity
    NAFY_EUSR_WA_HARAJ = "نفی عسر و حرج"     # No undue hardship
    TAFSIR_MADDIQ = "تفسیر مضیق"             # Narrow interpretation
    MAN_ATF_BIMASABBAQ = "منع عطفبماسببق"     # No retroactive


@dataclass
class Citation:
    source_type: str  # 'law' | 'circular' | 'judgment'
    source_id: str
    title: str
    url: str | None = None
    effective_date: str | None = None  # ISO 8601 — when this source became law


@dataclass
class AnalysisContext:
    """Input to the validator — describes the analysis being checked."""
    content: str                           # the analysis text
    citations: list[Citation] = field(default_factory=list)
    burden_of_proof: Literal["taxpayer", "administration"] | None = None
    has_prior_exemption: bool = False
    has_ambiguity: bool = False
    event_date: str | None = None          # ISO 8601 — date of the case event
    proposed_tax_liability: float | None = None
    prior_tax_liability: float | None = None
    books_verified: bool = False           # whether دفاتر were verified
    hardship_claim: bool = False


@dataclass
class RuleResult:
    rule: FiqhRule
    passed: bool
    reasoning: str                         # human-readable explanation
    evidence: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    overall_passed: bool
    results: list[RuleResult] = field(default_factory=list)
    summary: str = ""

    def failed_rules(self) -> list[RuleResult]:
        return [r for r in self.results if not r.passed]


class FiqhValidationError(Exception):
    """Raised when an analysis fails one or more fiqh rules."""


# ---------------------------------------------------------------------------
# Rule 1: قاعده لاضرر (No Harm Principle)
# ---------------------------------------------------------------------------

def validate_ladarar(ctx: AnalysisContext) -> RuleResult:
    """
    No harm principle: a tax demand that is double or unrealistic is invalid.

    Detection heuristics:
      - Proposed liability > 2x prior liability → suspicious
      - Liability present without any citation → suspicious
    """
    rule = FiqhRule.LADARAR
    evidence: list[str] = []

    # Check 1: sudden spike in liability
    if (
        ctx.proposed_tax_liability is not None
        and ctx.prior_tax_liability is not None
        and ctx.prior_tax_liability > 0
    ):
        ratio = ctx.proposed_tax_liability / ctx.prior_tax_liability
        if ratio > 2.0:
            evidence.append(
                f"نسبت مطالبه‌ی جدید به قدیمی: {ratio:.2f}× "
                f"(پیشین: {ctx.prior_tax_liability}, پیشنهادی: {ctx.proposed_tax_liability})"
            )
            return RuleResult(
                rule=rule,
                passed=False,
                reasoning=(
                    "مطالبه‌ی مالیاتی به‌طور قابل‌توجه بالاتر از وضعیت قبلی است "
                    "که می‌تواند موجب ضرر ناروا به مؤدی شود. قاعده لاضرر نقض می‌شود."
                ),
                evidence=evidence,
            )
        evidence.append(f"نسبت مطالبه: {ratio:.2f}× — در محدوده‌ی قابل‌قبول.")

    # Check 2: liability without citation
    if ctx.proposed_tax_liability is not None and ctx.proposed_tax_liability > 0:
        if not ctx.citations:
            return RuleResult(
                rule=rule,
                passed=False,
                reasoning=(
                    "مطالبه‌ی مالیاتی بدون استناد به منبع رسمی مطرح شده. "
                    "این امر می‌تواند موجب ضرر مضاعف به مؤدی شود."
                ),
                evidence=["هیچ citation در تحلیل موجود نیست."],
            )
        evidence.append(f"استناد به {len(ctx.citations)} منبع موجود است.")

    return RuleResult(
        rule=rule,
        passed=True,
        reasoning="هیچ نشانه‌ای از مطالبه‌ی مضاعف یا غیرواقعی نیست.",
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Rule 2: أصالةالبرائه (Burden of Proof on Administration)
# ---------------------------------------------------------------------------

def validate_asalat_al_barah(ctx: AnalysisContext) -> RuleResult:
    """
    Burden of proof of income concealment is on the tax administration.

    Reference: Article 37 of Iranian Constitution.

    Detection:
      - If content mentions "کتمان درآمد" (income concealment), the
        burden_of_proof must be set to 'administration'.
    """
    rule = FiqhRule.ASALAT_AL_BARAH
    keywords = ["کتمان", "پنهان‌کاری درآمد", "عدم تسلیم اظهارنامه"]

    if any(k in ctx.content for k in keywords):
        if ctx.burden_of_proof != "administration":
            return RuleResult(
                rule=rule,
                passed=False,
                reasoning=(
                    "تحلیل به «کتمان درآمد» اشاره کرده ولی بار اثبات را به‌درستی "
                    "بر عهده‌ی اداره‌ی امور مالیاتی نگذاشته است. اصل ۳۷ قانون اساسی "
                    "تصریح می‌کند که بار اثبات جرم بر عهده‌ی اداره است."
                ),
                evidence=[
                    "اصل ۳۷ قانون اساسی",
                    "محتوای تحلیل شامل یکی از کلیدواژه‌های کتمان/پنهان‌کاری است.",
                ],
            )
        return RuleResult(
            rule=rule,
            passed=True,
            reasoning="بار اثبات به‌درستی بر عهده‌ی اداره‌ی امور مالیاتی گذاشته شده.",
            evidence=["burden_of_proof=administration"],
        )

    return RuleResult(
        rule=rule,
        passed=True,
        reasoning="بحث کتمان درآمد مطرح نشده. این قاعده اعمال نمی‌شود.",
    )


# ---------------------------------------------------------------------------
# Rule 3: استصحاب (Continuity of Prior Status)
# ---------------------------------------------------------------------------

def validate_istishab(ctx: AnalysisContext) -> RuleResult:
    """
    Continuity of prior status: prior exemption remains until proven otherwise.

    Detection:
      - If has_prior_exemption is True, the analysis should not propose
        new tax liability without explicitly overcoming the exemption.
    """
    rule = FiqhRule.ISTISHAB

    if not ctx.has_prior_exemption:
        return RuleResult(
            rule=rule,
            passed=True,
            reasoning="معافیت قبلی وجود ندارد. این قاعده اعمال نمی‌شود.",
        )

    if ctx.proposed_tax_liability is not None and ctx.proposed_tax_liability > 0:
        # Need to see if the analysis explicitly addresses the prior exemption
        if "رفع معافیت" not in ctx.content and "اقامه دلیل" not in ctx.content:
            return RuleResult(
                rule=rule,
                passed=False,
                reasoning=(
                    "معافیت قبلی وجود دارد ولی تحلیل بدون اقامه‌ی دلیل یقینی، "
                    "مطالبه‌ی مالیاتی جدیدی مطرح کرده. قاعده استصحاب نقض می‌شود."
                ),
                evidence=[
                    f"has_prior_exemption={ctx.has_prior_exemption}",
                    "محتوای تحلیل شامل «رفع معافیت» یا «اقامه دلیل» نیست.",
                ],
            )

    return RuleResult(
        rule=rule,
        passed=True,
        reasoning="معافیت قبلی به‌درستی حفظ شده یا با دلیل موجه رفع شده.",
        evidence=["has_prior_exemption=True با مواجهه‌ی صریح."],
    )


# ---------------------------------------------------------------------------
# Rule 4: أصالةالصحه (Presumption of Validity)
# ---------------------------------------------------------------------------

def validate_asalat_al_sihhah(ctx: AnalysisContext) -> RuleResult:
    """
    Presumption of validity: taxpayer's books are presumed valid unless
    proven otherwise with concrete evidence.

    Reference: Articles 229 & 237 of ق.م.م (Direct Taxes Act).
    """
    rule = FiqhRule.ASALAT_AL_SIHHAH

    if not ctx.books_verified:
        # No books → rule doesn't apply
        if "دفاتر" not in ctx.content and "کمک‌خرید و فروش" not in ctx.content:
            return RuleResult(
                rule=rule,
                passed=True,
                reasoning="بحث دفاتر مطرح نشده. قاعده اعمال نمی‌شود.",
            )

        if "نقص دفاتر" in ctx.content or "عدم اعتبار دفاتر" in ctx.content:
            # Need citation proving books invalidity
            has_evidence = any(
                c.source_type in ("law", "judgment")
                for c in ctx.citations
            )
            if not has_evidence:
                return RuleResult(
                    rule=rule,
                    passed=False,
                    reasoning=(
                        "تحلیل دفاتر را فاقد اعتبار دانسته ولی بدون استناد به "
                        "حکم قانونی یا رأی مرجع. قاعده أصالةالصحه نقض می‌شود."
                    ),
                    evidence=[
                        "مواد ۲۲۹ و ۲۳۷ ق.م.م — لزوم استناد مثبت برای رد دفاتر.",
                        "هیچ citation قانونی/قضایی موجود نیست.",
                    ],
                )

    return RuleResult(
        rule=rule,
        passed=True,
        reasoning="دفاتر به‌درستی بر صحت فرض شده یا با استناد مثبت رد شده‌اند.",
        evidence=[f"books_verified={ctx.books_verified}"],
    )


# ---------------------------------------------------------------------------
# Rule 5: نفی عسر و حرج (No Undue Hardship)
# ---------------------------------------------------------------------------

def validate_nafy_eusr_wa_haraj(ctx: AnalysisContext) -> RuleResult:
    """
    No undue hardship: AI should not impose obligations beyond capacity.

    Detection:
      - If hardship_claim is True, analysis must acknowledge it.
    """
    rule = FiqhRule.NAFY_EUSR_WA_HARAJ

    if not ctx.hardship_claim:
        return RuleResult(
            rule=rule,
            passed=True,
            reasoning="ادعای عسر و حرج مطرح نشده. قاعده اعمال نمی‌شود.",
        )

    if "عسر و حرج" not in ctx.content and "مالایطاق" not in ctx.content:
        return RuleResult(
            rule=rule,
            passed=False,
            reasoning=(
                "مؤدی ادعای عسر و حرج کرده ولی تحلیل به آن توجهی نکرده. "
                "قاعده نفی عسر و حرج نیازمند رسیدگی صریح است."
            ),
            evidence=[
                "hardship_claim=True",
                "کلیدواژه‌های «عسر و حرج» یا «مالایطاق» در محتوای تحلیل موجود نیست.",
            ],
        )

    return RuleResult(
        rule=rule,
        passed=True,
        reasoning="ادعای عسر و حرج به‌طور صریح در تحلیل مورد توجه قرار گرفته.",
        evidence=["hardship_claim=True با مواجهه‌ی صریح."],
    )


# ---------------------------------------------------------------------------
# Rule 6: تفسیر مضیق (Narrow Interpretation in Ambiguity)
# ---------------------------------------------------------------------------

def validate_tafsir_maddiq(ctx: AnalysisContext) -> RuleResult:
    """
    In ambiguity, tax-imposing laws are interpreted narrowly in favor of taxpayer.

    Detection:
      - If has_ambiguity is True, the analysis must explicitly favor taxpayer.
    """
    rule = FiqhRule.TAFSIR_MADDIQ

    if not ctx.has_ambiguity:
        return RuleResult(
            rule=rule,
            passed=True,
            reasoning="ابهام در متن قانون شناسایی نشده. قاعده اعمال نمی‌شود.",
        )

    pro_taxpayer_markers = [
        "نفع مؤدی", "به نفع مؤدی", "تفسیر مضیق",
        "به نفع-taxpayer", "pro-taxpayer",
    ]
    found = [m for m in pro_taxpayer_markers if m in ctx.content]

    if not found:
        return RuleResult(
            rule=rule,
            passed=False,
            reasoning=(
                "ابهام در قانون شناسایی شده ولی تحلیل صراحتاً تفسیر به نفع مؤدی "
                "را ذکر نکرده. قاعده تفسیر مضیق نقض می‌شود."
            ),
            evidence=[
                "has_ambiguity=True",
                f"هیچ‌یک از نشانه‌های {pro_taxpayer_markers} در محتوا یافت نشد.",
            ],
        )

    return RuleResult(
        rule=rule,
        passed=True,
        reasoning=f"ابهام شناسایی و تفسیر به نفع مؤدی اعمال شده (یافت‌شده: {found}).",
        evidence=found,
    )


# ---------------------------------------------------------------------------
# Rule 7: منع عطفبماسببق (No Retroactive Application)
# ---------------------------------------------------------------------------

def validate_man_atf_bimassabaq(ctx: AnalysisContext) -> RuleResult:
    """
    No retroactive application of law.

    Reference: Article 4 of قانون مدنی (Civil Code).

    Detection:
      - Every citation must have an effective_date that is on or before event_date.
      - If a law became effective AFTER the event, applying it retroactively is forbidden.
    """
    rule = FiqhRule.MAN_ATF_BIMASABBAQ

    if not ctx.event_date:
        return RuleResult(
            rule=rule,
            passed=True,
            reasoning="تاریخ رخداد مشخص نیست. قاعده اعمال نمی‌شود.",
        )

    violations: list[str] = []
    for cite in ctx.citations:
        if not cite.effective_date:
            continue  # unknown — skip
        if cite.effective_date > ctx.event_date:
            violations.append(
                f"منبع «{cite.title}» (effect: {cite.effective_date}) "
                f"پس از رخداد ({ctx.event_date}) وضع شده. اعمال آن عطف‌بماسببق است."
            )

    if violations:
        return RuleResult(
            rule=rule,
            passed=False,
            reasoning=(
                f"{len(violations)} مورد از منابع پس از تاریخ رخداد وضع شده‌اند. "
                "اعمال آن‌ها عطف‌بماسببق بوده و ممنوع است (ماده ۴ قانون مدنی)."
            ),
            evidence=violations,
        )

    return RuleResult(
        rule=rule,
        passed=True,
        reasoning="همه‌ی منابع دارای تاریخ وضع پیش از رخداد هستند.",
        evidence=[
            f"event_date={ctx.event_date}",
            f"{len([c for c in ctx.citations if c.effective_date])} منبع دارای تاریخ."
        ],
    )


# ---------------------------------------------------------------------------
# Combined Validator
# ---------------------------------------------------------------------------

VALIDATORS = [
    (FiqhRule.LADARAR, validate_ladarar),
    (FiqhRule.ASALAT_AL_BARAH, validate_asalat_al_barah),
    (FiqhRule.ISTISHAB, validate_istishab),
    (FiqhRule.ASALAT_AL_SIHHAH, validate_asalat_al_sihhah),
    (FiqhRule.NAFY_EUSR_WA_HARAJ, validate_nafy_eusr_wa_haraj),
    (FiqhRule.TAFSIR_MADDIQ, validate_tafsir_maddiq),
    (FiqhRule.MAN_ATF_BIMASABBAQ, validate_man_atf_bimassabaq),
]


def validate_analysis(ctx: AnalysisContext) -> ValidationReport:
    """
    Run all 7 fiqh rules against an analysis.

    Returns a full report. If any rule fails, overall_passed is False.
    """
    results = [validator(ctx) for _, validator in VALIDATORS]
    overall = all(r.passed for r in results)
    failed = [r for r in results if not r.passed]

    if overall:
        summary = f"✅ همه‌ی ۷ قاعده‌ی فقهی به‌درستی اعمال شده‌اند."
    else:
        failed_names = [r.rule.value for r in failed]
        summary = (
            f"❌ {len(failed)} قاعده‌ی فقهی نقض شده: "
            f"{', '.join(failed_names)}"
        )

    return ValidationReport(
        overall_passed=overall,
        results=results,
        summary=summary,
    )


def enforce_fiqh(ctx: AnalysisContext) -> ValidationReport:
    """
    Validate and raise if any rule fails. Used as a guard in the pipeline.
    """
    report = validate_analysis(ctx)
    if not report.overall_passed:
        failed = report.failed_rules()
        raise FiqhValidationError(
            f"fiqh validation failed — {len(failed)} rule(s) violated: "
            + "; ".join(f"{r.rule.value}: {r.reasoning}" for r in failed)
        )
    return report


__all__ = [
    "FiqhRule",
    "Citation",
    "AnalysisContext",
    "RuleResult",
    "ValidationReport",
    "FiqhValidationError",
    "validate_ladarar",
    "validate_asalat_al_barah",
    "validate_istishab",
    "validate_asalat_al_sihhah",
    "validate_nafy_eusr_wa_haraj",
    "validate_tafsir_maddiq",
    "validate_man_atf_bimassabaq",
    "VALIDATORS",
    "validate_analysis",
    "enforce_fiqh",
]
