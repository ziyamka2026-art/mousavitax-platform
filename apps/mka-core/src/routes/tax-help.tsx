import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { useState } from "react";
import { getTaxGuidance } from "@/lib/tax-help.functions";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/tax-help")({
  head: () => ({
    meta: [
      { title: "راهنمای هوشمند مسائل مالیاتی | کتابخانه قوانین مالیاتی" },
      {
        name: "description",
        content:
          "مسئله مالیاتی خود را آزادانه بنویسید و راهنمایی آموزشی و مراحل پیشنهادی مبتنی بر قوانین و بخشنامه‌های مالیاتی ایران دریافت کنید.",
      },
      { property: "og:title", content: "راهنمای هوشمند مسائل مالیاتی" },
      {
        property: "og:description",
        content: "راهنمایی آموزشی و مراحل پیشنهادی برای مسائل مالیاتی با پشتیبانی هوش مصنوعی",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: TaxHelpPage,
});

const EXAMPLES = [
  "اظهارنامه ارزش افزوده‌ام را دیر ارسال کرده‌ام؛ چه جریمه‌ای تعلق می‌گیرد و چطور می‌توانم درخواست بخشودگی بدهم؟",
  "برگ تشخیص مالیات برایم صادر شده و با آن موافق نیستم؛ مراحل اعتراض چیست؟",
  "کارفرما هستم و مالیات حقوق کارکنان را دیر پرداخت کرده‌ام؛ تکلیف چیست؟",
];

function TaxHelpPage() {
  const [question, setQuestion] = useState("");
  const guidanceFn = useServerFn(getTaxGuidance);

  const guidance = useMutation({
    mutationFn: (text: string) => guidanceFn({ data: { question: text } }),
  });

  const submit = () => {
    if (question.trim().length < 10 || guidance.isPending) return;
    guidance.mutate(question.trim());
  };

  return (
    <div className="min-h-screen">
      <SiteHeader />
      <header className="print-header bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-4xl px-5 py-12">
          <h1 className="text-2xl font-bold sm:text-3xl">راهنمای هوشمند مسائل مالیاتی</h1>
          <p className="mt-3 max-w-2xl text-sm leading-8 opacity-90">
            مسئله مالیاتی خود را به زبان ساده بنویسید؛ راهنمایی آموزشی، قوانین مرتبط و مراحل
            پیشنهادی را با ذکر منبع دریافت می‌کنید: ابتدا مخزن اسناد، سپس قوانین و بخشنامه‌ها و در صورت نیاز سایت سازمان امور مالیاتی و قوانین مجلس.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-5 py-10">
        <section className="panel p-5">
          <label className="text-sm font-semibold" htmlFor="tax-question">
            مسئله مالیاتی شما
          </label>
          <textarea
            id="tax-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={6}
            placeholder="مثلاً: اظهارنامه ارزش افزوده‌ام را دیر ارسال کرده‌ام؛ چه کار کنم؟"
            className="mt-3 w-full rounded-lg border border-input bg-background p-4 text-sm leading-7 outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              onClick={submit}
              disabled={guidance.isPending || question.trim().length < 10}
              className="h-11 rounded-lg bg-primary px-6 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {guidance.isPending ? "در حال بررسی مسئله…" : "دریافت راهنمایی"}
            </button>
            <span className="text-xs text-muted-foreground">
              پاسخ ممکن است تا چند دقیقه طول بکشد؛ لطفاً صفحه را نبندید.
            </span>
          </div>
          {guidance.error && (
            <p className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              {guidance.error.message}
            </p>
          )}
        </section>

        <section className="mt-6">
          <h2 className="text-sm font-semibold text-muted-foreground">چند نمونه مسئله</h2>
          <div className="mt-3 grid gap-2">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                onClick={() => setQuestion(example)}
                className="panel p-3 text-right text-xs leading-6 text-muted-foreground transition-colors hover:text-primary"
              >
                {example}
              </button>
            ))}
          </div>
        </section>

        {guidance.data && (
          <section className="panel mt-8 p-6">
            <h2 className="text-lg font-semibold text-primary">راهنمایی پیشنهادی</h2>
            <div className="law-text mt-4 whitespace-pre-line text-foreground/90">
              {guidance.data.answer}
            </div>
            {guidance.data.sources.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold">منابع استفاده‌شده</h3>
                <ul className="mt-3 space-y-2">
                  {guidance.data.sources.map((src) => (
                    <li key={src.id} className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="rounded bg-primary px-1.5 py-0.5 font-mono text-primary-foreground">{src.id}</span>
                      <span
                        className={`rounded px-2 py-0.5 ${src.origin === "drive" ? "bg-gold text-gold-foreground" : "bg-secondary text-secondary-foreground"}`}
                      >
                        {src.originLabel}
                      </span>
                      <a href={src.href} target="_blank" rel="noreferrer" className="text-primary underline">
                        {src.title}
                      </a>
                      {src.meta && <span className="text-muted-foreground">— {src.meta}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="mt-6 rounded-lg bg-secondary/60 p-3 text-xs leading-6 text-muted-foreground">
              این راهنمایی صرفاً جنبه اطلاع‌رسانی و آموزشی دارد و جایگزین مشاوره رسمی مالیاتی یا
              رأی سازمان امور مالیاتی نیست. برای متن دقیق قوانین و بخشنامه‌ها از{" "}
              <Link to="/search" search={{ q: "", type: "all", page: 0 }} className="text-primary underline">
                جستجوی پیشرفته کتابخانه
              </Link>{" "}
              استفاده کنید.
            </p>
          </section>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
