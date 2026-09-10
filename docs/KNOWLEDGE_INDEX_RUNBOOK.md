# Runbook — اتصال Google Drive دانش به MousaviTax

**پوشه اصلی:** https://drive.google.com/drive/folders/1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del  
**شناسه:** `1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del`

## هدف
بایگانی رسمی + منبع RAG برای پاسخ و پیش‌نویس لایحه (با Citation و Human review).

## مسیر داده
```text
Drive 1Jx0cip…
  → knowledge/drive_mirror  یا  knowledge/official
  → scripts/seed_knowledge.py
  → data/iran_tax_vectors.json
  → POST /v1/rag/query | /v1/orchestrate
```

## روش A — دستی (پیشنهادی برای شروع)
1. از Drive چند PDF اولویت‌دار را دانلود کنید (لیست در `knowledge/drive_manifest.json`).
2. کپی در `knowledge/official/`
3. اجرا:
```bat
scripts\win-index-knowledge.bat
```

## روش B — Service Account
```powershell
$env:GOOGLE_SERVICE_ACCOUNT_JSON="D:\secrets\sa.json"
$env:GOOGLE_DRIVE_PRIMARY_FOLDER="1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del"
scripts\win-index-knowledge.ps1
```

## پس از ایندکس
1. API را با همان `VECTOR_DB_PATH` بالا بیاورید.
2. `GET /health` → `knowledge_chunks` باید > 0 باشد.
3. اگر evidence نبود → `INSUFFICIENT_DATA` (بدون citation جعلی).

## لایحه
بازیابی chunks مرتبط → پیش‌نویس با استناد → **بازبینی مشاور** قبل از استفاده رسمی.
