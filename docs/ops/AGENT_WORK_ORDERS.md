# Initial Parallel Work Orders

## Agent A — AGENT-BE-SECURITY-DATA

### مأموریت
اجرای مرحله بعدی WO-2026-002 با تمرکز بر persistence و امنیت Backend، بدون تغییر UI.

### محدوده
`apps/api/**`
`packages/shared/**`
`packages/ai-gateway/**`
`infra/**` در صورت نیاز مستقیم

### ترتیب
1. وضعیت فعلی JSONL persistence را inventory کن.
2. مدل داده Case/Document/Service Request را استخراج کن.
3. طرح PostgreSQL migration را rollback-capable طراحی کن.
4. Authentication/RBAC را طبق مالکیت Case/Document طراحی و پیاده کن.
5. IDOR/ownership checks را اضافه کن.
6. upload security را تقویت کن.
7. CORS و startup failure behavior را اصلاح کن.
8. audit trail را تکمیل کن.
9. تست regression بنویس.
10. گزارش مرحله‌ای ثبت کن.

### ممنوع
- تغییر `apps/web/**`
- تغییر UX
- افزودن قابلیت جدید خارج از WO-2026-002
- حذف فایل بدون cleanup order

### خروجی
branch اختصاصی + commitهای کوچک + تست + report + درخواست دستور بعدی.

---

## Agent B — AGENT-FE-UX

### مأموریت
بازطراحی رابط کاربری MousaviTax با ظاهر شاد، جذاب، حرفه‌ای و RTL، بدون تغییر منطق مالیاتی/API.

### محدوده
فقط `apps/web/**`

### ترتیب
1. ساختار فعلی صفحات و componentها را inventory کن.
2. design tokens و palette مشترک تعریف کن.
3. homepage و navigation را بازطراحی کن.
4. کارت‌های خدمات، CTAها، states و فرم‌ها را یکپارچه کن.
5. responsive/mobile را بررسی کن.
6. accessibility، focus و reduced-motion را بررسی کن.
7. build/lint/typecheck موجود پروژه را اجرا کن.
8. گزارش تصویری/توضیحی تغییرات ثبت کن.

### ممنوع
- تغییر API
- تغییر backend
- تغییر مدل مالیاتی
- تغییر database
- افزودن route مالیاتی بدون Work Order

### خروجی
branch اختصاصی + PR + تست + report + درخواست دستور بعدی.

## قانون همکاری
Agent A و B می‌توانند هم‌زمان کار کنند چون مالکیت فایل‌های آنها جداست.
اگر هر دو به یک فایل نیاز پیدا کردند: توقف تغییر آن فایل و ارجاع به ARCHITECTURE/GOVERNANCE.
