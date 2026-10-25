# راهنمای PostgreSQL، API و تست ورک‌فلو مالیاتی

## ۱. وضعیت فعلی

ماشین‌حالت فعلی در `packages/agent-core/legal_workflow.py` برای نمونه‌سازی، وضعیت Workflow را در حافظه نگهداری می‌کند:

```python
self._workflows: dict[str, CaseWorkflow] = {}
```

بنابراین با Restart شدن API، Workflowها و رویدادهای حسابرسی از بین می‌روند. برای محیط عملیاتی باید **داده‌های پرونده، وضعیت ورک‌فلو، دروازه‌های باز، خروجی ایجنت‌ها و رویدادهای حسابرسی** در PostgreSQL ذخیره شوند.

---

## ۲. معماری پیشنهادی

```text
Client / Admin UI
       |
       v
FastAPI Agent Routes
       |
       +--> WorkflowService
       |       +--> WorkflowRepository (PostgreSQL)
       |       +--> AuditRepository (PostgreSQL)
       |       +--> Agent adapters (Drive, OCR, MKA-Core, Law Library)
       |
       v
PostgreSQL
  - tax_cases
  - legal_workflows
  - workflow_events
  - workflow_artifacts
  - workflow_gates
```

### اصل مهم

ایجنت‌ها نباید مستقیماً به دیتابیس خام دسترسی داشته باشند. مسیر صحیح:

```text
Agent -> Service Tool -> Authorization + Case Ownership -> Repository -> PostgreSQL
```

تمام تغییر وضعیت‌ها باید در یک تراکنش ثبت شوند:

1. قفل کردن رکورد Workflow؛
2. بررسی مالک پرونده و نسخه رکورد؛
3. بررسی معتبر بودن انتقال وضعیت؛
4. ذخیره وضعیت جدید؛
5. ثبت رویداد حسابرسی؛
6. commit.

---

## ۳. Schema پیشنهادی PostgreSQL

> این schema نمونه است؛ پیش از اجرای production باید با مدل فعلی پرونده و سیاست نگهداری داده سازمان تطبیق داده شود.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE tax_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_case_id text NOT NULL UNIQUE,
  owner_id text NOT NULL,
  taxpayer_ref text NOT NULL,
  status text NOT NULL DEFAULT 'OPEN',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE legal_workflows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES tax_cases(id),
  owner_id text NOT NULL,
  status text NOT NULL,
  current_stage text NOT NULL,
  version integer NOT NULL DEFAULT 1,
  data jsonb NOT NULL DEFAULT '{}'::jsonb,
  pending_gates jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (case_id)
);

CREATE TABLE workflow_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  workflow_id uuid NOT NULL REFERENCES legal_workflows(id),
  event_type text NOT NULL,
  actor_id text,
  agent_id text NOT NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES legal_workflows(id),
  artifact_type text NOT NULL,
  storage_uri text,
  content_hash text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_gates (
  workflow_id uuid NOT NULL REFERENCES legal_workflows(id),
  gate_type text NOT NULL,
  state text NOT NULL DEFAULT 'OPEN',
  resolved_by text,
  resolution_note text,
  resolved_at timestamptz,
  PRIMARY KEY (workflow_id, gate_type)
);

CREATE INDEX workflow_events_workflow_time_idx
  ON workflow_events(workflow_id, created_at);
CREATE INDEX workflow_artifacts_workflow_type_idx
  ON workflow_artifacts(workflow_id, artifact_type);
```

### چرا `data` از نوع JSONB است؟

اطلاعات میان ایجنت‌ها در مراحل مختلف شکل یکسانی ندارد؛ برای نمونه `timeline`، `issue_matrix`، `penalty_matrix` و `quality_report` ساختارهای متفاوتی دارند. استفاده از JSONB برای payload مرحله مناسب است، اما فیلدهای حساس و قابل گزارش مانند `status`، `owner_id`، `version` و `current_stage` باید ستون مستقل داشته باشند.

---

## ۴. Repository و تراکنش انتقال وضعیت

نمونه ساده با SQLAlchemy Async:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class WorkflowRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_update(self, workflow_id: str):
        result = await self.session.execute(
            select(LegalWorkflow)
            .where(LegalWorkflow.id == workflow_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def save_transition(
        self, workflow, *, expected_version: int, actor_id: str,
        event_type: str, agent_id: str, details: dict
    ):
        if workflow.version != expected_version:
            raise ConflictError("نسخه پرونده تغییر کرده است؛ وضعیت را دوباره بخوانید")
        workflow.version += 1
        workflow.updated_at = utcnow()
        self.session.add(WorkflowEvent(
            workflow_id=workflow.id,
            event_type=event_type,
            actor_id=actor_id,
            agent_id=agent_id,
            details=details,
        ))
        await self.session.commit()
        await self.session.refresh(workflow)
        return workflow
```

در عملیات واقعی، متدهای `start`، `record_intake`، `submit_research`، `submit_draft`، `approve` و `deliver` باید به جای تغییر `self._workflows`، از این Repository استفاده کنند.

