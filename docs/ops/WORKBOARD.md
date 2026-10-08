# MousaviTax Workboard

آخرین بروزرسانی: 2026-10-08

## فعال
### WO-2026-002 — Security & Data Integrity Hardening
مالک اجرایی: AGENT-BE-SECURITY-DATA
وضعیت: Active / P0
مرجع: Issue #3

### WO-2026-003 — Multi-Agent Governance
مالک: ARCHITECTURE/GOVERNANCE
وضعیت: Active
مرجع: Issue #9

### UI-2026-001 — Vibrant Visual Refresh
مالک اجرایی: AGENT-FE-UX
وضعیت: Active / Review
مرجع: PR #5

## قرارداد دو ایجنت هم‌زمان

| Agent | مالکیت اصلی | مجاز به تغییر | ممنوع |
|---|---|---|---|
| AGENT-BE-SECURITY-DATA | Backend/Security/Data | `apps/api/**`, `packages/shared/**`, `packages/ai-gateway/**`, `infra/**` و migrationهای مرتبط | `apps/web/**` و فایل‌های UI |
| AGENT-FE-UX | Frontend/UX | `apps/web/**` و assets/styleهای داخل web | `apps/api/**`, backend packages، migration |

### قواعد هم‌زمانی
- هر Agent branch مستقل دارد.
- هیچ فایل مشترکی بین این دو مالک نیست.
- مستندات مشترک فقط توسط ARCHITECTURE/GOVERNANCE تغییر می‌کند.
- تغییرات لازم خارج از scope باید به Work Order جدید تبدیل شود.
- هیچ Agent مجاز به merge خودکار نیست.

## Agent Map
1. ARCHITECTURE/GOVERNANCE — معماری، ADR، Workboard، repository scope
2. AGENT-BE-SECURITY-DATA — API، امنیت، RBAC، persistence، ownership، audit
3. TAXLAW-ENGINE — قوانین و محاسبات مالیاتی نسخه‌دار
4. KNOWLEDGE-RAG — منابع رسمی، ingestion، retrieval، citation/APCS
5. DOCUMENT-AI — OCR، parsing، classification و extraction
6. AGENT-FE-UX — web UI/UX، responsive، accessibility
7. CHANNELS/BOTS — Telegram/Bale و adapters؛ بدون منطق مالیاتی مستقل
8. QA/DEVOPS — تست، CI/CD، observability و release validation

Agentهای 3 تا 5 و 7 تا 8 تا زمان صدور Work Order فعال نیستند.

## چرخه کار
READ → CLAIM/WORK ORDER → BRANCH → IMPLEMENT → TEST → REPORT → REVIEW → MERGE

هیچ مرحله‌ای حذف نمی‌شود.
