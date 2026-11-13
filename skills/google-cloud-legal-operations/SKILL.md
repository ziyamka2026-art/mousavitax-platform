---
name: google-cloud-legal-operations
description: عملیات امن Google Cloud برای پلتفرم مشاوره حقوقی ایران؛ شامل IAM و احراز هویت، Google Drive/Cloud Storage، استقرار Cloud Run، logging و monitoring. Use when configuring, reviewing, troubleshooting, or deploying the legal case platform on Google Cloud.
---

# عملیات Google Cloud برای پلتفرم حقوقی

این اسکیل از الگوهای منتخب مخزن رسمی Google Skills استفاده می‌کند، اما نسخه اجرایی آن برای پرونده‌های محرمانه، حافظه اول/دوم و workflow لایحه‌نویسی بومی‌سازی شده است. قبل از هر تغییر زیرساختی، ابتدا طرح و اثر امنیتی/هزینه‌ای را مشخص کن و برای mutationهای زیرساختی تأیید انسانی بگیر.

## ترتیب اجباری

1. هدف، پروژه، محیط (`local`, `staging`, `production`) و منبع داده را مشخص کن.
2. هویت اجراکننده را تعیین کن: کاربر انسانی، Service Account، یا Workload Identity. کلید JSON را در مخزن، log یا پاسخ نمایش نده.
3. کمترین سطح دسترسی را اعمال کن. برای خواندن اسناد، `Viewer` یا نقش محدود منبع کافی است؛ از Owner/Editor و نقش‌های گسترده پروژه استفاده نکن.
4. پیش از هر دستور `gcloud`، syntax همان leaf command را با `gcloud help <leaf-command>` بررسی کن. فهرست‌های منابع را بدون `--limit`, `--filter` یا `--format` اجرا نکن.
5. برای اسناد پرونده، منبع اصلی را تغییر نده. Drive منبع حقیقت است؛ mirror محلی یا Cloud Storage باید checksum، manifest و تاریخچه داشته باشد.
6. برای storage محرمانه، دسترسی عمومی را ممنوع، uniform bucket-level access را فعال، versioning/retention را متناسب با سیاست نگهداری بررسی و lifecycle را قبل از اعمال مستند کن.
7. لاگ‌ها نباید متن کامل لایحه، OCR، شماره ملی، اطلاعات تماس یا کلیدها را ثبت کنند. در log فقط `case_id` داخلی، `source_id`، عملیات و checksum مجاز است.
8. استقرار API و worker را جدا کن: API برای درخواست کوتاه؛ worker/job برای sync، OCR، indexing و به‌روزرسانی حافظه.
9. پایش را بر چهار علامت اصلی بنا کن: latency، traffic، errors و saturation. برای sync شاخص‌های timeout، تعداد فایل، خطا، مدت اجرا و عقب‌ماندگی صف را ثبت کن.
10. قبل از production، rollback، backup، تست دسترسی یک پرونده آزمایشی و کنترل عدم نشت محرمانه را اجرا کن.

## مسیرهای کاربردی

- **احراز هویت و IAM**: `references/google-cloud-operations.md#احراز-هویت-و-iam`
- **Drive و Cloud Storage**: همان مرجع، بخش ذخیره‌سازی
- **Cloud Run**: همان مرجع، بخش استقرار
- **Logging و Monitoring**: همان مرجع، بخش مشاهده‌پذیری
- **چک‌لیست قبل از انتشار**: همان مرجع، بخش چک‌لیست

## ممنوعیت‌ها

- commit کردن Service Account JSON، OAuth token یا `.env.local`؛
- عمومی‌کردن bucket یا پوشه پرونده؛
- اجرای mutation زیرساخت بدون تأیید انسانی؛
- ثبت متن اسناد در log؛
- حذف خودکار سند Drive به‌علت تفاوت manifest؛
- قرار دادن اسناد پرونده در GitHub؛
- ادعای موفقیت استقرار بدون health check و rollback path.
