/**
 * Registry Document Registration — server-side functions
 * =====================================================
 *
 * Fixes the critical "new row violates row-level security policy" error
 * by leveraging the new RLS policies in migration 005_registry_documents.sql
 * and the auto_fill_registry_code() trigger that generates MKA-TYPE-NNN codes.
 *
 * @package apps.mka-core.src.lib.registry.functions
 */

import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { z } from "zod";
import {
  inferTypeFromFilename,
  TYPE_ABBREVIATIONS,
  type DocumentType,
} from "@mousavitax/registry";

/**
 * Get the Supabase client for the authenticated user — uses the user's
 * JWT so RLS policies apply automatically.
 *
 * IMPORTANT: This is the key to the RLS fix. Before, we used `publicClient()`
 * which used the publishable key without a user JWT — that bypassed RLS
 * in a way that broke INSERT. Now we pass the user's JWT so RLS sees the
 * authenticated user and applies the INSERT policy correctly.
 */
async function userSupabaseClient(context: { supabase: any; userId: string }) {
  // The TanStack Start middleware `requireSupabaseAuth` already injects a
  // Supabase client configured with the user's access token. RLS will work.
  return context.supabase;
}

/**
 * Get the user's tenant_id from user_profiles (cached in JWT metadata).
 */
async function getUserTenantId(ctx: { supabase: any; userId: string }): Promise<string> {
  const { data, error } = await ctx.supabase
    .from("user_profiles")
    .select("tenant_id")
    .eq("user_id", ctx.userId)
    .maybeSingle();

  if (error) throw new Error(`Failed to fetch tenant_id: ${error.message}`);
  if (!data) throw new Error("User profile not found — user_profiles row missing for this user.");
  return data.tenant_id;
}

// ---------------------------------------------------------------------------
// Schema for the new registration form
// ---------------------------------------------------------------------------

const registerDocSchema = z.object({
  title: z.string().min(1).max(300),                            // ← NEW: dedicated title field
  source_type: z.enum(['web', 'drive', 'upload', 'manual']).default('manual'),
  source_url: z.string().url().optional(),                      // URL or Drive file link
  drive_file_id: z.string().optional(),                         // ← NEW: Drive file picker result
  source_ref: z.string().max(500).optional(),                   // human-readable path / file name
  expert_notes: z.string().max(5000).optional(),
  extracted_text: z.string().max(200000).optional(),
  type_hint: z.enum([
    'law', 'circular', 'judgment', 'contract',
    'appeal', 'tax_case', 'general',
  ]).optional(),                                                 // ← NEW: type hint for code generation
  metadata: z.record(z.any()).optional(),
});

/**
 * Register a new document.
 *
 * Flow:
 *   1. Auth middleware ensures user is logged in
 *   2. Get tenant_id from user_profiles
 *   3. Infer type from filename or use provided type_hint
 *   4. INSERT into registry_documents — the DB trigger auto-fills:
 *      - code (MKA-TYPE-001)
 *      - sequence_num
 *      - type_code
 *   5. Return the saved document with its new code
 */
export const registerDocument = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) => registerDocSchema.parse(input ?? {}))
  .handler(async ({ data, context }) => {
    const supabase = await userSupabaseClient(context);
    const tenantId = await getUserTenantId({ supabase, userId: context.userId });

    // Infer type from filename/source_ref if not provided
    const filename = data.source_ref ?? data.source_url ?? "";
    const docType: DocumentType = data.type_hint ?? inferTypeFromFilename(filename);
    const typeCode = TYPE_ABBREVIATIONS[docType];

    // Build the insert payload — the trigger will auto-fill `code` and `sequence_num`
    const insertPayload = {
      tenant_id: tenantId,
      user_id: context.userId,
      title: data.title,
      source_type: data.source_type,
      source_url: data.source_url ?? null,
      source_ref: data.source_ref ?? null,
      drive_file_id: data.drive_file_id ?? null,  // ← NEW field for Drive picker
      content: data.extracted_text ?? null,
      summary: null,
      expert_notes: data.expert_notes ?? null,
      extracted_text: data.extracted_text ?? null,
      status: 'unidentified',
      type_code: typeCode,
      metadata: {
        ...data.metadata,
        type_label: docType,
        registered_via: 'web_form',
      },
      // code and sequence_num are auto-filled by trigger
    };

    const { data: inserted, error } = await supabase
      .from("registry_documents")
      .insert(insertPayload)
      .select("id, code, title, type_code, status, created_at")
      .single();

    if (error) {
      // Helpful error messages for common failures
      if (error.code === "42501" || error.message.includes("row-level security")) {
        throw new Error(
          "خطای سطح‌امنیت: حساب شما اجازه‌ی ثبت ندارد. مطمئن شوید وارد شده‌اید و پروفایل شما در user_profiles موجود است. " +
          "اگر مشکل ادامه داشت، ادمین سامانه را مطلع کنید تا migration 005 را اعمال کند."
        );
      }
      if (error.message.includes("registry_documents" && "does not exist")) {
        throw new Error(
          "جدول registry_documents وجود ندارد. migration 005_registry_documents.sql را در Supabase اعمال کنید."
        );
      }
      throw new Error(`DB error: ${error.message}`);
    }

    return {
      document: inserted,
      code: inserted.code,
      type_code: inserted.type_code,
      message: `سند با کد ${inserted.code} ثبت شد.`,
    };
  });

