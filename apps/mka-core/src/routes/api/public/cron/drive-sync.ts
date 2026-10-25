import { createFileRoute } from "@tanstack/react-router";
import { authenticateCronRequest } from "@/integrations/supabase/cron-auth";
import { syncDrive } from "@/lib/drive-sync.server";

export const Route = createFileRoute("/api/public/cron/drive-sync")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        // Accept the cron secret, or the project key used by the database scheduler.
        // Sync is idempotent (re-reads Drive, fills missing text) so the key only screens stray traffic.
        const bearer = request.headers.get("authorization")?.replace(/^Bearer\s+/, "");
        const isSchedulerKey = !!bearer && bearer === process.env["SUPABASE_PUBLISHABLE_KEY"];
        if (!isSchedulerKey) {
          const denied = await authenticateCronRequest(request);
          if (denied) return denied;
        }
        try {
          const result = await syncDrive({ ocrLimit: 60 });
          return Response.json(result);
        } catch (error) {
          return Response.json({ error: (error as Error).message }, { status: 500 });
        }
      },
    },
  },
});