### کنترل هم‌زمانی

در API برای هر Workflow مقدار `version` برگردانده می‌شود. کلاینت باید آخرین نسخه را ارسال کند یا Repository با `SELECT ... FOR UPDATE` از انتقال هم‌زمان و overwrite شدن تصمیم ناظر جلوگیری کند.

---

## ۵. اتصال FastAPI

الگوی پیشنهادی:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/legal-workflow/{workflow_id}/approve")
async def approve_workflow(
    workflow_id: str,
    body: ApprovalIn,
    session: AsyncSession = Depends(get_db_session),
):
    service = WorkflowService(WorkflowRepository(session), AuditRepository(session))
    workflow = await service.approve(
        workflow_id=workflow_id,
        supervisor_id=body.supervisor_id,
        decision=body.decision,
        note=body.note,
    )
    return workflow.public_view()
```

در production، `supervisor_id` نباید صرفاً از body پذیرفته شود؛ باید از توکن احراز هویت و RBAC استخراج شود. مقدار body فقط برای نمونه API فعلی است.

### تنظیم اتصال

```env
DATABASE_URL=postgresql+asyncpg://mousavitax:CHANGE_ME@postgres:5432/mousavitax
WORKFLOW_EVENT_RETENTION_DAYS=2555
```

پیشنهاد می‌شود Secret در Secret Manager یا محیط deploy نگهداری شود و داخل Git قرار نگیرد.

---

## ۶. APIهای موجود

Base URL نمونه:

```text
http://localhost:8000
```

### ۶.۱ شروع Workflow

```bash
curl -X POST http://localhost:8000/agents/legal-workflow/start \
  -H 'Content-Type: application/json' \
  -d '{
    "case_id": "CASE-1402-0001",
    "owner_id": "supervisor-1",
    "request": "اعتراض به برگ تشخیص مالیات عملکرد سال ۱۴۰۲",
    "documents": [
      {"name": "برگ-تشخیص.pdf", "uri": "drive://case/assessment.pdf", "sha256": "..."}
    ]
  }'
```

خروجی شامل `workflow_id`، وضعیت اولیه `INTAKE`، مرحله جاری و رویداد شروع است. مقدار `workflow_id` را برای درخواست‌های بعدی نگه دارید.

### ۶.۲ ثبت Intake

```bash
curl -X POST http://localhost:8000/agents/legal-workflow/{WORKFLOW_ID}/intake \
  -H 'Content-Type: application/json' \
  -d '{
    "actor_id": "supervisor-1",
    "facts": {"tax_year": 1402, "assessment_number": "A-237"},
    "missing_fields": ["مرحله رسیدگی", "تاریخ ابلاغ"],
    "scope": {"taxpayer_ref": "TP-REDACTED", "property_count": 1}
  }'
```

اگر `missing_fields` خالی نباشد، وضعیت `NEEDS_CLARIFICATION` و دروازه `CLARIFICATION` ایجاد می‌شود.

### ۶.۳ رفع ابهام

```bash
curl -X POST http://localhost:8000/agents/legal-workflow/{WORKFLOW_ID}/clarification \
  -H 'Content-Type: application/json' \
  -d '{
    "actor_id": "supervisor-1",
    "answers": {
      "مرحله رسیدگی": "هیأت حل اختلاف بدوی",
      "تاریخ ابلاغ": "1403/02/18"
    },
    "documents": []
  }'
```

پس از آن Workflow به `RESEARCH` منتقل می‌شود.

### ۶.۴ ثبت تحقیق و منابع

```bash
curl -X POST http://localhost:8000/agents/legal-workflow/{WORKFLOW_ID}/research \
  -H 'Content-Type: application/json' \
  -d '{
    "actor_id": "supervisor-1",
    "findings": {
      "facts": {"certain": ["رقم اظهارنامه ثبت شده است"], "unknown": []},
      "issues": ["بررسی استدلال برگ تشخیص بر اساس ماده ۲۳۷"]
    },
    "citations": [
      {
        "source_type": "law",
        "source_id": "law-237",
        "title": "ماده ۲۳۷ قانون مالیات‌های مستقیم",
        "url": "drive://laws/direct-tax/article-237",
        "effective_date": ""
      }
    ]
  }'
```

ارسال فهرست خالی `citations` عمداً Workflow را در وضعیت `BLOCKED` قرار می‌دهد.

### ۶.۵ ثبت پیش‌نویس

```bash
curl -X POST http://localhost:8000/agents/legal-workflow/{WORKFLOW_ID}/draft \
  -H 'Content-Type: application/json' \
  -d '{
    "actor_id": "supervisor-1",
    "draft": "ریاست محترم هیأت حل اختلاف ...",
    "quality": {"blockers": []},
    "attachment_index": [
      {"order": 1, "title": "برگ تشخیص", "document_id": "doc-1"}
    ]
  }'