/**
 * List documents for the current user's tenant.
 */
export const listRegistryDocuments = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z
      .object({
        query: z.string().optional(),
        status: z.string().optional(),
        type_code: z.string().optional(),
        page: z.number().int().min(0).default(0),
        pageSize: z.number().int().min(1).max(100).default(20),
      })
      .parse(input ?? {}),
  )
  .handler(async ({ data, context }) => {
    const supabase = await userSupabaseClient(context);

    let query = supabase
      .from("registry_documents")
      .select("id, code, title, source_type, source_url, status, type_code, expert_notes, created_at, updated_at", { count: "exact" });

    // Apply filters
    const term = (data.query ?? "").trim();
    if (term.length > 1) {
      query = query.or(
        `title.ilike.%${term}%,code.ilike.%${term}%,expert_notes.ilike.%${term}%`
      );
    }
    if (data.status && data.status !== "all") {
      query = query.eq("status", data.status);
    }
    if (data.type_code && data.type_code !== "all") {
      query = query.eq("type_code", data.type_code.toUpperCase());
    }

    const size = data.pageSize;
    const { data: rows, count, error } = await query
      .order("created_at", { ascending: false })
      .range(data.page * size, data.page * size + size - 1);

    if (error) throw new Error(error.message);

    return {
      documents: rows ?? [],
      total: count ?? 0,
      page: data.page,
      pageSize: size,
    };
  });

/**
 * Update a document — owner or admin only (RLS enforces).
 */
export const updateRegistryDocument = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z
      .object({
        id: z.string().uuid(),
        title: z.string().min(1).max(300).optional(),
        status: z.enum([
          'unidentified', 'identified', 'reviewed',
          'approved', 'rejected', 'archived',
        ]).optional(),
        expert_notes: z.string().max(5000).optional(),
        summary: z.string().max(5000).optional(),
        extracted_text: z.string().max(200000).optional(),
      })
      .parse(input ?? {}),
  )
  .handler(async ({ data, context }) => {
    const supabase = await userSupabaseClient(context);

    const { id, ...updates } = data;
    const cleaned: Record<string, unknown> = { ...updates };
    // Strip undefined values
    Object.keys(cleaned).forEach((k) => {
      if (cleaned[k] === undefined) delete cleaned[k];
    });

    const { data: updated, error } = await supabase
      .from("registry_documents")
      .update(cleaned)
      .eq("id", id)
      .select("id, code, title, status, updated_at")
      .maybeSingle();

    if (error) throw new Error(error.message);
    if (!updated) throw new Error("سند یافت نشد یا اجازه‌ی ویرایش ندارید.");

    return { document: updated };
  });

/**
 * Delete a document (soft delete — sets deleted_at).
 */
export const deleteRegistryDocument = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z.object({ id: z.string().uuid() }).parse(input ?? {}),
  )
  .handler(async ({ data, context }) => {
    const supabase = await userSupabaseClient(context);

    // Soft delete — only sets deleted_at; RLS blocks true DELETE for non-admins
    const { error } = await supabase
      .from("registry_documents")
      .update({ deleted_at: new Date().toISOString() })
      .eq("id", data.id);

    if (error) throw new Error(error.message);
    return { ok: true, id: data.id };
  });

/**
 * Get document by code — useful for deep-linking.
 */
export const getRegistryDocumentByCode = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z.object({ code: z.string().regex(/^MKA-[A-Z]{3}-\d{3}$/i) }).parse(input ?? {}),
  )
  .handler(async ({ data, context }) => {
    const supabase = await userSupabaseClient(context);
    const { data: doc, error } = await supabase
      .from("registry_documents")
      .select("*")
      .eq("code", data.code.toUpperCase())
      .maybeSingle();

    if (error) throw new Error(error.message);
    return { document: doc ?? null };
  });
