import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";

const FAQ = [
  {
    q: "منبع متن قوانین و بخشنامه‌ها چیست؟",
    a: "متن مواد قانونی و بخشنامه‌ها از منابع عمومی منتشرشده مقررات مالیاتی گردآوری و در این پایگاه بایگانی می‌شود. نشانی سند اصلی در صفحه هر ماده یا بخشنامه در دسترس است.",
  },
  {
    q: "چطور یک ماده مشخص را پیدا کنم؟",
    a: "در جستجوی پیشرفته شماره ماده (مثلاً «ماده ۱۳۱») یا بخشی از متن آن را وارد کنید و فیلتر «مواد قانونی» را انتخاب کنید.",
  },
  {
    q: "آیا می‌توانم از متن خروجی PDF بگیرم؟",
    a: "بله. در بالای صفحه هر قانون، ماده، بخشنامه و همچنین صفحه نتایج جستجو دکمه دانلود PDF قرار دارد که نسخه چاپی مرتب تولید می‌کند.",
  },
  {
    q: "بخشنامه‌ها چند وقت یک‌بار به‌روزرسانی می‌شوند؟",
    a: "به‌روزرسانی از طریق پنل مدیریت محتوا انجام می‌شود؛ هر بار فهرست جدید دریافت و متن کامل موارد تازه ذخیره می‌گردد.",
  },
  {
    q: "آیا این پایگاه مشاوره مالیاتی ارائه می‌دهد؟",
    a: "خیر. این پایگاه یک آرشیو اطلاع‌رسانی است و جایگزین مشاوره تخصصی یا نظر کارشناس رسمی مالیاتی نیست.",
  },
  {
    q: "اگر متنی ناقص یا نادرست بود چه کنم؟",
    a: "از صفحه «درباره و تماس» موضوع را اطلاع دهید تا سند از منبع اصلی بازخوانی و اصلاح شود.",
  },
] as const;

export const Route = createFileRoute("/faq")({
  head: () => ({
    meta: [
      { title: "پرسش‌های متداول — کتابخانه قوانین مالیاتی" },
      {
        name: "description",
        content:
          "پاسخ پرسش‌های رایج درباره جستجو در قوانین مالیاتی، منبع اسناد، خروجی PDF و به‌روزرسانی بخشنامه‌ها.",
      },
      { property: "og:title", content: "پرسش‌های متداول — کتابخانه قوانین مالیاتی" },
      {
        property: "og:description",
        content: "پاسخ پرسش‌های رایج درباره استفاده از آرشیو قوانین و بخشنامه‌های مالیاتی",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: FaqPage,
});

function FaqPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <header className="print-header bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-4xl px-5 py-12">
          <h1 className="text-2xl font-bold sm:text-3xl">پرسش‌های متداول</h1>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-5 py-10">
        <div className="space-y-3">
          {FAQ.map((item) => (
            <details key={item.q} className="panel p-5">
              <summary className="cursor-pointer text-sm font-semibold">{item.q}</summary>
              <p className="mt-3 text-sm leading-8 text-muted-foreground">{item.a}</p>
            </details>
          ))}
        </div>
        <p className="mt-8 text-sm text-muted-foreground">
          پاسخ پرسش‌تان را پیدا نکردید؟{" "}
          <Link to="/about" className="text-primary underline">
            با ما در تماس باشید
          </Link>
          .
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
