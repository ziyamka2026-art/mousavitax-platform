# ارزیابی mousavitax-v2

## نتیجه تصمیم

نسخه `mousavitax-v2.zip` بررسی شد. این فایل یک MVP مستقل و آموزشی با ۲۶ فایل و حدود ۸ کیلوبایت کد است، اما نسبت به نسخه فعلی پروژه بهبود قابل‌ادغام و ایمنی ایجاد نمی‌کند. بنابراین کد v2 مستقیماً روی پروژه اصلی overwrite نشد.

## مقایسه قابلیت‌ها

| قابلیت | نسخه v2 | پروژه فعلی | تصمیم |
|---|---|---|---|
| Health API | دارد | دارد و version/knowledge status بیشتری ارائه می‌کند | عدم ادغام |
| Tax Case | in-memory و بدون auth | PostgreSQL ORM، Alembic، مالکیت پرونده و RBAC | نسخه فعلی حفظ شد |
| Document metadata | فقط filename و content type | کنترل ownership، ذخیره‌سازی امن metadata، hash و وضعیت scan | نسخه فعلی کامل‌تر است |
| Audit | فهرست in-memory | جدول `audit_log`، helper پایگاه‌داده و trigger append-only | نسخه فعلی حفظ شد |
| Citation | مدل ساده با `verified` | RAG واقعی با citationهای مبتنی بر hit و وضعیت `INSUFFICIENT_DATA` | ادغام مستقیم لازم نیست |
| RAG | جست‌وجوی token ساده و بدون داده پیش‌فرض | retrieval/embedding service و منع citation جعلی | نسخه فعلی ایمن‌تر است |
| AI Gateway | پاسخ stub با confidence صفر | gateway قابل‌تنظیم و fallback extractive | نسخه فعلی حفظ شد |
| امنیت | endpointهای `/cases` و `/query` عمومی | JWT، RBAC، کنترل IDOR و تست‌های امنیتی | v2 نباید جایگزین شود |
| persistence | دیکشنری‌های حافظه | PostgreSQL و migrationهای Alembic | v2 برای production نامناسب است |

## یافته‌های مهم

نسخه v2 در خود README تصریح می‌کند که storage آن in-memory است و برای production مناسب نیست. در `apps/api/main.py` نیز endpointهای ایجاد پرونده، دریافت پرونده، افزودن سند و دریافت audit بدون احراز هویت و بدون کنترل مالکیت ارائه شده‌اند. انتقال این endpointها باعث ایجاد bypass امنیتی و از بین رفتن کنترل‌های IDOR نسخه فعلی می‌شد.

RAG نسخه v2 در صورت نبود نتیجه، متن `No verified knowledge was retrieved` را برمی‌گرداند و gateway همیشه پاسخ stub تولید می‌کند. پروژه فعلی در نبود evidence واقعی، LLM را صدا نمی‌زند، citation جعلی تولید نمی‌کند و وضعیت `INSUFFICIENT_DATA` و `HUMAN_REVIEW_REQUIRED` را برمی‌گرداند. این رفتار برای سامانه مالیاتی مناسب‌تر است.

## بخش‌های قابل استفاده به‌عنوان ایده

مرزبندی ساده v2 میان `TaxCaseService`، `AuditLog`، `RetrievalEngine` و `AIGateway` با معماری فعلی هم‌راستا است، اما این مرزبندی در پروژه اصلی با PostgreSQL، RBAC، citation واقعی و audit پایدار پیاده‌سازی شده است. بنابراین ارزش v2 در مستندسازی مفهوم MVP است، نه در جایگزینی کد production-oriented فعلی.

## اقدام انجام‌شده

هیچ فایل اجرایی v2 روی پروژه اصلی overwrite نشد. تنها این گزارش به‌عنوان سابقه بررسی و تصمیم معماری اضافه شد تا در آینده مشخص باشد چرا endpointهای in-memory و عمومی v2 وارد هسته MousaviTax نشده‌اند.

برای پذیرش هر بخش از v2 در آینده، حداقل این شروط لازم است: اتصال به ORM و migration، احراز هویت و authorization، کنترل مالکیت پرونده، ذخیره‌سازی پایدار، ثبت audit در PostgreSQL، provenance واقعی برای citation و تست‌های regression امنیتی.

**Archived by MKA Manager · 2026-09-10 · Canonical repo: ziyamka2026-art/mousavitax-platform**
