import { createServerFn } from "@tanstack/react-start";
import { createClient } from "@supabase/supabase-js";
import { z } from "zod";
import type { Database } from "@/integrations/supabase/types";

const SYSTEM_PROMPT = `شما یک راهنمای آموزشی امور مالیاتی ایران هستید و باید پاسخ مستند بدهید.

ترتیب استفاده از منابع (الزامی):
1. ابتدا «مخزن اسناد» (منابع با شناسه D). اگر پاسخ در آن‌ها هست، بر آن تکیه کنید.
2. سپس قوانین و مواد قانونی (شناسه Q) و بخشنامه‌ها (شناسه B) کتابخانه.
3. فقط اگر منابع بالا کافی نبود، با ابزار جستجو در سایت سازمان امور مالیاتی و سامانه قوانین مجلس جستجو کنید.

قواعد:
- هر ادعا را با شناسه منبع در کروشه مستند کنید، مثل [D2] یا [Q1]. برای نتایج وب، نام سایت را بنویسید.
- چیزی را که در منابع نیست به‌عنوان متن قانون نقل نکنید؛ اگر از دانش عمومی استفاده می‌کنید صریحاً بگویید «بدون منبع مستند».
- ساختار پاسخ: خلاصه پاسخ، مستندات قانونی، مراحل پیشنهادی عملی، پرسش‌های تکمیلی (در صورت نیاز).
- در پایان تأکید کنید این راهنمایی جنبه اطلاع‌رسانی دارد و جایگزین مشاوره رسمی نیست.
- پاسخ فارسی، شفاف و ساختاریافته. از ارائه راهکار فرار مالیاتی خودداری کنید.`;

const Input = z.object({
  question: z.string().min(10, "لطفاً مسئله خود را کمی کامل‌تر توضیح دهید (حداقل ۱۰ نویسه).").max(4000),
});

const STOP = new Set(
  "از به در با که این آن را و یا برای تا بر هم چه چطور چگونه آیا است هست نیست شود کنم کنید کرده‌ام کرده دارم باید می من ما شما یک چند اگر پس هر ولی اما".split(" "),
);

export type SourceItem = {
  id: string;
  origin: "drive" | "law" | "circular" | "web";
  originLabel: string;
  title: string;
  meta: string | null;
  href: string;
};

function publicClient() {
  const key = process.env["SUPABASE_PUBLISHABLE_KEY"]!;
  return createClient<Database>(process.env["SUPABASE_URL"]!, key, {
    auth: { storage: undefined, persistSession: false, autoRefreshToken: false },
    global: {
      fetch: (input, init) => {
        const headers = new Headers(init?.headers);
        if (key.startsWith("sb_") && headers.get("Authorization") === `Bearer ${key}`) headers.delete("Authorization");
        headers.set("apikey", key);
        return fetch(input, { ...init, headers });
      },
    },
  });
}

function keywords(q: string) {
  const words = q
    .replace(/[\u200c]/g, " ")
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOP.has(w));
  return [...new Set(words)].sort((a, b) => b.length - a.length).slice(0, 6);
}

const clip = (t: string | null, n = 1500) => (t ?? "").replace(/\s+/g, " ").trim().slice(0, n);

