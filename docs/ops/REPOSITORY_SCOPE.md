# Repository Scope & Cleanup Policy

## مرجع اصلی
**ziyamka2026-art/mousavitax-platform** تنها مخزن مرجع پروژه‌های مالیاتی MousaviTax است.

در بررسی فعلی GitHub، این repository تنها نتیجه مرتبط مستقیم با `mousavitax-platform` برای حساب مالک پروژه بود. بنابراین از این تاریخ، همه توسعه‌های مالیاتی باید به همین مخزن هدایت شوند.

## مرزبندی محصول
### هسته مالیاتی — KEEP
- `domains/iran-tax/**`
- `packages/taxlaw-engine/**`
- `packages/knowledge-core/**`
- `packages/prompt-engine/**`
- `packages/ai-gateway/**`
- `packages/retrieval-engine/**`
- `packages/document-parser/**`
- `knowledge/**`
- `templates/**` در صورت وابستگی به خدمات مالیاتی

### سرویس/API — KEEP
- `apps/api/**`
- `packages/shared/**`
- `infra/**`
- `tests/**` مربوط به محصول

### واسط‌ها/کانال‌ها — KEEP
- `apps/web/**`
- `apps/telegram-bot/**`
- `apps/bale-bot/**`
- `apps/admin/**`
اینها کانال/واسط هستند و نباید منطق مالیاتی مستقل و متناقض بسازند.

### اسناد و عملیات — KEEP
- `docs/**`
- `scripts/**` فقط در صورت ارتباط با build/test/data pipeline

## سیاست اضافات
فعلاً هیچ پوشه‌ای صرفاً با مشاهده نام حذف نمی‌شود.
هر مورد باید ممیزی شود:
- KEEP: بخشی از محصول
- REFACTOR: لازم ولی ساختار نامناسب
- MERGE: قابلیت تکراری
- MOVE: در محل نامناسب
- ARCHIVE: تاریخی/مرجع قدیمی
- DELETE: غیرمرتبط یا بلااستفاده پس از اثبات نبود dependency

## مواردی که نیازمند ممیزی عمیق‌اند
- `templates/contracts/**`
- `scripts/**`
- محتوای `knowledge/**`
- هر کد تکراری بین botها و API
- هر implementation قدیمی که با معماری ADR-007 تعارض دارد

## قاعده مهم
«حذف اضافات» یک مرحله مستقل Cleanup است و تا تهیه dependency inventory و تأیید Work Order انجام نمی‌شود.