```

در صورت نبود blocker، وضعیت به `HUMAN_REVIEW` می‌رود و دروازه `FINAL_HUMAN_REVIEW` باز می‌شود.

### ۶.۶ تأیید یا رد ناظر

```bash
curl -X POST http://localhost:8000/agents/legal-workflow/{WORKFLOW_ID}/approve \
  -H 'Content-Type: application/json' \
  -d '{
    "supervisor_id": "supervisor-1",
    "decision": "approve",
    "note": "استنادات، ارقام و پیوست‌ها کنترل شد."
  }'
```

مقادیر مجاز `decision`:

- `approve`: انتقال به `APPROVED`
- `request_changes`: انتقال به `BLOCKED` با ثبت یادداشت اصلاحی
- `reject`: انتقال به `BLOCKED`

### ۶.۷ تحویل نهایی

```bash
curl -X POST http://localhost:8000/agents/legal-workflow/{WORKFLOW_ID}/deliver \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"supervisor-1"}'
```

این درخواست فقط از وضعیت `APPROVED` مجاز است و Workflow را به `DELIVERED` می‌برد.

### ۶.۸ مشاهده وضعیت

```bash
curl http://localhost:8000/agents/legal-workflow/{WORKFLOW_ID}
```

برای داشبورد ناظر از فیلدهای زیر استفاده کنید:

```text
status
current_stage
pending_gates
version
data.release_blockers
events
```

---

## ۷. سناریوی تست اجراشده

سناریوی نمونه به شکل زیر اجرا شد:

### مرحله ۱: ایجاد پرونده

```text
case_id = demo-1
owner_id = supervisor
request = اعتراض به برگ تشخیص
```

خروجی مورد انتظار:

```text
status = INTAKE
current_stage = case-intake
```

### مرحله ۲: Intake کامل

اطلاعات اولیه بدون ابهام مؤثر ثبت شد:

```text
facts = {}
missing_fields = []
scope = {}
```

خروجی:

```text
status = RESEARCH
current_stage = document-forensics
```

### مرحله ۳: ثبت منبع

یک منبع قابل ردیابی برای ماده ۲۳۷ ثبت شد:

```json
{"source_id":"237", "title":"ماده ۲۳۷"}
```

پس از آن وضعیت به `ANALYSIS` منتقل شد.

### مرحله ۴: ثبت پیش‌نویس بدون blocker

```text
quality.blockers = []
draft = «پیش‌نویس»
```

خروجی:

```text
status = HUMAN_REVIEW
pending_gates = ["FINAL_HUMAN_REVIEW"]
```

### مرحله ۵: تأیید ناظر

```text
supervisor_id = supervisor
decision = approve
note = بازبینی شد
```

خروجی:

```text
status = APPROVED
```

### مرحله ۶: تحویل

با actor مالک پرونده، عملیات `deliver` اجرا شد:

```text
status = DELIVERED
```

در مجموع ۶ رویداد حسابرسی برای این نمونه ثبت شد:

1. `workflow.started`
2. `intake.completed`
3. `research.completed`
4. `draft.ready`
5. `human_review.approve`
6. `pleading.delivered`

### سناریوهای منفی تست‌شده

1. اگر `missing_fields` وجود داشته باشد، وضعیت `NEEDS_CLARIFICATION` می‌شود و تحقیق بدون رفع ابهام ادامه پیدا نمی‌کند.
2. اگر `citations` خالی باشد، وضعیت `BLOCKED` و دروازه `EVIDENCE` فعال می‌شود.
3. کاربری غیر از مالک Workflow نمی‌تواند approve یا deliver کند.
4. deliver پیش از approve مجاز نیست.
5. کیفیت دارای blocker باعث توقف انتشار می‌شود.

اجرای محلی تست‌ها:

```bash
PYTHONPATH=packages uv run --with pytest pytest -q \
  tests/test_legal_workflow.py tests/test_agent_security.py
```

خروجی فعلی: **۷ تست موفق**.

---

## ۸. چک‌لیست انتقال به Production

- [ ] ایجاد migration و اعمال schema در PostgreSQL
- [ ] جایگزینی `LegalAppealWorkflow` درون‌حافظه‌ای با `WorkflowService + Repository`
- [ ] استخراج `owner_id` و `supervisor_id` از JWT/RBAC، نه body
- [ ] ذخیره فایل‌ها در object storage و نگهداری hash/URI در `workflow_artifacts`
- [ ] ثبت همه transitionها با actor، agent، timestamp و correlation ID
- [ ] فعال‌سازی optimistic locking و `SELECT FOR UPDATE`
- [ ] جداسازی tenant/case در queryها و policyهای دیتابیس
- [ ] رمزنگاری داده‌های حساس و محدودسازی logها
- [ ] تعریف retention و archive برای پرونده و رویدادها
- [ ] افزودن تست integration با PostgreSQL واقعی یا Testcontainers
- [ ] مانیتورینگ زمان هر ایجنت، خطا، blocker و تعداد بازبینی انسانی
- [ ] اجرای migration در staging پیش از production
