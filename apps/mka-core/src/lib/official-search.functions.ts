import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

export type OfficialHit = { title: string; url: string; site: string; summary: string };

const DOMAINS = ["intamedia.ir", "tax.gov.ir", "rc.majlis.ir"];

const siteLabel = (host: string) =>
  host.includes("majlis") ? "پایگاه قوانین مجلس" : "سازمان امور مالیاتی";

const SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["results"],
  properties: {
    results: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["title", "url", "summary"],
        properties: {
          title: { type: "string" },
          url: { type: "string" },
          summary: { type: "string" },
        },
      },
    },
  },
};

/** جستجو در سایت سازمان امور مالیاتی و پایگاه قوانین مجلس؛ فقط نتایج همین دامنه‌ها برگردانده می‌شود. */
export const searchOfficial = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => z.object({ q: z.string().min(2).max(120) }).parse(input))
  .handler(async ({ data }): Promise<{ results: OfficialHit[]; error: string | null }> => {
    const key = process.env["LOVABLE_API_KEY"];
    if (!key) return { results: [], error: "سرویس جستجوی رسمی پیکربندی نشده است." };

    const res = await fetch("https://ai.gateway.lovable.dev/v1/responses", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Lovable-API-Key": key, "X-Lovable-AIG-SDK": "fetch" },
      body: JSON.stringify({
        model: "openai/gpt-6-astra",
        stream: true,
        store: false,
        reasoning: { effort: "low" },
        instructions:
          "با ابزار جستجوی وب، فقط در سایت‌های سازمان امور مالیاتی ایران و پایگاه قوانین مجلس جستجو کن و حداکثر ۸ صفحه رسمی مرتبط را با عنوان، نشانی دقیق و خلاصه یک‌جمله‌ای فارسی برگردان. نشانی‌ها را از خودت نساز.",
        input: `عبارت جستجو: ${data.q}`,
        tools: [{ type: "web_search", filters: { allowed_domains: DOMAINS } }],
        text: { format: { type: "json_schema", name: "official_results", strict: true, schema: SCHEMA } },
      }),
    });

    if (!res.ok || !res.body) {
      const msg =
        res.status === 402
          ? "اعتبار سرویس هوش مصنوعی تمام شده است."
          : res.status === 429
            ? "درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."
            : "جستجو در منابع رسمی فعلاً ممکن نیست.";
      return { results: [], error: msg };
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let text = "";
    const cited = new Map<string, string>();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        try {
          const evt = JSON.parse(payload) as {
            type?: string;
            delta?: string;
            annotation?: { url?: string; title?: string };
          };
          if (evt.type === "response.output_text.delta" && evt.delta) text += evt.delta;
          if (evt.type === "response.output_text.annotation.added" && evt.annotation?.url)
            cited.set(evt.annotation.url, evt.annotation.title ?? evt.annotation.url);
        } catch {
          /* partial */
        }
      }
    }

    const allowed = (url: string) => {
      try {
        const host = new URL(url).hostname;
        return DOMAINS.some((d) => host === d || host.endsWith(`.${d}`)) ? host : null;
      } catch {
        return null;
      }
    };

    let parsed: Array<{ title: string; url: string; summary: string }> = [];
    try {
      parsed = (JSON.parse(text) as { results: typeof parsed }).results ?? [];
    } catch {
      /* fall back to citations */
    }
    for (const [url, title] of cited) if (!parsed.some((p) => p.url === url)) parsed.push({ title, url, summary: "" });

    const seen = new Set<string>();
    const results: OfficialHit[] = [];
    for (const p of parsed) {
      const host = allowed(p.url);
      const k = p.url.replace(/[#?].*$/, "").replace(/\/$/, "");
      if (!host || seen.has(k)) continue;
      seen.add(k);
      results.push({ title: p.title || p.url, url: p.url, site: siteLabel(host), summary: p.summary });
    }
    return { results: results.slice(0, 10), error: null };
  });
