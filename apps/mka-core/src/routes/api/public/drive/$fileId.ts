import { createFileRoute } from "@tanstack/react-router";
import { downloadDriveFile } from "@/lib/drive-sync.server";

// Streams a file from the indexed Drive folder. Only files already indexed are served.
export const Route = createFileRoute("/api/public/drive/$fileId")({
  server: {
    handlers: {
      GET: async ({ params }) => {
        if (!/^[\w-]{10,100}$/.test(params.fileId)) return new Response("Bad id", { status: 400 });
        const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
        const { data } = await supabaseAdmin
          .from("drive_documents")
          .select("id, name, mime_type")
          .eq("id", params.fileId)
          .maybeSingle();
        if (!data) return new Response("Not found", { status: 404 });
        try {
          const upstream = await downloadDriveFile(data.id, data.mime_type ?? "");
          const type = data.mime_type?.startsWith("application/vnd.google-apps")
            ? upstream.headers.get("content-type") ?? "application/pdf"
            : data.mime_type ?? "application/octet-stream";
          return new Response(upstream.body, {
            headers: {
              "content-type": type.includes("text/") ? `${type.split(";")[0]}; charset=utf-8` : type,
              "content-disposition": `inline; filename*=UTF-8''${encodeURIComponent(data.name)}`,
              "cache-control": "public, max-age=3600",
            },
          });
        } catch (error) {
          return new Response((error as Error).message, { status: 502 });
        }
      },
    },
  },
});
