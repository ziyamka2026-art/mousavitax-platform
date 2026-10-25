// Server-only: indexes the owner's Google Drive tax folder into drive_documents.
export const DRIVE_ROOT_FOLDER = "1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del";
const GATEWAY = "https://connector-gateway.lovable.dev/google_drive/drive/v3";
const MAX_OCR_BYTES = 8 * 1024 * 1024;

type DriveFile = { id: string; name: string; mimeType: string; size?: string; modifiedTime?: string };

function driveHeaders() {
  const lovable = process.env["LOVABLE_API_KEY"];
  const conn = process.env["GOOGLE_DRIVE_API_KEY"];
  if (!lovable || !conn) throw new Error("اتصال گوگل درایو پیکربندی نشده است.");
  return { Authorization: `Bearer ${lovable}`, "X-Connection-Api-Key": conn };
}

async function driveFetch(path: string, params?: Record<string, string>) {
  const url = new URL(`${GATEWAY}${path}`);
  for (const [k, v] of Object.entries(params ?? {})) url.searchParams.set(k, v);
  let res = await fetch(url, { headers: driveHeaders() });
  for (let attempt = 1; attempt <= 3 && (res.status === 429 || res.status === 403 || res.status >= 500); attempt++) {
    await new Promise((r) => setTimeout(r, 1500 * attempt));
    res = await fetch(url, { headers: driveHeaders() });
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Google Drive [${res.status}]: ${body.slice(0, 300)}`);
  }
  return res;
}

async function listChildren(folderId: string): Promise<DriveFile[]> {
  const out: DriveFile[] = [];
  let pageToken: string | undefined;
  do {
    const res = await driveFetch("/files", {
      q: `'${folderId}' in parents and trashed=false`,
      fields: "nextPageToken,files(id,name,mimeType,size,modifiedTime)",
      pageSize: "1000",
      supportsAllDrives: "true",
      includeItemsFromAllDrives: "true",
      ...(pageToken ? { pageToken } : {}),
    });
    const json = (await res.json()) as { files: DriveFile[]; nextPageToken?: string };
    out.push(...json.files);
    pageToken = json.nextPageToken;
  } while (pageToken);
  return out;
}

/** Download a file's bytes (exports Google Docs as plain text). */
export async function downloadDriveFile(id: string, mimeType: string) {
  if (mimeType === "application/vnd.google-apps.document") {
    return driveFetch(`/files/${id}/export`, { mimeType: "text/plain" });
  }
  if (mimeType === "application/vnd.google-apps.spreadsheet") {
    return driveFetch(`/files/${id}/export`, { mimeType: "text/csv" });
  }
  if (mimeType.startsWith("application/vnd.google-apps")) {
    return driveFetch(`/files/${id}/export`, { mimeType: "application/pdf" });
  }
  return driveFetch(`/files/${id}`, { alt: "media", supportsAllDrives: "true" });
}

async function ocrWithAi(bytes: ArrayBuffer, mimeType: string, name: string): Promise<string> {
  const key = process.env["LOVABLE_API_KEY"];
  if (!key) throw new Error("LOVABLE_API_KEY missing");
  const b64 = Buffer.from(bytes).toString("base64");
  const part =
    mimeType === "application/pdf"
      ? { type: "input_file", filename: name, file_data: `data:application/pdf;base64,${b64}` }
      : { type: "input_image", image_url: `data:${mimeType};base64,${b64}` };
  const res = await fetch("https://ai.gateway.lovable.dev/v1/responses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Lovable-API-Key": key,
      "X-Lovable-AIG-SDK": "fetch",
    },
    body: JSON.stringify({
      model: "openai/gpt-6-luna",
      stream: true,
      store: false,
      instructions:
        "متن کامل این سند مالیاتی فارسی را دقیقاً و بدون توضیح اضافه استخراج کن. فقط متن سند را برگردان. حداکثر ۶۰۰۰ کلمه.",
      input: [{ role: "user", content: [{ type: "input_text", text: `نام فایل: ${name}` }, part] }],
    }),
  });
  if (!res.ok || !res.body) {
    const body = await res.text();
    const err = new Error(`AI [${res.status}]: ${body.slice(0, 200)}`) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let text = "";
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
        const evt = JSON.parse(payload) as { type?: string; delta?: string };
        if (evt.type === "response.output_text.delta" && evt.delta) text += evt.delta;
      } catch {
        /* ignore partial */
      }
    }
  }
  return text.trim();
}

export async function syncDrive(options: { ocrLimit?: number; textLimit?: number } = {}) {
  const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
  const ocrLimit = options.ocrLimit ?? 8;

  // 1) Walk the folder tree and index metadata.
  const rows: Array<Record<string, unknown>> = [];
  const queue: Array<{ id: string; path: string }> = [{ id: DRIVE_ROOT_FOLDER, path: "" }];
  let guard = 0;
  while (queue.length && guard++ < 400) {
    const folder = queue.shift()!;
    for (const f of await listChildren(folder.id)) {
      if (f.mimeType === "application/vnd.google-apps.folder") {
        queue.push({ id: f.id, path: folder.path ? `${folder.path} / ${f.name}` : f.name });
      } else {
        rows.push({
          id: f.id,
          name: f.name,
          folder_path: folder.path || null,
          mime_type: f.mimeType,
          size: f.size ? Number(f.size) : null,
          modified_time: f.modifiedTime ?? null,
          synced_at: new Date().toISOString(),
        });
      }
    }
  }
  for (let i = 0; i < rows.length; i += 500) {
    const { error } = await supabaseAdmin.from("drive_documents").upsert(rows.slice(i, i + 500) as never);
    if (error) throw new Error(error.message);
  }

  // 2) Extract text: plain-text files in a large free batch, then a small AI batch for images/PDFs.
  const { data: textPending } = await supabaseAdmin
    .from("drive_documents")
    .select("id, name, mime_type, size")
    .is("content", null)
    .or("mime_type.like.text/%,mime_type.eq.application/vnd.google-apps.document,mime_type.eq.application/vnd.google-apps.spreadsheet")
    .limit(options.textLimit ?? 300);
  const { data: ocrPending } = await supabaseAdmin
    .from("drive_documents")
    .select("id, name, mime_type, size")
    .is("content", null)
    .or("mime_type.like.image/%,mime_type.eq.application/pdf")
    .lte("size", MAX_OCR_BYTES)
    .order("modified_time", { ascending: false })
    .limit(ocrLimit);
  const pending = [...(textPending ?? []), ...(ocrPending ?? [])];

  let extracted = 0;
  let stop = false;
  const work = async (doc: (typeof pending)[number]) => {
    const mime = doc.mime_type ?? "";
    try {
      let content = "";
      if (mime.startsWith("application/vnd.google-apps") || mime.startsWith("text/")) {
        const res = await downloadDriveFile(doc.id, mime);
        if (mime === "application/vnd.google-apps.document" || mime === "application/vnd.google-apps.spreadsheet" || mime.startsWith("text/")) {
          content = await res.text();
        }
      } else if ((mime.startsWith("image/") || mime === "application/pdf") && (doc.size ?? 0) <= MAX_OCR_BYTES) {
        const res = await downloadDriveFile(doc.id, mime);
        content = await ocrWithAi(await res.arrayBuffer(), mime, doc.name);
      }
      await supabaseAdmin
        .from("drive_documents")
        .update({ content: content.slice(0, 200000) || "" } as never)
        .eq("id", doc.id);
      extracted++;
    } catch (error) {
      const status = (error as { status?: number }).status;
      console.error("drive extract failed", doc.id, error);
      if (status === 402 || status === 403 || status === 429) stop = true;
    }
  };
  // اجرای موازی برای سرعت بیشتر (۶ سند هم‌زمان)
  const queueDocs = [...pending];
  await Promise.all(
    Array.from({ length: 6 }, async () => {
      while (!stop && queueDocs.length) await work(queueDocs.shift()!);
    }),
  );

  const { count: remaining } = await supabaseAdmin
    .from("drive_documents")
    .select("*", { count: "exact", head: true })
    .is("content", null);

  return { indexed: rows.length, extracted, remaining: remaining ?? 0 };
}