async function gatherSources(question: string) {
  const supabase = publicClient();
  const kws = keywords(question);
  if (kws.length === 0) return { sources: [] as SourceItem[], context: "" };
  const orFor = (cols: string[]) => kws.flatMap((k) => cols.map((c) => `${c}.ilike.%${k.replace(/[,()%]/g, "")}%`)).join(",");

  const [drive, arts, circs] = await Promise.all([
    supabase.from("drive_documents").select("id, name, folder_path, content").or(orFor(["name", "content"])).limit(40),
    supabase.from("articles").select("source_id, book_source_id, title, chapter, content").or(orFor(["title", "content"])).limit(40),
    supabase.from("circulars").select("source_id, number, subject, content").or(orFor(["subject", "content"])).limit(40),
  ]);

  const score = (text: string) => kws.reduce((s, k) => s + (text.includes(k) ? 1 : 0), 0);
  const top = <T,>(rows: T[] | null, text: (r: T) => string, n: number) =>
    (rows ?? []).map((r) => ({ r, s: score(text(r)) })).sort((a, b) => b.s - a.s).slice(0, n).map((x) => x.r);

  const sources: SourceItem[] = [];
  const blocks: string[] = [];
  top(drive.data, (r) => `${r.name} ${r.content ?? ""}`, 6).forEach((r, i) => {
    const id = `D${i + 1}`;
    sources.push({ id, origin: "drive", originLabel: "مخزن اسناد", title: r.name, meta: r.folder_path ?? null, href: `/api/public/drive/${r.id}` });
    blocks.push(`[${id}] (مخزن اسناد) ${r.name} — ${r.folder_path ?? ""}\n${clip(r.content) || "(متن این فایل هنوز خوانده نشده؛ فقط عنوان در دسترس است)"}`);
  });
  top(arts.data, (r) => `${r.title} ${r.content ?? ""}`, 5).forEach((r, i) => {
    const id = `Q${i + 1}`;
    sources.push({ id, origin: "law", originLabel: "قوانین کتابخانه", title: r.title, meta: r.chapter ?? null, href: `/books/${r.book_source_id}#${r.source_id}` });
    blocks.push(`[${id}] (ماده قانونی) ${r.title}\n${clip(r.content)}`);
  });
  top(circs.data, (r) => `${r.subject ?? ""} ${r.content ?? ""}`, 4).forEach((r, i) => {
    const id = `B${i + 1}`;
    sources.push({ id, origin: "circular", originLabel: "بخشنامه‌های کتابخانه", title: r.subject ?? `بخشنامه ${r.number ?? r.source_id}`, meta: r.number ? `شماره ${r.number}` : null, href: `/circulars/${r.source_id}` });
    blocks.push(`[${id}] (بخشنامه) ${r.subject ?? ""} ${r.number ?? ""}\n${clip(r.content)}`);
  });
  return { sources, context: blocks.join("\n\n---\n\n") };
}

export const getTaxGuidance = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => Input.parse(input))
  .handler(async ({ data }) => {
    const key = process.env["LOVABLE_API_KEY"];
    if (!key) throw new Error("سرویس هوش مصنوعی هنوز پیکربندی نشده است.");

    const { sources, context } = await gatherSources(data.question);

    const res = await fetch("https://ai.gateway.lovable.dev/v1/responses", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Lovable-API-Key": key, "X-Lovable-AIG-SDK": "fetch" },
      body: JSON.stringify({
        model: "openai/gpt-6-astra",
        instructions: SYSTEM_PROMPT,
        input: `منابع یافت‌شده:\n${context || "(هیچ منبعی در مخزن اسناد و کتابخانه یافت نشد)"}\n\n===\nمسئله مالیاتی کاربر:\n${data.question}`,
        tools: [{ type: "web_search", filters: { allowed_domains: ["intamedia.ir", "tax.gov.ir", "rc.majlis.ir"] } }],
        stream: true,
        store: false,
        reasoning: { effort: "low" },
      }),
    });

    if (!res.ok) {
      let message = "در حال حاضر امکان تولید راهنمایی وجود ندارد؛ لطفاً کمی بعد دوباره تلاش کنید.";
      if (res.status === 402) message = "اعتبار سرویس هوش مصنوعی تمام شده است.";
      else if (res.status === 429) message = "درخواست‌ها زیاد است؛ لطفاً یک دقیقه دیگر تلاش کنید.";
      else {
        try {
          const body = (await res.json()) as { message?: string; error?: { message?: string } };
          message = body.message ?? body.error?.message ?? message;
        } catch {
          /* keep default */
        }
      }
      throw new Error(message);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error("پاسخی از سرویس هوش مصنوعی دریافت نشد.");
    const decoder = new TextDecoder();
    let buffer = "";
    let answer = "";
    const web = new Map<string, string>();

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
            annotation?: { type?: string; url?: string; title?: string };
          };
          if (evt.type === "response.output_text.delta" && evt.delta) answer += evt.delta;
          if (evt.type === "response.output_text.annotation.added" && evt.annotation?.url) {
            web.set(evt.annotation.url, evt.annotation.title ?? evt.annotation.url);
          }
        } catch {
          /* ignore partial */
        }
      }
    }

    if (!answer.trim()) throw new Error("پاسخی تولید نشد؛ لطفاً مسئله را دقیق‌تر بنویسید و دوباره تلاش کنید.");

    const webSources: SourceItem[] = [...web.entries()].map(([url, title], i) => {
      const host = new URL(url).hostname;
      return {
        id: `W${i + 1}`,
        origin: "web",
        originLabel: host.includes("majlis") ? "سامانه قوانین مجلس" : "سازمان امور مالیاتی",
        title,
        meta: null,
        href: url,
      };
    });
    return { answer, sources: [...sources, ...webSources] };
  });
