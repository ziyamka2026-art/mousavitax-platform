# ADR-009: TAXLAW-GROK Constitution v2.0 — Foundational Charter

## Status
Accepted — 2026-10-25

## Context (زمینه)

پلتفرم MousaviTax AI Platform یک سیستم هوش مصنوعی مالیاتی برای ایران است که در آن چندین Agent (Triage، RAG، Citation، Risk) هم‌زمان عمل می‌کنند. بدون یک منشور بالادستی، این Agents می‌توانند رفتارهای متناقض نشان دهند — مثلاً:

- بدون مستند سخن بگویند (نقض اصل ۲ منشور)
- اطلاعات هویتی مؤدیان را در log عمومی ثبت کنند (نقض اصل ۱)
- در ابهام به نفع اداره تفسیر کنند (نقض اصل ۳ — تفسیر مضیق)
- نسخه‌ی تحلیل را بدون بایگانی رها کنند (نقض اصل ۲)
- بدون انطباق با گردش‌کار مصوب، لایحه تولید کنند (نقض اصل ۴)

این ADR منشور «مغز دوم قانون» (TAXLAW-GROK Constitution v2.0) را به‌عنوان سند بالادستی رفتار سامانه پذیرفته است. هر ویژگی جدید، هر Agent جدید، هر prompt جدید باید با این منشور انطباق یابد.

## Decision (تصمیم)

### ۱. چهار اصل بنیادین به‌عنوان invariants فنی پذیرفته می‌شوند

| اصل | Enforcement فنی |
|------|------------------|
| **اصل ۱: محرمانگی مطلق** | PII redaction middleware + RLS + AES-256-GCM برای PII در logs |
| **اصل ۲: ثبت اجباری نسخه تحلیل** | INSERT-only table `case_analyses` + RLS blocking UPDATE/DELETE + auto-versioning trigger |
| **اصل ۳: انطباق با قواعد فقهی** | Fiqh Validator Agent + LLM directive در system prompt |
| **اصل ۴: پیوند اسکریپت‌های مخزن** | ۷ ماژول به‌عنوان live services در `services/source-bridge/` |

### ۲. گردش‌کار شش‌مرحله‌ای به‌عنوان orchestrator پیش‌فرض پذیرفته می‌شود

هر تحلیل حقوقی از طریق `LegalAnalysisPipeline` با شش Stage اجرا می‌شود. هیچ Stage قابل skip نیست.

### ۳. سوگندنامه به‌عنوان runtime guards پیاده‌سازی می‌شود

شش بند سوگند به‌صورت کد guard در `packages/oath/runtime_guards.py` قابل اجرا هستند. هر خروجی پیش از تحویل از این guards عبور می‌کند.

### ۴. شناسه پوشه مرجع Google Drive

```
TAXLAW_GROK_MASTER_FOLDER_ID=1M7rsSpQf0akKKmV2P6o66A-uj8KF3cJW
```

این متغیر در `.env.example` اضافه شود و `services/source-bridge/` به‌عنوان source-of-truth برای اسکریپت‌های مخزن استفاده شود.

## Consequences (پیامدها)

### مزایya
- ✅ رفتار Agents قابل پیش‌بینی و قابل دفاع است
- ✅ Compliance با قوانین مالیاتی ایران تضمین می‌شود
- ✅ Audit trail کامل برای هر تحلیل موجود است
- ✅ مسئولیت نهایی همیشه بر عهده‌ی انسان است

### هزینه‌ها
- ⚠️ پیاده‌سازی Fiqh Validator نیازمند ارزیابی LLM است (هزینه‌ی API)
- ⚠️ INSERT-only tables دیباگ را سخت‌تر می‌کند (هر اشتباه نیاز به migration اصلاحی دارد)
- ⚠️ PII redaction می‌تواند کیفیت RAG را کاهش دهد (trade-off: privacy vs recall)
- ⚠️ اجرای هر ۶ مرحله برای هر query، latency را افزایش می‌دهد (هدف: < ۵ ثانیه برای query ساده)

### وابستگی‌ها
- ADR-007 (Hybrid AI Tax Platform) — این ADR مکمل آن است
- ADR-008 (Central Admin Case Ledger) — ارتباط با master control
- Migrations 001-004 — برای RLS و multi-tenant
- Migration 005 (جدید) — برای `case_analyses` table

## Implementation Plan (نقشه‌ی اجرا)

| فاز | کار | مالک | مدت |
|------|------|------|-----|
| P0 | افزودن `TAXLAW_GROK_MASTER_FOLDER_ID` به `.env.example` | Platform Team | ۱ ساعت |
| P0 | ایجاد `case_analyses` table (migration 005) | Knowledge Team | ۲ ساعت |
| P0 | ایجاد `packages/oath/runtime_guards.py` با ۶ guard | Analyzer Team | ۴ ساعت |
| P0 | اضافه کردن Fiqh Validator به pipeline | Analyzer Team | ۸ ساعت |
| P1 | پیاده‌سازی PII Redactor middleware | Platform Team | ۸ ساعت |
| P1 | Live connection به Google Drive folder (۷ ماژول) | Ingestion Team | ۱۶ ساعت |
| P1 | LegalAnalysisPipeline orchestrator | Analyzer Team | ۱۶ ساعت |
| P2 | LLM Eval برای Fiqh Validator | QA Team | ۲۴ ساعت |
| P2 | UI برای نمایش sworn-oath badge در خروجی | Product UX | ۸ ساعت |

## Reference Documents

- [TAXLAW-GROK Constitution v2.0](../../TAXLAW-GROK-CONSTITUTION.md) — متن کامل منشور
- [ADR-007-Hybrid-AI-Tax-Platform.md](./ADR-007-Hybrid-AI-Tax-Platform.md) — معماری پایه
- [docs/11_TAX_CASE.md](../11_TAX_CASE.md) — پرونده الکترونیکی

## Author
ضیاء الدین موسوی جراحی — تنظیم و تدوین منشور اصلی
ADR توسط AI Senior Dev به فرمت ADR استاندارد ترجمه شد.
