import { createFileRoute } from "@tanstack/react-router";
import { queryOptions, useMutation, useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useServerFn } from "@tanstack/react-start";
import {
  listBooks,
  scrapeBook,
  scrapeCirculars,
  syncBooks,
  syncCircularList,
  triggerDriveSync,
  checkIsAdmin,
} from "@/lib/library.functions";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";

const booksQueryOptions = queryOptions({
  queryKey: ["books"],
  queryFn: () => listBooks(),
});

export const Route = createFileRoute("/_authenticated/admin")({
  head: () => ({
    meta: [
      { title: "پنل مدیریت محتوا — کتابخانه قوانین مالیاتی" },
      {
        name: "description",
        content: "دریافت فهرست قوانین و بخشنامه‌ها و ذخیره متن کامل اسناد در پایگاه داده.",
      },
      { property: "og:title", content: "پنل مدیریت محتوا" },
      { property: "og:description", content: "به‌روزرسانی آرشیو قوانین و بخشنامه‌های مالیاتی" },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "robots", content: "noindex" },
    ],
  }),
  loader: async ({ context }) => {
    await checkIsAdmin();
    return context.queryClient.ensureQueryData(booksQueryOptions);
  },
  errorComponent: ({ error }: { error: unknown }) => (
    <div className="mx-auto max-w-3xl p-8 text-sm text-destructive">{(error as Error).message}</div>
  ),
  notFoundComponent: () => <div className="mx-auto max-w-3xl p-8 text-sm">یافت نشد.</div>,
  component: AdminPage,
});

function AdminPage() {
  const { data } = useSuspenseQuery(booksQueryOptions);
  const [log, setLog] = useState<string[]>([]);

  const syncBooksFn = useServerFn(syncBooks);
  const scrapeBookFn = useServerFn(scrapeBook);
  const syncCircularsFn = useServerFn(syncCircularList);
  const scrapeCircularsFn = useServerFn(scrapeCirculars);

  const driveSyncFn = useServerFn(triggerDriveSync);
  const driveSync = useMutation({
    mutationFn: async () => {
      const r = await driveSyncFn({});
      addLog(`گوگل درایو: ${r.indexed} فایل ثبت شد، متن ${r.extracted} فایل خوانده شد، ${r.remaining} فایل در انتظار`);
    },
  });

  const addLog = (line: string) => setLog((prev) => [line, ...prev].slice(0, 20));

  const syncLaws = useMutation({
    mutationFn: async () => {
      const result = await syncBooksFn({});
      addLog(`فهرست قوانین: ${result.saved} قانون مالیاتی از ${result.found} مورد ذخیره شد`);
      window.location.reload();
    },
  });

  const scrapeLaws = useMutation({
    mutationFn: async () => {
      for (const book of data.books) {
        let guard = 0;
        for (;;) {
          const result = await scrapeBookFn({ data: { sourceId: book.source_id, batchSize: 20 } });
          addLog(`${book.title}: ${result.total - result.remaining} از ${result.total} ماده ذخیره شد`);
          if (result.remaining === 0 || result.scraped === 0 || ++guard > 40) break;
        }
      }
      window.location.reload();
    },
  });

  const syncCirculars = useMutation({
    mutationFn: async () => {
      const result = await syncCircularsFn({ data: {} });
      addLog(`فهرست بخشنامه‌ها: ${result.total} بخشنامه در پایگاه داده`);
    },
  });

  const scrapeAllCirculars = useMutation({
    mutationFn: async () => {
      let guard = 0;
      for (;;) {
        const result = await scrapeCircularsFn({ data: { batchSize: 20 } });
        addLog(`${result.scraped} بخشنامه ذخیره شد — ${result.remaining} مورد باقی مانده`);
        if (result.remaining === 0 || result.scraped === 0 || ++guard > 500) break;
      }
    },
  });

  const busy =
    syncLaws.isPending ||
    scrapeLaws.isPending ||
    syncCirculars.isPending ||
    scrapeAllCirculars.isPending;

  const error =
    syncLaws.error ?? scrapeLaws.error ?? syncCirculars.error ?? scrapeAllCirculars.error;

  return (
    <div className="min-h-screen">
      <SiteHeader />
      <header className="bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-4xl px-5 py-12">
          <h1 className="text-2xl font-bold sm:text-3xl">پنل مدیریت محتوا</h1>
          <p className="mt-3 max-w-2xl text-sm leading-8 opacity-90">
            دریافت فهرست و ذخیره متن کامل اسناد. عملیات دسته‌ای است و می‌توانید آن را ادامه دهید.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-5 py-10">
        <section className="panel mb-4 border-gold/50 p-6">
          <h2 className="text-base font-semibold">مخزن اسناد گوگل درایو (منبع اول)</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            هر روز خودکار به‌روز می‌شود. با هر بار زدن دکمه، فهرست فایل‌ها تازه و متن چند فایل دیگر خوانده می‌شود.
          </p>
          <button
            onClick={() => driveSync.mutate()}
            disabled={driveSync.isPending}
            className="mt-4 h-10 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {driveSync.isPending ? "در حال به‌روزرسانی از درایو…" : "به‌روزرسانی از گوگل درایو"}
          </button>
          {driveSync.error && <p className="mt-3 text-sm text-destructive">{driveSync.error.message}</p>}
        </section>

        <section className="panel p-6">
          <h2 className="text-base font-semibold">قوانین و مواد قانونی</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              onClick={() => syncLaws.mutate()}
              disabled={busy}
              className="h-10 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {syncLaws.isPending ? "در حال دریافت فهرست…" : "۱) دریافت فهرست قوانین"}
            </button>
            <button
              onClick={() => scrapeLaws.mutate()}
              disabled={busy || data.books.length === 0}
              className="h-10 rounded-lg bg-gold px-5 text-sm font-medium text-gold-foreground disabled:opacity-50"
            >
              {scrapeLaws.isPending ? "در حال استخراج مواد…" : "۲) استخراج متن کامل مواد"}
            </button>
          </div>
        </section>

        <section className="panel mt-4 p-6">
          <h2 className="text-base font-semibold">بخشنامه‌ها</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              onClick={() => syncCirculars.mutate()}
              disabled={busy}
              className="h-10 rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {syncCirculars.isPending ? "در حال دریافت فهرست…" : "۱) دریافت فهرست بخشنامه‌ها"}
            </button>
            <button
              onClick={() => scrapeAllCirculars.mutate()}
              disabled={busy}
              className="h-10 rounded-lg bg-gold px-5 text-sm font-medium text-gold-foreground disabled:opacity-50"
            >
              {scrapeAllCirculars.isPending ? "در حال استخراج متن…" : "۲) استخراج متن بخشنامه‌ها"}
            </button>
          </div>
        </section>

        {error && <p className="mt-4 text-sm text-destructive">{(error as Error).message}</p>}

        {log.length > 0 && (
          <ul className="panel mt-4 space-y-1 p-5 text-xs text-muted-foreground">
            {log.map((line, index) => (
              <li key={index}>• {line}</li>
            ))}
          </ul>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
