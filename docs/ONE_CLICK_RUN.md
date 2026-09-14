# اجرای سریع MousaviTax

## روش پیشنهادی: GitHub Codespaces

1. مخزن را باز کنید.
2. از **Code → Codespaces → Create codespace** استفاده کنید.
3. برای تست اصلاحات، branch زیر را انتخاب کنید:
   `wo/2026-002-security-hardening`
4. Codespace با `.devcontainer/devcontainer.json` وابستگی‌های Python و Web را نصب می‌کند.
5. پس از شروع، API روی پورت `8000` و Web روی پورت `3000` اجرا می‌شوند.
6. در تب **Ports** روی Web بازشده کلیک کنید.

## اجرای دستی داخل Codespace

```bash
bash scripts/run_dev.sh
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Web:

```text
http://localhost:3000
```

## تست

```bash
cd apps/api
PYTHONPATH=app:../../packages/shared:../../packages/ai-gateway/app:../../packages/taxlaw-engine:../../packages/prompt-engine:../../packages/knowledge-core:../../packages/embedding-service/app:../../packages/retrieval-engine/app:../../packages/document-parser pytest -q
```

Web build:

```bash
cd apps/web
npm ci
npx tsc --noEmit
npm run build
```

## دانش مالیاتی

در صورت داشتن فایل‌های دانش محلی، ابتدا در صورت نیاز sync و سپس seed را اجرا کنید:

```bash
python scripts/sync_drive_knowledge.py
python scripts/seed_knowledge.py
```

## هشدار

این محیط برای توسعه و تست است. تا تکمیل WO-2026-002، از واردکردن اطلاعات واقعی و حساس مودیان در محیط آزمایشی خودداری کنید.
