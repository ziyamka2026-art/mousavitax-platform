import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "درباره و تماس — کتابخانه قوانین مالیاتی" },
      {
        name: "description",
        content:
          "معرفی کتابخانه قوانین و بخشنامه‌های مالیاتی، نحوه گردآوری اسناد و راه‌های ارتباط با ما.",
      },
      { property: "og:title", content: "درباره و تماس — کتابخانه قوانین مالیاتی" },
      {
        property: "og:description",
        content: "معرفی پایگاه، نحوه گردآوری اسناد و راه‌های ارتباطی",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AboutPage,
});

function AboutPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <header className="print-header bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-4xl px-5 py-12">
          <h1 className="text-2xl font-bold sm:text-3xl">درباره ما</h1>
          <p className="mt-3 max-w-2xl text-sm leading-8 opacity-90">
            هدف ما دسترسی سریع، رایگان و دقیق به متن کامل مقررات مالیاتی ایران است.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-5 py-10">
        <section className="panel p-6">
          <h2 className="text-base font-semibold text-primary">این پایگاه چه می‌کند؟</h2>
          <p className="mt-3 text-sm leading-8 text-muted-foreground">
            قوانین مالیاتی، مواد قانونی و بخشنامه‌های سازمان امور مالیاتی گردآوری، ساختاردهی و
            جستجوپذیر می‌شوند. هر ماده به مقررات مرتبط خود پیوند دارد و متن کامل هر سند قابل مطالعه،
            چاپ و ذخیره به صورت PDF است.
          </p>
        </section>

        <section className="panel mt-4 p-6">
          <h2 className="text-base font-semibold text-primary">نحوه گردآوری و به‌روزرسانی</h2>
          <ul className="mt-3 space-y-2 text-sm leading-8 text-muted-foreground">
            <li>• فهرست قوانین و بخشنامه‌ها به صورت دوره‌ای از منبع دریافت می‌شود.</li>
            <li>• متن کامل هر سند ذخیره و برای جستجوی متنی نمایه‌گذاری می‌شود.</li>
            <li>• نشانی سند اصلی در صفحه هر ماده و بخشنامه نگهداری می‌شود.</li>
          </ul>
        </section>

        <section className="panel mt-4 p-6">
          <h2 className="text-base font-semibold text-primary">تماس با ما</h2>
          <p className="mt-3 text-sm leading-8 text-muted-foreground">
            برای گزارش خطا در متن اسناد، پیشنهاد افزودن منبع جدید یا همکاری، پیام خود را به نشانی
            زیر بفرستید:
          </p>
          <p className="mt-2 text-sm font-semibold">info@example.com</p>
          <p className="mt-2 text-xs text-muted-foreground">
            (این نشانی نمونه است؛ نشانی واقعی خود را جایگزین کنید.)
          </p>
        </section>

        <section className="panel mt-4 p-6">
          <h2 className="text-base font-semibold text-primary">سلب مسئولیت</h2>
          <p className="mt-3 text-sm leading-8 text-muted-foreground">
            محتوای این پایگاه جنبه اطلاع‌رسانی دارد. مرجع رسمی، متن منتشرشده توسط مراجع قانونی است و
            استفاده از این اطلاعات جایگزین مشاوره تخصصی نیست.
          </p>
          <Link to="/faq" className="mt-4 inline-block text-sm text-primary underline">
            مشاهده پرسش‌های متداول
          </Link>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
