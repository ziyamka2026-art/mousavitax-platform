"use client";

import { FormEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Result = {
  clause_codes?: string[];
  audit_type_note?: string;
  tax_base_method?: string;
  procedure_steps?: string[];
  comparison_checklist?: string[];
  legal_refs?: string[];
  warnings?: string[];
  human_review_required?: boolean;
  disclaimer?: string;
  log_id?: string;
  rule_version?: string;
};

export default function AuditProcedurePage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    const fd = new FormData(e.currentTarget);
    const body = {
      taxpayer_kind: String(fd.get("taxpayer_kind") || "legal"),
      year: Number(fd.get("year") || 1402),
      invitation_received: fd.get("invitation_received") === "on",
      attended_on_time: fd.get("attended_on_time") === "on",
      current_audit_type: String(fd.get("current_audit_type") || "administrative"),
      books_status: String(fd.get("books_status") || "full"),
      docs_status: String(fd.get("docs_status") || "full"),
      revenue_docs: String(fd.get("revenue_docs") || "full"),
      cost_docs: String(fd.get("cost_docs") || "full"),
      legal_books_provided: fd.get("legal_books_provided") === "on",
      paper_company_tx: fd.get("paper_company_tx") === "on",
      related_party_below_fair: fd.get("related_party_below_fair") === "on",
      related_party_above_fair: fd.get("related_party_above_fair") === "on",
      concealment_activity: fd.get("concealment_activity") === "on",
      concealment_revenue: fd.get("concealment_revenue") === "on",
      opex_accepted_on_concealment: String(fd.get("opex_accepted_on_concealment") || "na"),
      facts_summary: String(fd.get("facts_summary") || ""),
      taxpayer_name: String(fd.get("taxpayer_name") || ""),
    };
    try {
      const res = await fetch(`${API}/v1/tax/audit-procedure/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      setResult(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "خطا در ارتباط با API");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8" dir="rtl">
      <h1 className="text-2xl font-bold mb-2">راهنمای نحوه صحیح حسابرسی</h1>
      <p className="text-sm text-gray-600 mb-6">
        بر اساس آیین‌نامه اجرایی ماده ۲۱۹ ق.م.م (مواد ۲۹ و ۴۱) و دستورالعمل تبیین ۲۰۰/۹۹/۵۲۲.
        وضعیت ارائه اسناد خود را مشخص کنید تا بند قانونی و روش صحیح تعیین درآمد/ماخذ استخراج شود و با گزارش حسابرسی‌تان مقایسه کنید.
      </p>

      <form onSubmit={onSubmit} className="space-y-4 rounded-xl border p-4 bg-white shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="text-sm">
            نام مودی (اختیاری)
            <input name="taxpayer_name" className="mt-1 w-full border rounded px-2 py-1" />
          </label>
          <label className="text-sm">
            سال عملکرد
            <input name="year" type="number" defaultValue={1402} className="mt-1 w-full border rounded px-2 py-1" />
          </label>
          <label className="text-sm">
            نوع مودی
            <select name="taxpayer_kind" className="mt-1 w-full border rounded px-2 py-1">
              <option value="legal">شخص حقوقی</option>
              <option value="sole">صاحب شغل (حقیقی)</option>
            </select>
          </label>
          <label className="text-sm">
            نوع حسابرسی فعلی
            <select name="current_audit_type" className="mt-1 w-full border rounded px-2 py-1">
              <option value="administrative">اداری</option>
              <option value="field">میدانی</option>
              <option value="unknown">نامشخص</option>
            </select>
          </label>
          <label className="text-sm">
            وضعیت دفاتر
            <select name="books_status" className="mt-1 w-full border rounded px-2 py-1">
              <option value="full">کامل</option>
              <option value="partial">ناقص</option>
              <option value="none">عدم ارائه</option>
            </select>
          </label>
          <label className="text-sm">
            وضعیت کلی اسناد
            <select name="docs_status" className="mt-1 w-full border rounded px-2 py-1">
              <option value="full">کامل</option>
              <option value="partial">بخشی</option>
              <option value="none">هیچ</option>
            </select>
          </label>
          <label className="text-sm">
            اسناد درآمدی
            <select name="revenue_docs" className="mt-1 w-full border rounded px-2 py-1">
              <option value="full">کامل</option>
              <option value="partial">بخشی</option>
              <option value="none">عدم ارائه</option>
            </select>
          </label>
          <label className="text-sm">
            اسناد هزینه‌ای
            <select name="cost_docs" className="mt-1 w-full border rounded px-2 py-1">
              <option value="full">کامل</option>
              <option value="partial_cogs">ناقص (بهای تمام‌شده)</option>
              <option value="partial_opex">ناقص (هزینه‌های جاری)</option>
              <option value="none">عدم ارائه</option>
            </select>
          </label>
          <label className="text-sm">
            پذیرش هزینه در کتمان درآمد
            <select name="opex_accepted_on_concealment" className="mt-1 w-full border rounded px-2 py-1">
              <option value="na">مورد ندارد</option>
              <option value="yes">پذیرفته شده</option>
              <option value="no">رد شده</option>
            </select>
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
          {[
            ["invitation_received", "دعوت‌نامه دریافت شده", true],
            ["attended_on_time", "مراجعه به‌موقع", true],
            ["legal_books_provided", "دفاتر قانونی ارائه شده", true],
            ["paper_company_tx", "معامله با شرکت کاغذی/مجهول‌المکان", false],
            ["related_party_below_fair", "فروش به وابسته کمتر از ارزش منصفانه", false],
            ["related_party_above_fair", "خرید از وابسته بیشتر از ارزش منصفانه", false],
            ["concealment_activity", "کتمان فعالیت احراز شده", false],
            ["concealment_revenue", "کتمان درآمد احراز شده", false],
          ].map(([name, label, def]) => (
            <label key={String(name)} className="flex items-center gap-2">
              <input type="checkbox" name={String(name)} defaultChecked={Boolean(def)} />
              {label}
            </label>
          ))}
        </div>

        <label className="text-sm block">
          شرح ماوقع (اختیاری)
          <textarea name="facts_summary" rows={3} className="mt-1 w-full border rounded px-2 py-1" placeholder="مثال: دفاتر ارائه شد ولی فاکتورهای خرید مواد ناقص بود..." />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-emerald-700 text-white py-2 font-medium hover:bg-emerald-800 disabled:opacity-60"
        >
          {loading ? "در حال استخراج..." : "استخراج نحوه صحیح رسیدگی"}
        </button>
      </form>

      {error && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>
      )}

      {result && (
        <section className="mt-6 space-y-4 rounded-xl border p-4 bg-slate-50">
          <div className="text-xs text-gray-500">
            نسخه قواعد: {result.rule_version} {result.log_id ? `· ${result.log_id}` : ""}
            {result.human_review_required ? " · نیاز به بازبینی انسانی" : ""}
          </div>
          <div>
            <h2 className="font-semibold mb-1">بندهای اعمال‌شده</h2>
            <ul className="list-disc pr-5 text-sm">
              {(result.clause_codes || []).map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
          <div>
            <h2 className="font-semibold mb-1">نوع حسابرسی (ماده ۲۹)</h2>
            <p className="text-sm leading-7">{result.audit_type_note}</p>
          </div>
          <div>
            <h2 className="font-semibold mb-1">روش صحیح تعیین درآمد/ماخذ (ماده ۴۱)</h2>
            <p className="text-sm leading-7">{result.tax_base_method}</p>
          </div>
          <div>
            <h2 className="font-semibold mb-1">مراحل پیشنهادی</h2>
            <ol className="list-decimal pr-5 text-sm space-y-1">
              {(result.procedure_steps || []).map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </div>
          <div>
            <h2 className="font-semibold mb-1">چک‌لیست مقایسه با گزارش حسابرسی شما</h2>
            <ul className="list-disc pr-5 text-sm space-y-1">
              {(result.comparison_checklist || []).map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
          <div>
            <h2 className="font-semibold mb-1">مستندات قانونی</h2>
            <ul className="list-disc pr-5 text-xs text-gray-700">
              {(result.legal_refs || []).map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
          {(result.warnings || []).length > 0 && (
            <div className="rounded border border-amber-300 bg-amber-50 p-3 text-sm">
              {(result.warnings || []).map((w, i) => (
                <p key={i}>{w}</p>
              ))}
            </div>
          )}
          <p className="text-xs text-gray-500">{result.disclaimer}</p>
        </section>
      )}
    </main>
  );
}
