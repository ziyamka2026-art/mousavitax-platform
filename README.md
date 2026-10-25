# 🇮🇷 MousaviTax AI Platform (MKA / ARYA Holding)

**AI-Native Tax Platform** برای ایران — نه فقط چت‌بات، نه کپی Marketplace.

> Hybrid: **AI Triage → RAG/APCS + Citation → Human-in-the-loop** · **Tax Case** · **Service Catalog** · مشاوران سراسری

⚠️ **هشدار مهم**: این پلتفرم جایگزین مشاور رسمی نیست. اطلاعات این سامانه صرفاً جنبه‌ی راهنمایی دارد و مسئولیت حقوقی نهایی بر عهده‌ی کاربر است.

---

## 📑 فهرست مطالب

- [نمای کلی](#نمای-کلی)
- [ویژگی‌های کلیدی](#ویژگی‌های-کلیدی)
- [معماری](#معماری)
- [Quick Start (۵ دقیقه)](#quick-start-۵-دقیقه)
- [ساختار پروژه](#ساختار-پروژه)
- [تنظیم محیط توسعه](#تنظیم-محیط-توسعه)
- [استقرار (Deployment)](#استقرار-deployment)
- [تست و کیفیت](#تست-و-کیفیت)
- [مشارکت](#مشارکت)
- [امنیت](#امنیت)
- [اسناد کلیدی](#اسناد-کلیدی)
- [مجوز](#مجوز)
- [تماس](#تماس)

---

## نمای کلی

MousaviTax یک پلتفرم هوش مصنوعی مالیاتی بومی‌سازی‌شده برای ایران است که بر پایه‌ی سه اصل بنا شده:

1. **AI-Native** — AI موتور اصلی است، نه افزونه. تمام جریان کار از Triage هوشمند شروع می‌شود.
2. **Human-in-the-loop** — تصمیمات حساس (اعتراض، لایحه، ارزش افزوده) به مشاور رسمی ارجاع می‌شود.
3. **Tax Case-centric** — واحد کار اصلی «پرونده‌ی مالیاتی الکترونیکی» است، نه سؤال و جواب منفرد.

### مدل درآمدی

| لایه | توضیح |
|------|------|
| Freemium | سؤال سریع + RAG پایه |
| AI Premium | ابزارهای پیشرفته + تحلیل ریسک |
| AI + Expert | همراه با دسترسی به مشاور |
| Case کامل | پرونده‌ی کامل با workflow |

---

## ویژگی‌های کلیدی

- ✅ **Tax Case Management** — پرونده‌ی الکترونیکی با تاریخچه‌ی کامل
- ✅ **Service Catalog (S01-S13)** — ۱۳ خدمت تخصصی مالیاتی
- ✅ **Hybrid AI Triage** — مسیریابی هوشمند سؤال به RAG/Expert/Workflow
- ✅ **RAG با Citation** — هر پاسخ به منبع رسمی ارجاع می‌دهد
- ✅ **APCS Quality Gate** — دروازه‌ی کنترل کیفیت پیش از نمایش پاسخ
- ✅ **Multi-channel** — Web, Telegram Bot, Bale Bot, Admin
- ✅ **Multi-tenant RBAC** — تفکیک داده بین سازمان‌ها
- ✅ **Append-only Audit Log** — ردپای کامل همه‌ی اقدامات حساس
- ✅ **Knowledge Approval Workflow** — چرخه‌ی تأیید محتوا پیش از ایندکس
- 🚧 Expert Marketplace — در حال توسعه (P0)
- 🚧 داشبورد مودی/مشاور/ادمین — در حال توسعه (P0)
- 🚧 Tax Calendar — در حال توسعه (P0)

---

## معماری

```text
┌──────────────────────────────────────────────────────────────┐
│                       کانال‌های ورودی                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │   Web   │  │Telegram │  │  Bale   │  │  Admin  │         │
│  │ Next.js │  │  Bot    │  │  Bot    │  │  Panel  │         │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│       └──────────┬──┴────────────┴────────────┘              │
│                  ▼                                            │
│         ┌────────────────────┐                                │
│         │  API Gateway (FastAPI)  │ ◄── RBAC + Audit Log      │
│         └──────────┬─────────┘                                │
│                    ▼                                          │
│   ┌────────────────────────────────────────────┐              │
│   │   AI Triage → RAG/APCS → Citation → Expert │              │
│   └────────────┬───────────────────────────────┘              │
│                ▼                                              │
│   ┌──────────────────┐  ┌──────────────────┐                 │
│   │  LLM Gateway      │  │  Vector DB       │                 │
│   │  (Ollama/OpenAI/  │  │  (Qdrant /       │                 │
│   │   Gemini)         │  │   pgvector)      │                 │
│   └──────────────────┘  └──────────────────┘                 │
│                ▼                                              │
│   ┌──────────────────────────────────────────┐               │
│   │  Knowledge Store (Supabase Postgres)     │               │
│   │  - knowledge_documents (with approval)   │               │
│   │  - tax_cases, audit_logs, tenants        │               │
│   └──────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

### اصول معماری

- **ADR-007**: Hybrid AI Tax Platform — تصمیم پایه‌گذار
- **Domain-Driven Design** — `domains/iran-tax/` محل زنده‌ی دامنه‌ی کاری
- **Monorepo** — کد اشتراکی در `packages/`، کانال‌های مجزا در `apps/`
- **API-First** — تمام جریان‌ها از طریق REST API با JSON Schema
- **Stateless Backend** — FastAPI بدون state، قابل scale افقی
- **Defense in Depth** — RBAC + Audit + RLS + IP allowlist

---

## Quick Start (۵ دقیقه)

### پیش‌نیازها

| ابزار | حداقل نسخه |
|------|-----------|
| Node.js | 20.x |
| Python | 3.12+ |
| Bun | 1.x (برای mka-core) |
| PostgreSQL | 16+ (یا Supabase) |
| Ollama (اختیاری) | آخرین نسخه — برای توسعه‌ی محلی LLM |

### ۱. کلون و نصب

```bash
git clone https://github.com/ziyamka2026-art/mousavitax-platform.git
cd mousavitax-platform

# کپی فایل env و پر کردن مقادیر
cp .env.example .env.local
# حالا .env.local را ویرایش کنید و مقادیر واقعی را وارد کنید
```

### ۲. نصب وابستگی‌ها

```bash
# Frontend (Next.js web)
cd apps/web && npm install && cd ../..

# MKA-Core (Bun)
cd apps/mka-core && bun install && cd ../..

# Backend (FastAPI)
pip install -r apps/api/requirements.txt
```

### ۳. اجرای سرویس‌ها

در ۳ ترمینال جداگانه:

```bash
# ترمینال ۱ — Backend API
cd apps/api
uvicorn app.main:app --reload --port 8000

# ترمینال ۲ — Frontend Web
cd apps/web
npm run dev

# ترمینال ۳ — MKA-Core (اختیاری)
cd apps/mka-core
bun dev
```

### ۴. اعتبارسنجی

- Backend: <http://localhost:8000/health>
- Frontend: <http://localhost:3001>
- MKA-Core: <http://localhost:3000>

---

## ساختار پروژه

```text
mousavitax-platform/
├── apps/                       # کانال‌های ورودی
│   ├── api/                    # FastAPI backend
│   ├── web/                    # Next.js 16 frontend
│   ├── mka-core/              # Knowledge brain (Bun)
│   ├── telegram-bot/          # Telegram bot
│   ├── bale-bot/              # Bale bot
│   └── admin/                 # Admin panel
├── packages/                  # پکیج‌های اشتراکی
│   ├── auth/                  # RBAC + session
│   ├── audit/                 # Audit logging
│   ├── observability/         # Tracing + metrics
│   ├── prompt-engine/         # Prompt construction
│   ├── knowledge-core/        # Knowledge mgmt
│   ├── taxlaw-engine/         # Iranian tax law engine
│   ├── retrieval-engine/      # RAG retrieval
│   ├── embedding-service/     # Embedding abstraction
│   ├── ai-gateway/            # LLM routing
│   ├── document-parser/       # PDF/DOCX parsing
│   ├── office-agent/          # Office integration
│   └── shared/                # Common utilities
├── services/                  # سرویس‌های مستقل
│   ├── rag/                   # Vector store implementations
│   ├── crawler/               # Web crawler
│   └── source-bridge/         # Google Drive bridge
├── domains/                   # Domain-specific logic
│   └── iran-tax/              # Iranian tax rules + prompts
├── infra/                     # Infrastructure
│   └── postgres/             # SQL migrations
│       └── migrations/
│           ├── 001_tenants.sql
│           ├── 002_audit_logs.sql
│           └── 003_knowledge_documents.sql
├── knowledge/                 # Raw knowledge sources
│   └── official/              # Official documents
├── templates/                 # Document templates
│   └── contracts/             # Contract templates
├── tests/                     # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/                   # Operational scripts
├── docs/                      # Documentation
│   ├── adr/                   # Architecture Decision Records
│   ├── ops/                   # Persian ops guides
│   └── phase3/
└── data/                      # Local data (gitignored)
```

---

## تنظیم محیط توسعه

### متغیرهای محیطی

| متغیر | توضیح | الزامی؟ |
|--------|------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | URL API Supabase (نه داشبورد!) | ✅ |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | کلید عمومی Supabase | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | کلید سرویس Supabase (server only) | ✅ |
| `LLM_PROVIDER` | ollama \| openai \| gemini | ✅ |
| `API_SECRET_KEY` | حداقل ۳۲ کاراکتر تصادفی | ✅ |
| `TELEGRAM_BOT_TOKEN` | توکن ربات تلگرام | در صورت استفاده |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | اعتبار Google Drive | در صورت استفاده |
| `QDRANT_URL` | آدرس Qdrant | برای تولید |
| `SENTRY_DSN` | DSN خطایابی Sentry | اختیاری |

详见 `.env.example` برای فهرست کامل.

### اجرای مایگریشن‌های دیتابیس

```bash
# با psql
for f in infra/postgres/migrations/*.sql; do
  psql "$DATABASE_URL" -f "$f"
done

# یا با Supabase CLI
supabase db push
```

---

## استقرار (Deployment)

### Frontend (Next.js) → Vercel

1. پروژه را در Vercel متصل کنید (`apps/web` به‌عنوان Root Directory)
2. متغیرهای محیط را در Vercel Environment Variables قرار دهید (هرگز در `.env.local`)
3. `vercel.json` در root پروژه تنظیمات build را مدیریت می‌کند

### Backend (FastAPI) → Railway / Fly.io / Render

```bash
# Dockerfile در apps/api/ موجود است
cd apps/api
docker build -t mousavitax-api .
docker run -p 8000:8000 --env-file .env.local mousavitax-api
```

### Database → Supabase

1. پروژه‌ی Supabase را ایجاد کنید
2. SQL Editor را باز کنید
3. مایگریشن‌های `infra/postgres/migrations/` را به ترتیب اجرا کنید
4. اکستنشن‌های `vector` و `pgcrypto` را فعال کنید

---

## تست و کیفیت

### اجرای تست‌ها

```bash
# Python unit tests
pytest tests/unit -v --cov=apps/api

# TypeScript unit tests
npx vitest run

# Integration tests (نیاز به سرویس‌های واقعی)
pytest tests/integration --run-integration

# E2E tests
npx playwright test

# Lint
ruff check apps/api packages services
npx eslint apps/web --ext .ts,.tsx
```

### پوشش مورد انتظار

| لایه | حداقل پوشش |
|------|-----------|
| Unit | ۸۰% |
| Integration | flows اصلی کاربر |
| E2E | Login, Create Case, Submit Service Request |
| Load | ۱۰۰ کاربر هم‌زمان |
| Security | هر PR اسکن شود |

CI به‌صورت خودکار همه‌ی این موارد را در هر PR اجرا می‌کند (`.github/workflows/ci.yml`).

---

## مشارکت

برای راهنمایی کامل به [CONTRIBUTING.md](CONTRIBUTING.md) مراجعه کنید. خلاصه:

1. Issue بسازید یا در Issue‌ی موجود نظر بدهید
2. Fork کنید و شاخه‌ی feature بسازید (`feat/...` یا `fix/...`)
3. Change‌های خود را commit کنید (پیروی از [Conventional Commits](https://www.conventionalcommits.org/))
4. PR باز کنید با توضیح کامل
5. CI سبز باید باشد
6. حداقل یک reviewer تأیید کند

### استانداردهای کد

- **TypeScript**: ESLint + Prettier، strict mode
- **Python**: Ruff + Black، type hints اجباری
- **Tests**: همراه با کد، حداقل one happy-path + one edge case
- **Commit message**: `feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:`

---

## امنیت

### گزارش آسیب‌پذیری

اگر آسیب‌پذیری امنیتی کشف کردید، لطفاً به‌صورت خصوصی به `ziya.mka2026@gmail.com` ایمیل بزنید و نه issue عمومی. در طول ۴۸ ساعت پاسخواهی دریافت خواهید کرد.

برای جزئیات: [SECURITY.md](SECURITY.md)

### اصول امنیتی

- 🔒 هرگز `.env.local` را commit نکنید (`.gitignore` فعال است)
- 🔒 هرگز service role key را در کد کلاینت استفاده نکنید
- 🔒 هرگز `NEXT_PUBLIC_` را به کلیدهای سرور اضافه نکنید
- 🔒 RBAC در هر endpoint از طریق `withAuth()` اعمال می‌شود
- 🔒 Audit log فقط با INSERT کار می‌کند (RLS در سطح دیتابیس)
- 🔒 Knowledge docs قبل از ایندکس باید `approved` شوند

---

## اسناد کلیدی

| سند | موضوع |
|-----|------|
| [docs/09_NAMA_BENCHMARK_AND_PRODUCT.md](docs/09_NAMA_BENCHMARK_AND_PRODUCT.md) | Benchmark نما + جهت محصول |
| [docs/10_SERVICE_CATALOG.md](docs/10_SERVICE_CATALOG.md) | کاتالوگ خدمات |
| [docs/11_TAX_CASE.md](docs/11_TAX_CASE.md) | پرونده الکترونیکی |
| [docs/12_BACKLOG.md](docs/12_BACKLOG.md) | P0 / P1 / P2 |
| [docs/adr/ADR-007-Hybrid-AI-Tax-Platform.md](docs/adr/ADR-007-Hybrid-AI-Tax-Platform.md) | تصمیم معماری |
| [docs/ops/](docs/ops/) | دستورالعمل فارسی ماژول‌ها |
| [CONTRIBUTING.md](CONTRIBUTING.md) | راهنمای مشارکت |
| [SECURITY.md](SECURITY.md) | سیاست امنیتی |
| [LICENSE](LICENSE) | مجوز استفاده |

---

## مجوز

© 2026 MousaviTax / ARYA Holding. تمام حقوق محفوظ است.

استفاده‌ی تجاری نیاز به مجوز کتبی دارد. برای جزئیات به [LICENSE](LICENSE) مراجعه کنید.

---

## تماس

| نوع | مقدار |
|------|-------|
| ایمیل | `ziya.mka2026@gmail.com` |
| Issues | [GitHub Issues](https://github.com/ziyamka2026-art/mousavitax-platform/issues) |
| Discord | به‌زودی |

⚠️ **سلب مسئولیت حقوقی**: این پلتفرم جایگزین مشاور رسمی نیست.
