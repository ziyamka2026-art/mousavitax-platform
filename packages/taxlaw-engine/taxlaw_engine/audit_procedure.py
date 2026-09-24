"""Audit procedure guide – آیین‌نامه اجرایی ماده ۲۱۹ ق.م.م + دستورالعمل ۲۰۰/۹۹/۵۲۲.

Helps taxpayers map how they presented books/documents to the correct
handling under ماده ۲۹ (audit types) and ماده ۴۱ (tax-base determination),
with cross-refs to تبیین‌نامه ۲۰۰/۹۹/۵۲۲ (اجرای ماده ۴۴ آیین‌نامه).

Output is advisory only; HUMAN_REVIEW_REQUIRED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AUDIT_PROC_VERSION = "1.0.0-py"

LEGAL_SOURCES = {
    "bylaw_219": {
        "id": "آیین‌نامه اجرایی ماده ۲۱۹ ق.م.م",
        "note": "اصلاحی ۱۳۹۴/۰۴/۳۱ و الحاقات بعدی",
    },
    "circular_522": {
        "id": "۲۰۰/۹۹/۵۲۲",
        "title": "دستورالعمل تبیین انواع و ترتیبات حسابرسی مالیاتی مواد (۳۹) و (۴۱)",
        "date": "۱۳۹۹/۰۱/۲۷",
        "implements": "ماده ۴۴ آیین‌نامه ماده ۲۱۹",
    },
    "art_29": "ماده ۲۹ آیین‌نامه ماده ۲۱۹ – انواع حسابرسی (اداری / میدانی / بازرسی / بازبینی)",
    "art_41": "ماده ۴۱ آیین‌نامه ماده ۲۱۹ – تعیین درآمد/ماخذ مشمول بر اساس نحوه ارائه اسناد",
}


@dataclass
class AuditProcedureInput:
    taxpayer_kind: Literal["legal", "sole"] = "legal"
    year: int = 1402
    invitation_received: bool = True
    attended_on_time: bool = True
    current_audit_type: Literal["administrative", "field", "unknown"] = "administrative"
    books_status: Literal["full", "partial", "none"] = "full"
    docs_status: Literal["full", "partial", "none"] = "full"
    revenue_docs: Literal["full", "partial", "none"] = "full"
    cost_docs: Literal["full", "partial_cogs", "partial_opex", "none"] = "full"
    legal_books_provided: bool = True
    paper_company_tx: bool = False
    related_party_below_fair: bool = False
    related_party_above_fair: bool = False
    concealment_activity: bool = False
    concealment_revenue: bool = False
    opex_accepted_on_concealment: Literal["yes", "no", "na"] = "na"
    facts_summary: str = ""


@dataclass
class AuditProcedureResult:
    rule_version: str
    clause_codes: list[str]
    audit_type_note: str
    tax_base_method: str
    procedure_steps: list[str]
    comparison_checklist: list[str]
    legal_refs: list[str]
    warnings: list[str]
    human_review_required: bool
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_version": self.rule_version,
            "clause_codes": self.clause_codes,
            "audit_type_note": self.audit_type_note,
            "tax_base_method": self.tax_base_method,
            "procedure_steps": self.procedure_steps,
            "comparison_checklist": self.comparison_checklist,
            "legal_refs": self.legal_refs,
            "warnings": self.warnings,
            "human_review_required": self.human_review_required,
            "disclaimer": self.disclaimer,
            "sources": LEGAL_SOURCES,
        }


def calculate_audit_procedure(inp: AuditProcedureInput) -> AuditProcedureResult:
    clauses: list[str] = []
    steps: list[str] = []
    checklist: list[str] = []
    refs: list[str] = [
        LEGAL_SOURCES["bylaw_219"]["id"],
        f"{LEGAL_SOURCES['circular_522']['id']} — {LEGAL_SOURCES['circular_522']['title']}",
        LEGAL_SOURCES["art_29"],
        LEGAL_SOURCES["art_41"],
    ]
    warnings: list[str] = []
    audit_type_note = ""
    tax_base_method = ""

    if not inp.attended_on_time or inp.docs_status == "none" or (
        inp.docs_status == "partial" and inp.books_status in ("partial", "none")
    ):
        if inp.current_audit_type == "administrative":
            audit_type_note = (
                "با توجه به عدم مراجعه به‌موقع یا عدم کفایت/عدم ارائه تمام یا بخشی از اسناد، "
                "مسئول حسابرسی می‌تواند تغییر نوع از «اداری» به «میدانی» را به مسئول حوزه پیشنهاد کند "
                "(ماده ۲۹ بند الف آیین‌نامه + دستورالعمل ۲۰۰/۹۹/۵۲۲). "
                "در صورت عدم موافقت مسئول حوزه، حسابرس مکلف به تهیه گزارش با رعایت مقررات است."
            )
            clauses.append("ماده۲۹-الف-تغییر-اداری-به-میدانی")
            steps.append(
                "بررسی کنید آیا در پرونده درخواست کتبی تغییر نوع حسابرسی و پاسخ مسئول حوزه ثبت شده است."
            )
        else:
            audit_type_note = "حسابرسی میدانی: حضور در محل و ارائه دفاتر/اسناد در طول دوره اعلام‌شده (ماده ۲۹ بند ب)."
            clauses.append("ماده۲۹-ب-میدانی")
    else:
        if inp.current_audit_type == "field":
            audit_type_note = "حسابرسی میدانی با ارائه اسناد؛ صورتمجلس دو نسخه الزامی است (تبصره ۳ ماده ۲۹)."
            clauses.append("ماده۲۹-ب")
        else:
            audit_type_note = (
                "حسابرسی اداری با مراجعه مودی و ارائه اسناد؛ پس از حسابرسی حداکثر ظرف ۶ روز کاری "
                "اسناد مسترد می‌شود (ماده ۲۹ بند الف)."
            )
            clauses.append("ماده۲۹-الف")

    steps.append("وجود دعوت‌نامه ارائه دفاتر/اسناد و صورتمجلس ارائه (دو نسخه) را با گزارش حسابرسی مطابقت دهید.")
    checklist.append("دعوت‌نامه + تاریخ ابلاغ + فاصله ۷ تا ۱۵ روز تا مراجعه (تبصره ۱ ماده ۲۹)")
    checklist.append("صورتمجلس ارائه دفاتر و اسناد (فهرست تفکیکی، نه عبارات کلی — تبصره ۳ ماده ۲۹ / دستورالعمل)")

    if inp.concealment_activity:
        clauses.append("ماده۴۱-بند۴-۱-کتمان-فعالیت")
        tax_base_method = (
            "کتمان فعالیت: درآمد/ماخذ با در نظر گرفتن نسبت سود فعالیت مشاغل مشابه "
            "(سامانه طرح جامع یا نسبت اعلامی سازمان تا ۱۵ مرداد هر سال) تعیین می‌شود."
        )
        steps.append("اطلاعات خارجی/بانکی/بازرسی که مبنای کتمان فعالیت قرار گرفته را فهرست و با گزارش مقایسه کنید.")
        checklist.append("مستند کتمان فعالیت + نسبت سود فعالیت اعمال‌شده")
    elif inp.concealment_revenue:
        clauses.append("ماده۴۱-بند۴-۲-کتمان-درآمد")
        if inp.opex_accepted_on_concealment == "yes":
            tax_base_method = (
                "کتمان درآمد + پذیرش هزینه‌های عمومی/اداری/فروش: کل درآمد کتمان‌شده پس از کسر بهای تمام‌شده "
                "آن بخش، با رعایت مقررات، مبنای سود مشمول است (۴-۲-۱)."
            )
            clauses.append("ماده۴۱-۴-۲-۱")
        elif inp.opex_accepted_on_concealment == "no":
            tax_base_method = (
                "کتمان درآمد + عدم پذیرش هزینه‌های عمومی/اداری/فروش: مشابه کتمان فعالیت با نسبت سود فعالیت (۴-۲-۲ ← ۴-۱)."
            )
            clauses.append("ماده۴۱-۴-۲-۲")
        else:
            tax_base_method = (
                "کتمان درآمد: اگر کل هزینه مربوط به درآمد قبلاً پذیرفته شده، کل رقم درآمد کتمان‌شده مبنای محاسبه است (۴-۲-۳)."
            )
            clauses.append("ماده۴۱-۴-۲-۳")
        checklist.append("رقم درآمد کتمان‌شده و نحوه برخورد با بهای تمام‌شده / هزینه‌های عمومی")
    elif inp.docs_status == "none" and inp.books_status == "none":
        clauses.append("ماده۴۱-بند۳-عدم-ارائه-تمامی-اسناد")
        tax_base_method = (
            "عدم ارائه تمامی اسناد و مدارک درآمدی و هزینه‌ای: درآمد/ماخذ با حجم فعالیت و نسبت سود فعالیت "
            "(ابراز مودی / مشاغل مشابه / نسبت سازمان) و رعایت ماده ۹۴ ق.م.م تعیین می‌شود."
        )
        steps.append("نسبت سود فعالیت و حجم فعالیت مبنای برگ تشخیص را از گزارش استخراج و با جداول سازمان مقایسه کنید.")
        checklist.append("حجم فعالیت + نسبت سود فعالیت + استناد ماده ۹۴")
    elif not inp.legal_books_provided:
        clauses.append("ماده۴۱-بند۲-۴-جریمه-۱۹۳")
        warnings.append("عدم ارائه دفاتر قانونی → مطالبه جریمه ماده ۱۹۳ ق.م.م (علاوه بر روش تعیین درآمد).")
        checklist.append("جریمه ماده ۱۹۳ در برگ تشخیص/مطالبه")

    if not tax_base_method:
        if (
            inp.docs_status == "full"
            and inp.books_status == "full"
            and inp.revenue_docs == "full"
            and inp.cost_docs == "full"
        ):
            clauses.append("ماده۴۱-بند۱-۱")
            tax_base_method = (
                "تسلیم کامل دفاتر و اسناد قابل حسابرسی: درآمد/ماخذ از طریق حسابرسی به دفاتر و اسناد ارائه‌شده "
                "طبق قوانین و احکام مالیاتی تعیین می‌شود (ترجیح قانونی — پذیرش اظهارنامه در نبود دلیل متقن خلاف)."
            )
            steps.append(
                "گزارش باید متکی به دفاتر/اسناد باشد؛ استفاده از نسبت سود فعالیت در این حالت خلاف روال اصلی است مگر استثنای مستند."
            )
            checklist.append("آیا برگ تشخیص صرفاً بر اساس دفاتر است یا بدون استناد به نسبت سود؟")
        else:
            if inp.cost_docs in ("partial_cogs", "none") and inp.docs_status != "none":
                clauses.append("ماده۴۱-بند۲-۱-قیمت-تمام-شده")
                tax_base_method = (
                    "عدم ارائه مدارک قیمت تمام‌شده (آنالیز، گردش مواد، فاکتور خرید و …) در حالی که روش دیگر "
                    "برآورد ممکن نباشد: بهای تمام‌شده آن بخش با نسبت سود ناویژه به فروش (ابراز / مشاغل مشابه / نسبت سازمان) محاسبه می‌شود."
                )
                checklist.append("نسبت سود ناویژه اعمال‌شده برای بخش فاقد مدرک COGS")
            if inp.cost_docs == "partial_opex":
                clauses.append("ماده۴۱-بند۲-۳-۲-هزینه-بدون-مدرک")
                tax_base_method = (
                    (tax_base_method + " | " if tax_base_method else "")
                    + "عدم ارائه بخشی از مدارک هزینه‌ای (غیر از بهای تمام‌شده): همان هزینه از نظر مالیاتی قابل قبول نیست."
                )
                checklist.append("اقلام هزینه ردشده به دلیل فقدان مدرک")
            if inp.revenue_docs == "none":
                clauses.append("ماده۴۱-بند۲-۲-۱-اسناد-درآمدی")
                tax_base_method = (
                    (tax_base_method + " | " if tax_base_method else "")
                    + "عدم ارائه تمام اسناد درآمدی (مؤدی مکلف به صدور صورتحساب): در صورت نبود دلیل بر فروش بیشتر، "
                    + "فروش ابرازی قبول و صرفاً جرائم عدم صدور صورتحساب؛ در صورت احراز کتمان، درآمد به‌دست‌آمده مبنا است."
                )
            elif inp.revenue_docs == "partial":
                clauses.append("ماده۴۱-بند۲-۲-۲")
                tax_base_method = (
                    (tax_base_method + " | " if tax_base_method else "")
                    + "بخش دارای مدرک درآمدی طبق بند ۱؛ بخش فاقد مدرک طبق ۲-۲-۱."
                )
            if not tax_base_method:
                clauses.append("ماده۴۱-جزئی-اختلاط")
                tax_base_method = (
                    "وضعیت اسناد مختلط است؛ ترکیب بندهای ماده ۴۱ باید صریحاً در گزارش حسابرسی ذکر شود. "
                    "بدون تفکیک بند قانونی، گزارش قابل اعتراض است."
                )
                warnings.append("در گزارش حسابرسی بند دقیق ماده ۴۱ برای هر بخش درآمد/هزینه باید مشخص باشد.")

    if inp.paper_company_tx:
        clauses.append("ماده۴۱-بند۱-۲-شرکت-کاغذی")
        steps.append(
            "معاملات با اشخاص کاغذی/مجهول‌المکان: خرید بر اساس ارزش منصفانه (مابه‌التفاوت غیرقابل قبول)؛ "
            "فروش بر اساس ارزش منصفانه (مابه‌التفاوت به درآمد اضافه). بخشنامه ۲۰۰/۹۹/۵۳ نیز مرتبط است."
        )
        checklist.append("ارزش منصفانه معاملات مشکوک + مستند وضعیت طرف معامله")
        refs.append("بخشنامه ۲۰۰/۹۹/۵۳ (اشخاص کاغذی/مجهول‌المکان)")

    if inp.related_party_below_fair:
        clauses.append("ماده۴۱-بند۱-۳-۱-وابسته-کمتر-از-منصفانه")
        steps.append("فروش به وابسته کمتر از ارزش منصفانه با انتقال سود: مابه‌التفاوت به درآمد فروشنده اضافه می‌شود.")
        checklist.append("تعدیل قیمت انتقالی (transfer pricing) فروشنده")

    if inp.related_party_above_fair:
        clauses.append("ماده۴۱-بند۱-۳-۲-وابسته-بیشتر-از-منصفانه")
        steps.append("خرید از وابسته بیشتر از ارزش منصفانه با انتقال سود: مابه‌التفاوت از هزینه/بهای تمام‌شده خریدار کسر می‌شود.")
        checklist.append("تعدیل قیمت انتقالی خریدار")

    steps.append(
        "خروجی این ابزار را بند‌به‌بند با «گزارش حسابرسی مالیاتی» و برگ تشخیص خود مقایسه کنید؛ "
        "هر انحراف بدون استناد به ماده ۴۱ یا ماده ۲۹ را یادداشت کنید."
    )
    steps.append(
        "برای لایحه دفاعی: صورتمجلس، فهرست اسناد ارائه‌شده/نشده، و بند قانونی مورد استناد حسابرس را ضمیمه کنید."
    )
    checklist.append("HUMAN_REVIEW: نتیجه نهایی فقط پس از بررسی مشاور رسمی معتبر است")

    if inp.facts_summary.strip():
        steps.append(f"شرح ماوقع ثبت‌شده توسط مودی: {inp.facts_summary.strip()[:500]}")

    warnings.append(
        "این خروجی جایگزین رأی سازمان امور مالیاتی نیست و برای مقایسه و دفاع کارشناسی است."
    )

    return AuditProcedureResult(
        rule_version=AUDIT_PROC_VERSION,
        clause_codes=clauses or ["نیاز-به-بررسی-دستی"],
        audit_type_note=audit_type_note or "نوع حسابرسی را از روی دعوت‌نامه/گزارش مشخص کنید.",
        tax_base_method=tax_base_method or "روش تعیین ماخذ از روی بندهای ماده ۴۱ مشخص نشد — بررسی دستی.",
        procedure_steps=steps,
        comparison_checklist=checklist,
        legal_refs=refs,
        warnings=warnings,
        human_review_required=True,
        disclaimer=(
            "خروجی سیستمی بر اساس آیین‌نامه ماده ۲۱۹ و دستورالعمل ۲۰۰/۹۹/۵۲۲ برای راهنمایی مودی و مشاور است. "
            "HUMAN_REVIEW_REQUIRED — تصمیم نهایی با مراجع قانونی و مشاور رسمی (۰۹۱۵۳۰۶۸۳۲۲)."
        ),
    )


def audit_procedure_meta() -> dict[str, Any]:
    return {
        "version": AUDIT_PROC_VERSION,
        "sources": LEGAL_SOURCES,
        "fields": {
            "taxpayer_kind": ["legal", "sole"],
            "books_status": ["full", "partial", "none"],
            "docs_status": ["full", "partial", "none"],
            "revenue_docs": ["full", "partial", "none"],
            "cost_docs": ["full", "partial_cogs", "partial_opex", "none"],
            "current_audit_type": ["administrative", "field", "unknown"],
        },
        "human_review_required": True,
    }


def run_audit_procedure_smoke() -> list[dict[str, Any]]:
    r1 = calculate_audit_procedure(
        AuditProcedureInput(docs_status="full", books_status="full", revenue_docs="full", cost_docs="full")
    )
    r2 = calculate_audit_procedure(
        AuditProcedureInput(docs_status="none", books_status="none", attended_on_time=False)
    )
    r3 = calculate_audit_procedure(
        AuditProcedureInput(concealment_revenue=True, opex_accepted_on_concealment="yes")
    )
    return [
        {"name": "اسناد کامل → بند ۱-۱", "ok": "ماده۴۱-بند۱-۱" in r1.clause_codes, "detail": r1.clause_codes},
        {
            "name": "بدون سند → بند ۳ + تغییر نوع",
            "ok": any("بند۳" in c or "میدانی" in c for c in r2.clause_codes),
            "detail": r2.clause_codes,
        },
        {
            "name": "کتمان درآمد + پذیرش هزینه → ۴-۲-۱",
            "ok": "ماده۴۱-۴-۲-۱" in r3.clause_codes,
            "detail": r3.clause_codes,
        },
    ]
