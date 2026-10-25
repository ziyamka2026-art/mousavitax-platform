# MKA-Core — مغز دانشی

سرویس مستقل «مغز دانشی» برای پلتفرم موسوی‌تکس (TanStack Start + Lovable Cloud).
این پوشه هیچ فایل دیگری از مخزن را تغییر نمی‌دهد.

## نقطه اتصال قرارداد

`POST /api/public/v1/orchestrate`

هدر: `Authorization: Bearer <MKA_CORE_API_KEY>` (یا `X-API-Key`)

ورودی:
```json
{ "question": "جریمه کتمان درآمد طبق ماده ۱۹۲؟", "user_id": "اختیاری", "context": {} }
```

خروجی (طبق `packages/shared-contracts/orchestrator.schema.json`):
```json
{ "status": "SUCCESS|INSUFFICIENT_DATA|CLARIFICATION_REQUIRED|ERROR",
  "answer": "...", "citations": [{"source_type":"circular","source_id":"...","title":"...","url":"..."}],
  "actions": [], "trace_id": "uuid" }
```

- فقط دانش رسمی (بخشنامه‌ها) جست‌وجو می‌شود؛ حافظه شخصی کاربران خصوصی می‌ماند.
- سطح اتوماسیون ۱: فقط خواندن و پیشنهاد؛ این نقطه چیزی نمی‌نویسد.
- کلید نادرست → 401؛ ورودی نامعتبر → 400 با `CLARIFICATION_REQUIRED`.

### نمونه پایتون
```python
import os, httpx
r = httpx.post(f"{os.environ['MKA_CORE_URL']}/api/public/v1/orchestrate",
    headers={"Authorization": f"Bearer {os.environ['MKA_CORE_API_KEY']}"},
    json={"question": "نرخ مالیات بر ارزش افزوده"}, timeout=60)
print(r.json())
```

متغیرهای سرور پایتون: `MKA_CORE_URL` (آدرس منتشرشده برنامه) و `MKA_CORE_API_KEY` (همان کلیدی که در Lovable ذخیره شد).

## اجرای محلی
`bun install && bun run dev` — متغیرها در `.env.example`.
