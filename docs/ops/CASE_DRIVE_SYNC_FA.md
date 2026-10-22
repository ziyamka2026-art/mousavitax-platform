# راهنمای اتصال و همگام‌سازی پرونده با Google Drive

## هدف

در این نسخه، Google Drive منبع اصلی اسناد پرونده است. پلتفرم فقط یک mirror محلی برای استخراج متن، OCR و نمایه‌سازی می‌سازد. اصل اسناد در Drive باقی می‌ماند و حذف خودکار فایل محلی یا Drive انجام نمی‌شود.

## مرحله ۱: ساخت پوشه پرونده در Drive

برای هر پرونده یک پوشه بسازید:

```text
پرونده‌ها/case-1405-abgin-gostar-toos/
```

شناسه پوشه را از URL یا جزئیات Google Drive بردارید. فایل‌های پرونده را داخل همان پوشه یا زیرپوشه‌های آن قرار دهید.

## مرحله ۲: اشتراک پوشه با Service Account

یک Service Account در Google Cloud بسازید و Drive API را فعال کنید. ایمیل Service Account را فقط با پوشه پرونده و پوشه قوانین، با سطح Viewer، به اشتراک بگذارید. فایل JSON کلید را خارج از GitHub نگه دارید؛ نمونه مسیر ویندوز:

```text
D:\secrets\mousavitax-drive-reader.json
```

## مرحله ۳: نصب وابستگی‌ها در Windows

از ریشه repository اجرا کنید:

```powershell
python -m pip install -r apps\api\requirements.txt
```

یا حداقل:

```powershell
python -m pip install google-api-python-client google-auth
```

## مرحله ۴: اجرای dry-run

پیش از دریافت فایل‌ها، فهرست تغییرات را آزمایش کنید:

```powershell
$env:GOOGLE_SERVICE_ACCOUNT_JSON = "D:\secrets\mousavitax-drive-reader.json"
python scripts\sync_case_drive.py `
  --case-id "case-1405-abgin-gostar-toos" `
  --folder-id "DRIVE_FOLDER_ID" `
  --dry-run
```

در این مرحله هیچ فایل محلی دریافت نمی‌شود.

## مرحله ۵: همگام‌سازی واقعی

```powershell
python scripts\sync_case_drive.py `
  --case-id "case-1405-abgin-gostar-toos" `
  --folder-id "DRIVE_FOLDER_ID"
```

خروجی در این مسیر ساخته می‌شود:

```text
data\case_drive_mirror\case-1405-abgin-gostar-toos\
├── manifest.json
├── sync-history.jsonl
└── ... اصل کپی محلی برای پردازش ...
```

## مرحله ۶: رفتار همگام‌سازی افزایشی

در اجرای بعدی:

- فایل تغییرنکرده دوباره دانلود نمی‌شود؛
- فایل جدید دریافت می‌شود؛
- فایل تغییرکرده با فایل موقت و جایگزینی اتمیک ذخیره می‌شود؛
- checksum SHA-256 ثبت می‌شود؛
- تاریخچه در `sync-history.jsonl` باقی می‌ماند؛
- فایل حذف‌شده از Drive به‌صورت خودکار از mirror حذف نمی‌شود.

## مرحله ۷: استفاده از API

API را با مسیرهای پروژه اجرا کنید:

```powershell
$env:CASE_DRIVE_MIRROR_ROOT = "D:\mousavitax-data\case_drive_mirror"
$env:GOOGLE_SERVICE_ACCOUNT_JSON = "D:\secrets\mousavitax-drive-reader.json"
$env:PYTHONPATH = "packages;apps\api"
uvicorn app.main:app --app-dir apps\api --reload
```

اجرای dry-run از API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/v1/cases/case-1405-abgin-gostar-toos/drive/sync" `
  -ContentType "application/json" `
  -Body '{"folder_id":"DRIVE_FOLDER_ID","dry_run":true}'
```

اجرای واقعی:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/v1/cases/case-1405-abgin-gostar-toos/drive/sync" `
  -ContentType "application/json" `
  -Body '{"folder_id":"DRIVE_FOLDER_ID","dry_run":false}'
```

وضعیت همگام‌سازی:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/v1/cases/case-1405-abgin-gostar-toos/drive/status"
```

## مرحله ۸: استخراج و حافظه

پس از موفقیت sync، worker باید فایل‌های `manifest.json` را بخواند، متن را در `02-extracted-text` بسازد و برای هر فایل یک رکورد حافظه اول ایجاد کند. سپس رکوردهای خلاصه و پیوندها به حافظه دوم افزوده می‌شوند.

ترتیب اجرایی:

```text
Drive sync
→ document parser/OCR
→ case memory-1
→ case memory-2
→ evidence map
→ initial report
→ draft
→ citation review
```

## نکات امنیتی

- کلید Service Account در GitHub commit نشود.
- اصل فایل‌های پرونده در GitHub قرار نگیرد.
- برای هر پرونده از `case_id` مستقل استفاده شود.
- Service Account فقط Viewer باشد مگر قابلیت upload خروجی عمداً فعال شود.
- لایحه نهایی بدون تأیید انسانی تولید یا ارسال نشود.
- مسیر mirror روی دیسک رمزگذاری‌شده یا با دسترسی محدود باشد.
