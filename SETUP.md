# Setup Guide — MousaviTax AI Platform v0.2.0

> راهنمای جامع راه‌اندازی برای دو محیط: **Lovable Preview** و **Vercel Production**

این سند توضیح می‌دهد چگونه پلتفرم را در یکی از دو محیط راه‌اندازی کنید. هر دو محیط از کد واحد استفاده می‌کنند — تنها تفاوت در تنظیمات محیط‌محرمانه (environment variables) است.

---

## 📑 فهرست

- [انتخاب محیط](#انتخاب-محیط)
- [Quick Start (Demo Mode)](#quick-start-demo-mode)
- [تنظیم محیط Lovable](#تنظیم-محیط-lovable)
- [تنظیم محیط Vercel](#تنظیم-محیط-vercel)
- [تنظیم Google Drive](#تنظیم-google-drive)
- [تنظیم Supabase](#تنظیم-supabase)
- [تنظیم LLM Provider](#تنظیم-llm-provider)
- [عیب‌یابی (Troubleshooting)](#عیب-یابی-troubleshooting)
- [تغییر محیط بین Lovable و Vercel](#تغییر-محیط-بین-lovable-و-vercel)

---

## انتخاب محیط

| معیار | Lovable | Vercel |
|-------|--------|--------|
| سرعت توسعه | ⚡ عالی (ویرایشگر بصری) | 🐢 نیاز به commit/push |
| کنترل کد | 🟡 محدود | 🟢 کامل |
| پشتیبانی Drive | ✅ داخلی (connector) | ⚠️ نیاز به Service Account |
| کنترل CI/CD | ❌ ندارد | ✅ GitHub Actions |
| Multi-tenant | ⚠️ محدود | ✅ کامل |
| RBAC + Audit | ⚠️ نشده | ✅ کامل |
| قیمت (Tyer free) | ✅ رایگان | ✅ رایگان (Hobby) |

**پیشنهاد**: برای توسعه از Lovable استفاده کنید، برای production به Vercel منتقل کنید.

---

## Quick Start (Demo Mode)

این ساده‌ترین راه برای شروع است — بدون هیچ تنظیماتی، پلتفرم با نمونه‌ی قوانین مالیاتی اجرا می‌شود.

### پیش‌نیازها
- Node.js 20+
- Python 3.12+

### مراحل

```bash
# 1. کلون repo
git clone https://github.com/ziyamka2026-art/mousavitax-platform.git
cd mousavitax-platform

# 2. کپی env template
cp .env.example .env.local
# (تنظیمات پیش‌فرض به Demo Mode می‌رود)

# 3. نصب وابستگی‌ها
cd apps/web && npm install && cd ../..
pip install -r apps/api/requirements.txt

# 4. اجرا
cd apps/api && uvicorn app.main:app --port 8000 &
cd apps/web && npm run dev
```

### تأیید
- Frontend: <http://localhost:3001>
- Backend: <http://localhost:8000/health>

**نمونه‌ی قوانین مالیاتی نشان داده می‌شود**:
- قانون مالیات‌های مستقیم
- قانون مالیات بر ارزش افزوده
- بخشنامه‌های نمونه
- آیین‌نامه اجرایی ماده ۲۱۹
- آرای دیوان عدالت اداری

---

## تنظیم محیط Lovable

### ۱. ساخت پروژه در Lovable

1. به <https://lovable.dev> بروید
2. روی **New Project** کلیک کنید
3. نوع **Remix** را انتخاب
4. فایل ZIP پروژه را آپلود کنید (یا GitHub repo را وصل کنید)

### ۲. اتصال Google Drive

1. در Lovable Editor، به **Settings → Integrations** بروید
2. روی **Connect Google Drive** کلیک
3. حساب Google خود را مجوز دهید
4. folder ID مرجع را تنظیم کنید:
   - متغیر `TAXLAW_GROK_MASTER_FOLDER_ID` را در Lovable env vars اضافه کنید
   - مقدار: `1M7rsSpQf0akKKmV2P6o66A-uj8KF3cJW` (یا folder ID خودتان)

### ۳. تنظیم متغیرهای محیطی در Lovable

در Lovable Editor → **Settings → Environment Variables**:

| متغیر | مقدار | الزامی |
|--------|-------|--------|
| `TAXLAW_GROK_MASTER_FOLDER_ID` | Drive folder ID | ✅ |
| `LOVABLE_API_KEY` | خودکار توسط Lovable | ✅ (auto) |
| `GOOGLE_DRIVE_API_KEY` | از Lovable integrations | ✅ |
| `LLM_PROVIDER` | `openai` یا `gemini` | ✅ |
| `OPENAI_API_KEY` | اگر openai انتخاب شد | ⚠️ |
| `GOOGLE_API_KEY` | اگر gemini انتخاب شد | ⚠️ |
| `SUPABASE_URL` | URL API Supabase | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | service role key | ✅ |

### ۴. Deploy

Lovable خودکار deploy می‌کند. preview URL از این شکل:
```
https://preview--<project-name>.lovable.app/
```

### ۵. تأیید

به `/api/health` بروید (در آدرس پیش‌نمایش):
```
https://preview--<project-name>.lovable.app/api/health
```

باید JSON برگرداند با:
```json
{
  "status": "ok",
  "demo_mode": false,
  "modules_count": 7,
  ...
}
```

---

## تنظیم محیط Vercel

### ۱. Fork repo در GitHub

```bash
# اگر هنوز fork نکرده‌اید:
gh repo fork ziyamka2026-art/mousavitax-platform
```

### ۲. Import به Vercel

1. به <https://vercel.com> بروید
2. روی **Add New Project** کلیک
3. repo `mousavitax-platform` را انتخاب
4. تنظیمات:
   - Framework Preset: **Next.js**
   - Root Directory: `apps/web`
   - Build Command: `cd ../.. && npm install && npm run build`
   - Output Directory: `apps/web/.next`

### ۳. تنظیم متغیرهای محیطی در Vercel

در **Vercel → Settings → Environment Variables**:

| متغیر | محیط | مقدار |
|--------|------|-------|
| `SUPABASE_URL` | Production | `https://<project-ref>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_URL` | Production | همان |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Production | anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Production | service role |
| `LLM_PROVIDER` | Production | `openai` یا `gemini` |
| `OPENAI_API_KEY` | Production | OpenAI key |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Production | JSON کامل |
| `TAXLAW_GROK_MASTER_FOLDER_ID` | Production | Drive folder ID |
| `NEXT_PUBLIC_APP_URL` | Production | `https://<your-domain>.vercel.app` |
| `SENTRY_DSN` | Production | اختیاری |

### ۴. Deploy

Vercel خودکار deploy می‌کند. URL از این شکل:
```
https://<project-name>.vercel.app/
```

### ۵. راه‌اندازی Backend (FastAPI)

Vercel فقط Next.js را deploy می‌کند. برای backend:

#### راه A: Railway (پیشنهادی)

1. به <https://railway.app> بروید
2. **New Project → Deploy from GitHub**
3. repo `mousavitax-platform` را انتخاب
4. تنظیم:
   - Source Directory: `apps/api`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. متغیرها را همان Vercel تنظیم کنید (به‌جز `NEXT_PUBLIC_*`)

#### راه B: Fly.io

```bash
cd apps/api
flyctl launch
flyctl deploy
```

### ۶. اتصال Vercel به Backend

در فایل `vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/v1/(.*)",
      "destination": "https://<your-railway-app>.railway.app/v1/$1"
    }
  ]
}
```

### ۷. تأیید

به `/api/health` بروید:
```
https://<project-name>.vercel.app/api/health
```

---

## تنظیم Google Drive

### ۱. ساخت Service Account (برای Vercel)

1. به <https://console.cloud.google.com> بروید
2. پروژه را انتخاب یا بسازید
3. **APIs & Services → Library** → فعال کنید:
   - Google Drive API
4. **APIs & Services → Credentials**
5. **Create Credentials → Service Account**
6. نام: `mousavitax-bridge`
7. نقش:なし (نیازی نیست)
8. پس از ساخت، روی Service Account کلیک
9. تب **Keys → Add Key → JSON**
10. فایل JSON را دانلود کنید
11. محتوای JSON را در `GOOGLE_SERVICE_ACCOUNT_JSON` کپی کنید

### ۲. اشتراک‌گذاری Drive Folder با Service Account

1. در Google Drive، folder مرجع را باز کنید
2. روی folder راست‌کلیک → **Share**
3. ایمیل Service Account را اضافه کنید (از فایل JSON)
4. نقش: **Editor**
5. folder ID را از URL بردارید:
   ```
   https://drive.google.com/drive/folders/<FOLDER_ID>
   ```
6. `FOLDER_ID` را در `TAXLAW_GROK_MASTER_FOLDER_ID` قرار دهید

### ۳. ساختار پوشه‌ها

در Drive folder اصلی، ۷ زیرپوشه با این نام‌ها بسازید:
- `LAYEHA_APPEAL_WORKFLOW_V`
- `TAXLAW_GROK_Paged_Queue_Dashboard`
- `setupCaseIndex`
- `intake_calculator`
- `summarizer`
- `TAXLAW-GROK-MASTER-CONTROL`
- `law_library`

---

## تنظیم Supabase

### ۱. ساخت پروژه Supabase

1. به <https://supabase.com> بروید
2. **New Project**
3. نام: `mousavitax`
4. منطقه: **EU Central** (نزدیک‌ترین به ایران)
5. Password را قوی انتخاب و ذخیره کنید

### ۲. فعال‌سازی اکستنشن‌ها

در Supabase SQL Editor:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

### ۳. اجرای migrations

به ترتیب این فایل‌ها را در SQL Editor اجرا کنید:

```bash
for f in infra/postgres/migrations/001_tenants.sql \
         infra/postgres/migrations/002_audit_logs.sql \
         infra/postgres/migrations/003_knowledge_documents.sql \
         infra/postgres/migrations/004_add_tenant_rls.sql; do
  echo "Running $f..."
done
```

یا با psql:
```bash
psql "$DATABASE_URL" -f infra/postgres/migrations/001_tenants.sql
psql "$DATABASE_URL" -f infra/postgres/migrations/002_audit_logs.sql
psql "$DATABASE_URL" -f infra/postgres/migrations/003_knowledge_documents.sql
psql "$DATABASE_URL" -f infra/postgres/migrations/004_add_tenant_rls.sql
```

### ۴. گرفتن API credentials

در Supabase Dashboard:
- **Project Settings → API**
- مقادیر زیر را کپی کنید:
  - Project URL (نه Dashboard URL!)
  - anon public key
  - service_role key

⚠️ **مهم**: URL باید مثل `https://<project-ref>.supabase.co` باشد، نه `https://supabase.com/dashboard/project/...`

---

## تنظیم LLM Provider

### گزینه ۱: OpenAI (پیشنهادی برای production)

1. به <https://platform.openai.com/api-keys> بروید
2. **Create new secret key**
3. در env:
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4o-mini
   ```

### گزینه ۲: Google Gemini

1. به <https://aistudio.google.com/apikey> بروید
2. **Create API key**
3. در env:
   ```
   LLM_PROVIDER=gemini
   GOOGLE_API_KEY=AIza...
   GEMINI_MODEL=gemini-2.0-flash-lite
   ```

### گزینه ۳: Ollama (تنها برای توسعه‌ی محلی)

```bash
# نصب Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull مدل
ollama pull qwen2.5:7b

# در env:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_MODEL=qwen2.5:7b
```

⚠️ **هشدار**: در production، LLM_PROVIDER=ollama قابل اجرا نیست. در pipeline Stage 2 (Fiqh) این تأیید می‌شود.

---

## عیب‌یابی (Troubleshooting)

### مشکل: «۰ فایل» در صفحه‌ی Law Library

**علت**: Drive credentials تنظیم نشده یا URL اشتباه است.

**راه‌حل**:

1. به `/api/health` بروید
2. بخش `credentials` را بررسی کنید — کدام متغیرها `is_set: false` هستند
3. در محیط خود (Lovable یا Vercel) مقادیر را تنظیم کنید

اگر گزینه‌ی Demo Mode را ترجیح می‌دهید:
```
SOURCE_BRIDGE_DEMO_MODE=true
```

### مشکل: خطای `Missing env var: SUPABASE_URL`

**علت**: `SUPABASE_URL` تنظیم نشده یا URL اشتباه است.

**کنترل**: باید `https://<ref>.supabase.co` باشد، نه dashboard URL.

### مشکل: Drive scan هنگ می‌کند

**علت**: احتمالاً rate-limit یا permission.

**کنترل**:
1. مطمئن شوید Service Account به folder اشتراک‌گذاری شده
2. Drive API فعال است
3. از `/api/health` وضعیت را بررسی کنید

### مشکل: Pipeline در مرحله ۶ fail می‌کند

**علت**: یکی از Oath Guards نقض شده.

معمول‌ترین علل:
- `require_citations`: هیچ citation در خروجی نیست (retriever خالی برگردانده)
- `law_over_circular`: بخشنامه بدون استناد به قانون
- `require_human_review`: AI تلاش کرده status=FINAL تنظیم کند

**راه‌حل**: لاگ خطا را بررسی کنید — نام guard صریحاً ذکر می‌شود.

---

## تغییر محیط بین Lovable و Vercel

### از Lovable به Vercel

1. در Lovable، پروژه را به GitHub export کنید (یا به repo خودتان push)
2. در Vercel، repo را import کنید
3. متغیرهای Lovable را در Vercel کپی کنید (با افزودن `GOOGLE_SERVICE_ACCOUNT_JSON` به‌جای `GOOGLE_DRIVE_API_KEY`)
4. Backend را روی Railway deploy کنید
5. در Vercel `vercel.json` را برای proxy API تنظیم کنید

### از Vercel به Lovable

1. در Lovable Editor، کد را با copy-paste یا git pull وارد کنید
2. متغیرهای Vercel را در Lovable تنظیم کنید (با حذف `GOOGLE_SERVICE_ACCOUNT_JSON`)
3. `LOVABLE_API_KEY` خودکار set می‌شود
4. Lovable خودکار deploy می‌کند

---

## چک‌لیست نهایی

| مورد | Lovable | Vercel |
|------|---------|--------|
| Demo mode کار می‌کند | ✅ | ✅ |
| Drive متصل | ⚠️ | ✅ |
| Supabase متصل | ✅ | ✅ |
| LLM تنظیم | ✅ | ✅ |
| Backend FastAPI | ❌ (Lovable server functions) | ✅ Railway |
| RBAC فعال | ⚠️ | ✅ |
| Audit Log | ⚠️ | ✅ |
| ۶ Stage Pipeline | ⚠️ (subset) | ✅ |
| ۷ Fiqh Rules | ✅ | ✅ |
| ۶ Oath Guards | ✅ | ✅ |

---

## تماس

اگر با مشکل مواجه شدید:

1. به `/api/health` نگاه کنید — diagnostic کامل
2. لاگ‌های Vercel/Railway را بررسی کنید
3. در GitHub Issues گزارش دهید: <https://github.com/ziyamka2026-art/mousavitax-platform/issues>

ایمیل: `ziya.mka2026@gmail.com`
