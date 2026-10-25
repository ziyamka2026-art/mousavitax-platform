/**
 * Drive File Picker — server-side functions for browsing + selecting
 * files from the user's connected Google Drive.
 *
 * Fixes the issue where the registration form only accepted a manual URL
 * paste — now users can search and pick files directly from Drive.
 *
 * @package apps.mka-core.src.lib.drive-picker.functions
 */

import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { z } from "zod";

const GATEWAY = "https://connector-gateway.lovable.dev/google_drive/drive/v3";

interface DriveFileMeta {
  id: string;
  name: string;
  mimeType: string;
  webViewLink?: string;
  iconLink?: string;
  modifiedTime?: string;
  size?: string;
  parents?: string[];
}

function driveHeaders(): HeadersInit {
  const lovable = process.env["LOVABLE_API_KEY"];
  const conn = process.env["GOOGLE_DRIVE_API_KEY"];
  if (!lovable || !conn) {
    throw new Error("اتصال گوگل درایو پیکربندی نشده است — LOVABLE_API_KEY یا GOOGLE_DRIVE_API_KEY موجود نیست.");
  }
  return {
    Authorization: `Bearer ${lovable}`,
    "X-Connection-Api-Key": conn,
  };
}

async function driveFetch(
  path: string,
  params?: Record<string, string>,
  timeoutMs: number = 15000,
): Promise<Response> {
  const url = new URL(`${GATEWAY}${path}`);
  for (const [k, v] of Object.entries(params ?? {})) {
    url.searchParams.set(k, v);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let res: Response;
  let attempt = 0;
  const MAX_RETRIES = 3;

  do {
    attempt += 1;
    try {
      res = await fetch(url.toString(), {
        headers: driveHeaders(),
        signal: controller.signal,
      });
      if (res.status !== 429 && res.status < 500) break;
    } catch (err) {
      if (attempt >= MAX_RETRIES) {
        clearTimeout(timeoutId);
        throw new Error(`Drive API unreachable: ${(err as Error).message}`);
      }
    }
    if (attempt < MAX_RETRIES) {
      await new Promise((r) => setTimeout(r, 800 * attempt));
    }
  } while (attempt < MAX_RETRIES);

  clearTimeout(timeoutId);

  if (!res!.ok) {
    const body = await res!.text();
    throw new Error(`Google Drive [${res!.status}]: ${body.slice(0, 300)}`);
  }
  return res!;
}

/**
 * List files in a specific Drive folder (defaults to root Tax folder).
 * Supports pagination + filtering by MIME type.
 *
 * Usage from client:
 *   const files = await listDriveFiles({ folderId, mimeType: 'application/pdf' });
 */
export const listDriveFiles = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z
      .object({
        folderId: z.string().optional(),
        mimeType: z.string().optional(),
        query: z.string().optional(),
        pageSize: z.number().int().min(1).max(200).default(50),
        pageToken: z.string().optional(),
      })
      .parse(input ?? {}),
  )
  .handler(async ({ data }) => {
    const folderId = data.folderId ?? "1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del";

    let q = `'${folderId}' in parents and trashed=false`;
    if (data.mimeType) {
      q += ` and mimeType='${data.mimeType}'`;
    }
    if (data.query && data.query.trim().length > 1) {
      q += ` and name contains '${data.query.trim().replace(/'/g, "\\'")}'`;
    }

    const res = await driveFetch("/files", {
      q,
      fields: "nextPageToken,files(id,name,mimeType,webViewLink,iconLink,modifiedTime,size,parents)",
      pageSize: String(data.pageSize),
      supportsAllDrives: "true",
      includeItemsFromAllDrives: "true",
      orderBy: "modifiedTime desc",
      ...(data.pageToken ? { pageToken: data.pageToken } : {}),
    });

    const json = (await res.json()) as {
      files: DriveFileMeta[];
      nextPageToken?: string;
    };

    return {
      files: (json.files ?? []).map((f) => ({
        id: f.id,
        name: f.name,
        mimeType: f.mimeType,
        webViewLink: f.webViewLink ?? null,
        iconLink: f.iconLink ?? null,
        modifiedTime: f.modifiedTime ?? null,
        size: f.size ? Number(f.size) : null,
        parentFolderId: f.parents?.[0] ?? folderId,
      })),
      nextPageToken: json.nextPageToken ?? null,
      folderId,
    };
  });

