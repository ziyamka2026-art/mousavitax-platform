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

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type, X-API-Key",
};

function json(body: unknown, status = 200) {
  return Response.json(body, { status, headers: CORS });
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
      OPTIONS: async () => new Response(null, { status: 204, headers: CORS }),
      POST: async ({ request }) => {
        const trace_id = crypto.randomUUID();
        const expected = process.env["MKA_CORE_API_KEY"];
        if (!expected) return json({ status: "ERROR", answer: "کلید سرویس تنظیم نشده است.", citations: [], actions: [], trace_id }, 503);
        const auth = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "") ?? request.headers.get("x-api-key") ?? "";
        if (!auth || !(await safeEqual(auth, expected))) {
          return json({ status: "ERROR", answer: "دسترسی غیرمجاز.", citations: [], actions: [], trace_id }, 401);
        }
        let parsed;
        try {
          parsed = Body.safeParse(await request.json());
        } catch {
          parsed = null;
        }
        if (!parsed?.success) {
          return json({ status: "CLARIFICATION_REQUIRED", answer: "ورودی نامعتبر است؛ فیلد question لازم است.", citations: [], actions: [], trace_id }, 400);
        }
        const { createClient } = await import("@supabase/supabase-js");
        const db = createClient(process.env["SUPABASE_URL"]!, process.env["SUPABASE_PUBLISHABLE_KEY"]!, {
          auth: { persistSession: false, autoRefreshToken: false },
        });
        const { orchestrate } = await import("@/lib/brain.server");
        try {
          return json(await orchestrate(db as any, parsed.data.question));
        } catch (e: any) {
          console.error("orchestrate failed", e);
          return json({ status: "ERROR", answer: e?.message ?? "خطا", citations: [], actions: [], trace_id }, 500);
        }
      },
    },
  },
});
