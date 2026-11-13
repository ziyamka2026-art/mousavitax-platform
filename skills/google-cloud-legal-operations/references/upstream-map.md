# نگاشت منابع upstream

بررسی در 2026-11-13 روی شاخه `main/skills/cloud` مخزن رسمی Google Skills انجام شد. این شاخه 174 اسکیل داشت. به‌جای vendor کردن همه موارد، فقط الگوهای مرتبط با معماری فعلی MousaviTax استخراج شد.

## ادغام‌شده به‌صورت بومی

- `google-cloud-recipe-auth`: تفکیک authentication/authorization، کمترین دسترسی، ترجیح ADC/Workload Identity بر کلید JSON.
- `google-cloud-storage-basics`: public access prevention، uniform bucket-level access، versioning، lifecycle و signed URL با کنترل محرمانگی.
- `google-cloud-storage-bucket-architect`: تصمیم‌گیری قبل از ساخت storage با توجه به حساسیت، location، retention و هزینه.
- `google-cloud-storage-diagnostic`: مسیر عیب‌یابی 403 و تفکیک IAM bucket/object.
- `cloud-run-basics`: جداسازی API stateless از worker/job و استفاده از secret runtime.
- `cloud-logging-configuration-basics`: جلوگیری از ثبت متن پرونده و کنترل اثر هزینه/امنیت sink و metric.
- `cloud-monitoring-alert-configuration`: چهار علامت اصلی و شاخص‌های اختصاصی sync، بدون ساخت alert خودکار.
- `gcloud`: الزام اعتبارسنجی syntax leaf command و محدودکردن خروجی list.

## فعلاً ادغام‌نشده

- BigQuery، Bigtable، Spanner، AlloyDB، GKE و Vertex AI: در معماری شاخه فعلی استفاده مستقیم ندارند.
- API Gateway و Apigee: endpointهای فعلی مستقیم FastAPI هستند و gateway در repository پیکربندی نشده است.
- Firebase، Genkit، Agent Platform و Gemini API: نیاز کسب‌وکار فعلی را پوشش نمی‌دهند و ادغام زودهنگام پیچیدگی ایجاد می‌کند.
- Cloud Armor، SLOهای کامل و alert policyهای production: تا تعیین پروژه، محیط، notification channel و بودجه deploy نمی‌شوند.

## سیاست نگهداری

این فایل فقط نگاشت و تصمیم طراحی است و جایگزین منابع رسمی upstream نیست. پیش از اجرای دستورهای Google Cloud، نسخه جاری اسکیل منبع و syntax رسمی همان ابزار بررسی شود.