/**
 * Search across all of the user's Drive (not just one folder).
 * Useful for finding a specific file by name when you don't know where it lives.
 */
export const searchDriveFiles = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z
      .object({
        query: z.string().min(2).max(200),
        pageSize: z.number().int().min(1).max(50).default(20),
      })
      .parse(input ?? {}),
  )
  .handler(async ({ data }) => {
    const q = `name contains '${data.query.replace(/'/g, "\\'")}' and trashed=false`;
    const res = await driveFetch("/files", {
      q,
      fields: "files(id,name,mimeType,webViewLink,iconLink,modifiedTime,size,parents)",
      pageSize: String(data.pageSize),
      supportsAllDrives: "true",
      includeItemsFromAllDrives: "true",
      orderBy: "modifiedTime desc",
    });

    const json = (await res.json()) as { files: DriveFileMeta[] };
    return {
      files: (json.files ?? []).map((f) => ({
        id: f.id,
        name: f.name,
        mimeType: f.mimeType,
        webViewLink: f.webViewLink ?? null,
        iconLink: f.iconLink ?? null,
        modifiedTime: f.modifiedTime ?? null,
        size: f.size ? Number(f.size) : null,
      })),
      query: data.query,
    };
  });

/**
 * List Drive folders (only folders, no files). Used to build a folder
 * tree browser in the UI.
 */
export const listDriveFolders = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z
      .object({
        folderId: z.string().optional(),
      })
      .parse(input ?? {}),
  )
  .handler(async ({ data }) => {
    const folderId = data.folderId ?? "1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del";
    const q = `'${folderId}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'`;

    const res = await driveFetch("/files", {
      q,
      fields: "files(id,name,modifiedTime,iconLink)",
      pageSize: "100",
      supportsAllDrives: "true",
      includeItemsFromAllDrives: "true",
      orderBy: "name",
    });

    const json = (await res.json()) as { files: DriveFileMeta[] };
    return {
      folders: (json.files ?? []).map((f) => ({
        id: f.id,
        name: f.name,
        modifiedTime: f.modifiedTime ?? null,
        iconLink: f.iconLink ?? null,
      })),
      parentFolderId: folderId,
    };
  });

/**
 * Get file metadata by ID — used when user pastes a Drive link and we
 * need to verify the file exists and fetch its name.
 */
export const getDriveFileMeta = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) =>
    z.object({ fileId: z.string() }).parse(input ?? {}),
  )
  .handler(async ({ data }) => {
    try {
      const res = await driveFetch(`/files/${data.fileId}`, {
        fields: "id,name,mimeType,webViewLink,iconLink,modifiedTime,size,parents",
        supportsAllDrives: "true",
      });
      const f = (await res.json()) as DriveFileMeta;
      return {
        file: {
          id: f.id,
          name: f.name,
          mimeType: f.mimeType,
          webViewLink: f.webViewLink ?? null,
          iconLink: f.iconLink ?? null,
          modifiedTime: f.modifiedTime ?? null,
          size: f.size ? Number(f.size) : null,
          parentFolderId: f.parents?.[0] ?? null,
        },
      };
    } catch (err) {
      return {
        file: null,
        error: (err as Error).message,
      };
    }
  });

/**
 * Health check — verifies Drive connection is working without fetching
 * any actual files. Useful for the UI to show a green/red status badge.
 */
export const checkDriveHealth = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async () => {
    const start = Date.now();
    try {
      const res = await driveFetch("/files", {
        q: "'1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del' in parents and trashed=false",
        pageSize: "1",
        fields: "files(id)",
        supportsAllDrives: "true",
      }, 8000);
      const json = (await res.json()) as { files: DriveFileMeta[] };
      return {
        status: "ok" as const,
        reachable: true,
        latencyMs: Date.now() - start,
        sampleFileFound: (json.files ?? []).length > 0,
      };
    } catch (err) {
      return {
        status: "error" as const,
        reachable: false,
        latencyMs: Date.now() - start,
        error: (err as Error).message,
      };
    }
  });
