# گردش‌کارهای Google Cloud برای پرونده‌های حقوقی

این مرجع، برداشت اجرایی و کوتاه‌شده از الگوهای زیر در مخزن رسمی [Google Skills](https://github.com/google/skills/tree/main/skills/cloud) است:

- `google-cloud-recipe-auth`
- `google-cloud-storage-basics`
- `google-cloud-storage-bucket-architect`
- `google-cloud-storage-diagnostic`
- `cloud-run-basics`
- `cloud-logging-configuration-basics`
- `cloud-monitoring-alert-configuration`
- `gcloud`

نسخه‌های upstream را کپی نکن؛ هنگام نیاز، نسخه روز منبع رسمی را دوباره بررسی کن.

## احراز هویت و IAM

برای توسعه محلی از ADC یا credential محلی استفاده کن. برای production، Workload Identity یا Service Account متصل به runtime را بر کلید JSON ترجیح بده. اگر کلید JSON اجتناب‌ناپذیر است، آن را خارج از repository و در secret manager یا مسیر ACL‌شده نگه دار.

پیش از اتصال، این موارد را ثبت کن:

- principal اجراکننده؛
- پروژه و محیط؛
- منبعی که باید خوانده یا نوشته شود؛
- نقش حداقلی؛
- تاریخ بازبینی و مسیر لغو دسترسی.

برای جریان فعلی Drive، Service Account باید فقط روی پوشه لازم `Viewer` باشد. برای بارگذاری خروجی در Drive، یک هویت جدا یا مجوز محدود پوشه خروجی تعریف کن؛ مجوز خواندن را به مجوز نوشتن تبدیل نکن.

## ذخیره‌سازی

ترتیب تصمیم برای آرشیو پرونده:

1. Google Drive منبع حقیقت پرونده باقی بماند.
2. mirror محلی برای parser/OCR/indexing با `manifest.json`, `sync-history.jsonl` و SHA-256 نگهداری شود.
3. اگر Cloud Storage برای backup یا پردازش حجیم اضافه شد، برای bucket پرونده این defaults را بررسی کن: uniform bucket-level access، public access prevention، location سازگار با سیاست داده، versioning در صورت نیاز، lifecycle صریح، و retention/hold پس از بررسی حقوقی.
4. نام object نباید شماره ملی یا نام کامل شخص را آشکار کند؛ از `case_id/source_id` استفاده کن.
5. قبل از فعال‌سازی retention lock یا حذف lifecycle، اثر برگشت‌ناپذیری و هزینه را به کاربر گزارش کن.

برای خطای 403 این ترتیب را دنبال کن: هویت واقعی را مشخص کن، پروژه/منبع را بررسی کن، IAM bucket و object را جداگانه بررسی کن، Uniform Bucket-Level Access و VPC Service Controls را بررسی کن و در پایان درخواست را با یک فایل آزمایشی غیرمحرمانه تکرار کن. کلیدها و متن اسناد را در خروجی diagnostic چاپ نکن.

## استقرار Cloud Run

API فعلی باید به‌صورت stateless اجرا شود و اسناد را روی filesystem موقت به‌عنوان منبع دائمی فرض نکند. sync/OCR/indexing را به Cloud Run Job یا worker جدا منتقل کن. این مرزها را حفظ کن:

- API: ایجاد پرونده، ثبت درخواست، وضعیت sync؛
- worker: دریافت افزایشی، استخراج متن، OCR، حافظه اول/دوم؛
- پایگاه داده: ledger و metadata؛
- Drive/Storage: اصل سند و آرشیو مجاز.

برای انتشار: image را immutable tag کن، environment variables محرمانه را از Secret Manager بده، service account runtime را محدود کن، health check را اجرا کن و نسخه قبلی را برای rollback نگه دار. هرگز Service Account key را داخل image یا Dockerfile نساز.

## Logging و Monitoring

لاگ ساختاریافته هر sync باید فقط شامل این fields باشد:

```json
{
  "operation": "drive_sync",
  "case_id": "case-...",
  "listed": 12,
  "downloaded": 3,
  "updated": 1,
  "unchanged": 8,
  "skipped": 0,
  "errors": 0,
  "duration_ms": 4200,
  "human_review_required": true
}
```

هرگز این موارد را log نکن: متن PDF/DOCX، OCR، شماره ملی، شماره حساب، token، `private_key`، URL امضاشده، یا متن کامل لایحه.

برای production پایش حداقلی بساز:

- latency درخواست API؛
- نرخ 4xx/5xx؛
- timeout و retry Drive؛
- تعداد فایل و حجم sync؛
- خطای parser/OCR؛
- سن آخرین sync هر پرونده؛
- مصرف CPU/Memory worker؛
- backlog صف.

Notification channel را پیش از فعال‌سازی alert مشخص کن. ایجاد metric، sink، alert یا routing ممکن است هزینه یا اثر امنیتی داشته باشد؛ قبل از mutation تأیید بگیر.

## چک‌لیست انتشار

- [ ] repository با secret scan بررسی شده است.
- [ ] Service Account JSON و `.env.local` خارج از Git هستند.
- [ ] Drive folder دقیق و کوچک برای پرونده انتخاب شده است.
- [ ] `dry-run` موفق و timeout محدود است.
- [ ] checksum و manifest تولید شده است.
- [ ] دسترسی Viewer با یک فایل آزمایشی تأیید شده است.
- [ ] API و worker هویت‌های جدا یا نقش‌های حداقلی دارند.
- [ ] لاگ بدون محتوای محرمانه است.
- [ ] health check، backup و rollback آزمایش شده‌اند.
- [ ] تأیید انسانی برای mutation و نسخه نهایی لایحه ثبت شده است.
