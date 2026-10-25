import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";

const SERVICES = [
  {
    title: "تنظیم و ارسال اظهارنامه مالیاتی",
    body: "مهلت‌های قانونی، مدارک لازم و مواد مرتبط با تسلیم اظهارنامه اشخاص حقیقی و حقوقی.",
    q: "اظهارنامه",
  },
  {
    title: "اعتراض و لایحه دفاعیه",
    body: "مسیر اعتراض به برگ تشخیص، مهلت‌ها و مواد مربوط به هیئت‌های حل اختلاف مالیاتی.",
    q: "هیئت حل اختلاف",
  },
  {
    title: "ارزش افزوده",
    body: "ثبت‌نام، دوره‌های مالیاتی، صورتحساب و جرایم مرتبط با قانون مالیات بر ارزش افزوده.",
    q: "ارزش افزوده",
  },
  {
    title: "معافیت‌ها و مشوق‌ها",
    body: "مواد قانونی معافیت‌های مالیاتی و شرایط برخورداری از آن‌ها.",
    q: "معافیت",
  },
  {
    title: "مالیات املاک",
    body: "نقل و انتقال، درآمد اجاره و سرقفلی و مقررات مربوط به املاک.",
    q: "املاک",
  },
  {
    title: "مالیات بر ارث",
    body: "طبقات وراث، نرخ‌ها و تشریفات گواهی واریز مالیات بر ارث.",
    q: "ارث",
  },
] as const;

export const Route = createFileRoute("/guide")({
  head: () => ({
    meta: [
      { title: "راهنمای موضوعی خدمات مالیاتی" },
      {
        name: "description",
        content:
          "راهنمای موضوعی اظهارنامه، اعتراض مالیاتی، ارزش افزوده، معافیت‌ها، املاک و ارث با پیوند به مواد قانونی مرتبط.",
      },
      { property: "og:title", content: "راهنمای موضوعی خدمات مالیاتی" },
      {
        property: "og:description",
        content: "راهنمای موضوعی مالیاتی با پیوند مستقیم به مواد و بخشنامه‌های مرتبط",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: GuidePage,
});

function GuidePage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <header className="print-header bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-5xl px-5 py-12">
          <h1 className="text-2xl font-bold sm:text-3xl">راهنمای موضوعی خدمات مالیاتی</h1>
          <p className="mt-3 max-w-2xl text-sm leading-8 opacity-90">
            برای هر موضوع پرکاربرد، خلاصه‌ای کوتاه و پیوند مستقیم به مواد قانونی و بخشنامه‌های مرتبط.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-10">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICES.map((service) => (
            <div key={service.q} className="panel flex flex-col p-5">
              <div className="text-sm font-semibold">{service.title}</div>
              <p className="mt-2 flex-1 text-xs leading-6 text-muted-foreground">{service.body}</p>
              <Link
                to="/search"
                search={{ q: service.q, type: "all", page: 0 }}
                className="mt-4 text-xs font-semibold text-primary hover:underline"
              >
                مشاهده اسناد مرتبط ←
              </Link>
            </div>
          ))}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
