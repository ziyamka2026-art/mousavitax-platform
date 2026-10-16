import { Link } from "@tanstack/react-router";

const NAV = [
  { to: "/", label: "خانه" },
  { to: "/laws", label: "قوانین" },
  { to: "/circulars", label: "بخشنامه‌ها" },
  { to: "/search", label: "جستجوی پیشرفته" },
  { to: "/tax-help", label: "راهنمای هوشمند" },
  { to: "/waiver", label: "بخشودگی جرائم" },
  { to: "/guide", label: "خدمات مالیاتی" },
  { to: "/faq", label: "پرسش‌های متداول" },
  { to: "/about", label: "درباره ما" },
] as const;

export function SiteHeader() {
  return (
    <div className="no-print sticky top-0 z-30 border-b border-border bg-card/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-5 py-3">
        <Link to="/" className="text-sm font-bold text-primary">
          کتابخانه قوانین مالیاتی
        </Link>
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: item.to === "/" }}
              activeProps={{ className: "text-primary font-semibold" }}
              className="transition-colors hover:text-primary"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="no-print mt-16 border-t border-border bg-secondary/40">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 py-10 text-sm sm:grid-cols-3">
        <div>
          <div className="font-semibold text-primary">کتابخانه قوانین و بخشنامه‌های مالیاتی</div>
          <p className="mt-2 leading-7 text-muted-foreground">
            آرشیو جستجوپذیر متن کامل قوانین، مواد قانونی و بخشنامه‌های مالیاتی ایران، همراه با خروجی
            چاپ و PDF برای هر سند.
          </p>
        </div>
        <div>
          <div className="font-semibold">دسترسی سریع</div>
          <ul className="mt-2 space-y-1 text-muted-foreground">
            <li>
              <Link to="/laws" className="hover:text-primary">
                فهرست قوانین
              </Link>
            </li>
            <li>
              <Link to="/circulars" className="hover:text-primary">
                بخشنامه‌ها
              </Link>
            </li>
            <li>
              <Link
                to="/search"
                search={{ q: "", type: "all", page: 0 }}
                className="hover:text-primary"
              >
                جستجوی پیشرفته
              </Link>
            </li>
            <li>
              <Link to="/guide" className="hover:text-primary">
                راهنمای خدمات مالیاتی
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <div className="font-semibold">راهنما</div>
          <ul className="mt-2 space-y-1 text-muted-foreground">
            <li>
              <Link to="/faq" className="hover:text-primary">
                پرسش‌های متداول
              </Link>
            </li>
            <li>
              <Link to="/about" className="hover:text-primary">
                درباره و تماس
              </Link>
            </li>
            <li>
              <Link to="/admin" className="hover:text-primary">
                پنل مدیریت محتوا
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-border py-4 text-center text-xs text-muted-foreground">
        این پایگاه صرفاً جنبه اطلاع‌رسانی دارد و جایگزین مشاوره تخصصی مالیاتی نیست.
      </div>
    </footer>
  );
}
