import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

// Shared contract endpoint for bots and the mousavitax-platform Python server.
// Callers send `Authorization: Bearer <MKA_CORE_API_KEY>`. Only official knowledge
// (circulars) is searched — user memory stays private behind RLS.
const Body = z.object({
  question: z.string().min(1).max(2000),
  user_id: z.string().max(200).optional(),
  context: z.record(z.string(), z.unknown()).optional(),
});

function corsHeaders(request: Request): Headers {
  const headers = new Headers({ Vary: "Origin" });
  const origin = request.headers.get("origin");
  const allowedOrigin = process.env["MKA_CORE_ALLOWED_ORIGIN"]?.trim();

  // This is a server-to-server endpoint by default. Browser access is enabled
  // only for one explicitly configured origin; CORS is not an auth mechanism.
  if (origin && allowedOrigin && origin === allowedOrigin) {
    headers.set("Access-Control-Allow-Origin", allowedOrigin);
    headers.set("Access-Control-Allow-Methods", "POST, OPTIONS");
    headers.set("Access-Control-Allow-Headers", "Authorization, Content-Type, X-API-Key");
    headers.set("Access-Control-Max-Age", "600");
  }
  return headers;
}

function json(body: unknown, status = 200, request?: Request) {
  return Response.json(body, { status, headers: request ? corsHeaders(request) : undefined });
}

async function safeEqual(a: string, b: string) {
  const enc = new TextEncoder();
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b)),
  ]);
  const x = new Uint8Array(ha), y = new Uint8Array(hb);
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return d === 0;
}

export const Route = createFileRoute("/api/public/v1/orchestrate")({
  server: {
    handlers: {
      OPTIONS: async ({ request }) => new Response(null, { status: 204, headers: corsHeaders(request) }),
      POST: async ({ request }) => {
        const trace_id = crypto.randomUUID();
        const expected = process.env["MKA_CORE_API_KEY"];
        if (!expected) {
          console.error("MKA_CORE_API_KEY is not configured", { trace_id });
          return json({ status: "ERROR", answer: "سرویس موقتاً در دسترس نیست.", citations: [], actions: [], trace_id }, 503, request);
        }
        const auth = request.headers.get("authorization")?.match(/^Bearer\s+(.+)$/i)?.[1] ?? request.headers.get("x-api-key") ?? "";
        if (!auth || !(await safeEqual(auth, expected))) {
          return json({ status: "ERROR", answer: "دسترسی غیرمجاز.", citations: [], actions: [], trace_id }, 401, request);
        }
        let parsed;
        try {
          parsed = Body.safeParse(await request.json());
        } catch {
          parsed = null;
        }
        if (!parsed?.success) {
          return json({ status: "CLARIFICATION_REQUIRED", answer: "ورودی نامعتبر است؛ فیلد question لازم است.", citations: [], actions: [], trace_id }, 400, request);
        }
        const supabaseUrl = process.env["SUPABASE_URL"];
        const supabaseKey = process.env["SUPABASE_PUBLISHABLE_KEY"];
        if (!supabaseUrl || !supabaseKey) {
          console.error("Supabase configuration is incomplete", { trace_id });
          return json({ status: "ERROR", answer: "سرویس موقتاً در دسترس نیست.", citations: [], actions: [], trace_id }, 503, request);
        }
        const { createClient } = await import("@supabase/supabase-js");
        const db = createClient(supabaseUrl, supabaseKey, {
          auth: { persistSession: false, autoRefreshToken: false },
        });
        const { orchestrate } = await import("@/lib/brain.server");
        try {
          return json(await orchestrate(db as any, parsed.data.question, { scope: "official" }), 200, request);
        } catch (e: unknown) {
          console.error("orchestrate failed", { trace_id, error: e });
          return json({ status: "ERROR", answer: "در پردازش پرسش خطا رخ داد.", citations: [], actions: [], trace_id }, 500, request);
        }
      },
    },
  },
});
