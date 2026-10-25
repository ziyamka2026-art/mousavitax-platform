import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  DOC_CHECKLIST,
  PENALTY_TYPES,
  WAIVER_CIRCULAR_ID,
  calculateWaiver,
  type PenaltyRow,
} from "@/lib/waiver";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/waiver")({
  head: () => ({
    meta: [
      { title: "محاسبه‌گر بخشودگی جرائم مالیاتی | بخشنامه ۲۰۰/۱۴۰۴/۵۰۴" },
      {
        name: "description",
        content:
          "محاسبه درصد و مبلغ بخشودگی جرائم قابل بخشش مالیاتی بر اساس بخشنامه 200/1404/504، همراه با چک‌لیست مدارک لازم.",
      },
      { property: "og:title", content: "محاسبه‌گر بخشودگی جرائم مالیاتی" },
      {
        property: "og:description",
        content: "برآورد بخشودگی جرائم مالیاتی بر اساس بخشنامه 200/1404/504",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: WaiverPage,
});

const faNumber = (value: number) => Math.round(value).toLocaleString("fa-IR");
const faPercent = (value: number) => `${(value * 100).toLocaleString("fa-IR")}٪`;

const inputClass =
  "h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring";

function WaiverPage() {
  const [year, setYear] = useState(1403);
  const [appealStages, setAppealStages] = useState(0);
  const [reduceDebt30, setReduceDebt30] = useState(false);
  const [afterExecutive, setAfterExecutive] = useState(false);
  const [payType, setPayType] = useState<"پرداخت نقدی" | "ترتیب پرداخت">("پرداخت نقدی");
  const [art19080, setArt19080] = useState(false);
  const [art19040, setArt19040] = useState(false);
  const [isProductionUnit, setIsProductionUnit] = useState(false);
  const [payDate, setPayDate] = useState("");
  const [penalties, setPenalties] = useState<PenaltyRow[]>([
    { type: PENALTY_TYPES[0] ?? "سایر", amount: 10_000_000, waivable: true },
  ]);

  const result = useMemo(
    () =>
      calculateWaiver({
        year,
        appealStages,
        reduceDebt30,
        afterExecutiveOneMonth: afterExecutive,
        payType,
        art19080,
        art19040,
        isProductionUnit,
        payDate: payDate.trim(),
        penalties: penalties.filter((p) => p.amount > 0),
      }),
    [year, appealStages, reduceDebt30, afterExecutive, payType, art19080, art19040, isProductionUnit, payDate, penalties],
  );

  const updatePenalty = (index: number, patch: Partial<PenaltyRow>) =>
    setPenalties((prev) => prev.map((p, i) => (i === index ? { ...p, ...patch } : p)));

  return (
    <div className="min-h-screen">
      <SiteHeader />
      <header className="print-header bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-5xl px-5 py-12">
          <h1 className="text-2xl font-bold sm:text-3xl">محاسبه‌گر بخشودگی جرائم مالیاتی</h1>
          <p className="mt-3 max-w-2xl text-sm leading-8 opacity-90">
            برآورد درصد و مبلغ بخشودگی جرائم قابل بخشش بر اساس بخشنامه {WAIVER_CIRCULAR_ID} (تفویض
            اختیار بخشودگی جرائم، اجرای از ۱۴۰۴/۰۹/۰۱).
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-10">
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <div className="space-y-6">
            <section className="panel p-5">
              <h2 className="text-sm font-semibold">مشخصات پرونده</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <label className="text-xs text-muted-foreground">
                  سال مالی
                  <input
                    type="number"
                    value={year}
                    onChange={(e) => setYear(Number(e.target.value) || 1403)}
                    className={`mt-1 w-full ${inputClass}`}
                  />
                </label>
                <label className="text-xs text-muted-foreground">
                  تعداد مراحل دادرسی طی‌شده
                  <input
                    type="number"
                    min={0}
                    value={appealStages}
                    onChange={(e) => setAppealStages(Math.max(0, Number(e.target.value) || 0))}
                    className={`mt-1 w-full ${inputClass}`}
                  />
                </label>
                <label className="text-xs text-muted-foreground">
                  نحوه پرداخت
                  <select
                    value={payType}
                    onChange={(e) => setPayType(e.target.value as typeof payType)}
                    className={`mt-1 w-full ${inputClass}`}
                  >
                    <option value="پرداخت نقدی">پرداخت نقدی</option>
                    <option value="ترتیب پرداخت">ترتیب پرداخت (اقساط)</option>
                  </select>
                </label>
                <label className="text-xs text-muted-foreground">
                  تاریخ پرداخت (شمسی، مثل 1405/06/10)
                  <input
                    dir="ltr"
                    value={payDate}
                    onChange={(e) => setPayDate(e.target.value)}
                    placeholder="1405/06/10"
                    className={`mt-1 w-full ${inputClass}`}
                  />
                </label>
              </div>
              <div className="mt-4 grid gap-2 text-xs sm:grid-cols-2">
                {[
                  { label: "بدهی مالیاتی حداقل ۳۰٪ کاهش یافته است", value: reduceDebt30, set: setReduceDebt30 },
                  { label: "بیش از یک ماه از ابلاغ برگ اجرایی گذشته است", value: afterExecutive, set: setAfterExecutive },
                  { label: "معافیت ماده ۱۹۰ — قبولی تشخیص یا توافق (۸۰٪)", value: art19080, set: (v: boolean) => { setArt19080(v); if (v) setArt19040(false); } },
                  { label: "معافیت ماده ۱۹۰ — پرداخت تا یک ماه پس از قطعیت (۴۰٪)", value: art19040, set: (v: boolean) => { setArt19040(v); if (v) setArt19080(false); } },
                  { label: "واحد تولیدی یا آسیب‌دیده از جنگ رمضان", value: isProductionUnit, set: setIsProductionUnit },
                ].map((item) => (
                  <label key={item.label} className="flex items-center gap-2 rounded-lg border border-border p-2.5 leading-5">
                    <input
                      type="checkbox"
                      checked={item.value}
                      onChange={(e) => item.set(e.target.checked)}
                      className="size-4 accent-primary"
                    />
                    {item.label}
                  </label>
                ))}
              </div>
            </section>

            <section className="panel p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">جرائم (ریال)</h2>
                <button
                  onClick={() =>
                    setPenalties((prev) => [...prev, { type: PENALTY_TYPES[7] ?? "سایر قابل بخشش", amount: 0, waivable: true }])
                  }
                  className="h-8 rounded-lg border border-border px-3 text-xs hover:border-primary hover:text-primary"
                >
                  + افزودن جریمه
                </button>
              </div>
              <div className="mt-4 space-y-3">
                {penalties.map((penalty, index) => (
                  <div key={index} className="grid gap-2 rounded-lg border border-border p-3 sm:grid-cols-[1fr_140px_auto_auto] sm:items-center">
                    <select
                      value={penalty.type}
                      onChange={(e) => updatePenalty(index, { type: e.target.value })}
                      className={inputClass}
                    >
                      {PENALTY_TYPES.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min={0}
                      value={penalty.amount || ""}
                      onChange={(e) => updatePenalty(index, { amount: Number(e.target.value) || 0 })}
                      placeholder="مبلغ"
                      className={inputClass}
                    />
                    <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <input
                        type="checkbox"
                        checked={penalty.waivable}
                        onChange={(e) => updatePenalty(index, { waivable: e.target.checked })}
                        className="size-4 accent-primary"
                      />
                      قابل بخشش
                    </label>
                    <button
                      onClick={() => setPenalties((prev) => prev.filter((_, i) => i !== index))}
                      disabled={penalties.length === 1}
                      className="text-xs text-destructive disabled:opacity-30"
                    >
                      حذف
                    </button>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel p-5">
              <h2 className="text-sm font-semibold">چک‌لیست مدارک درخواست بخشودگی</h2>
              <ul className="mt-3 grid gap-1.5 text-xs leading-6 text-muted-foreground sm:grid-cols-2">
                {DOC_CHECKLIST.map((doc) => (
                  <li key={doc} className="flex items-start gap-2">
                    <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-gold" />
                    {doc}
                  </li>
                ))}
              </ul>
            </section>
          </div>

          <aside className="lg:sticky lg:top-20 lg:self-start">
            <section className="panel border-primary/30 p-5">
              <h2 className="text-sm font-semibold text-primary">نتیجه برآورد</h2>
              <dl className="mt-4 space-y-3 text-xs">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">نرخ پایه پس از کسورات</dt>
                  <dd className="font-semibold">{faPercent(result.baseAfterDeductions)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">نرخ معافیت ماده ۱۹۰</dt>
                  <dd className="font-semibold">{faPercent(result.art190Rate)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">افزایش ویژه (تولیدی/جنگ)</dt>
                  <dd className="font-semibold">{faPercent(result.specialAdd)}</dd>
                </div>
                <div className="flex justify-between border-t border-border pt-3">
                  <dt className="font-semibold">درصد نهایی بخشودگی</dt>
                  <dd className="text-base font-bold text-primary">{faPercent(result.finalPct)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">جمع جرائم قابل بخشش</dt>
                  <dd>{faNumber(result.waivableSum)} ریال</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">جمع جرائم غیرقابل بخشش</dt>
                  <dd>{faNumber(result.nonWaivableSum)} ریال</dd>
                </div>
                <div className="flex justify-between text-primary">
                  <dt className="font-semibold">مبلغ بخشودگی</dt>
                  <dd className="font-bold">{faNumber(result.waivedAmount)} ریال</dd>
                </div>
                <div className="flex justify-between border-t border-border pt-3">
                  <dt className="font-semibold">مانده قابل پرداخت</dt>
                  <dd className="font-bold">{faNumber(result.remaining)} ریال</dd>
                </div>
              </dl>
              <p className="mt-5 rounded-lg bg-gold/15 p-3 text-[11px] leading-6 text-muted-foreground">
                این خروجی صرفاً برآورد سیستمی برای بررسی کارشناس است و جایگزین رأی سازمان امور
                مالیاتی یا مشاور رسمی نیست. نرخ پایه سال ۱۴۰۳ به بعد ۱۰۰٪، ۱۴۰۲ برابر ۹۵٪، ۱۴۰۱
                برابر ۸۵٪، ۱۴۰۰ برابر ۷۵٪ و قبل از آن ۶۵٪ است؛ کف پرداخت نقدی ۳۰٪ و اقساط ۲۰٪.
              </p>
            </section>
          </aside>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
