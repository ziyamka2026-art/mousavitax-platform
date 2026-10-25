import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { searchAll } from "@/lib/library.functions";
import { searchOfficial } from "@/lib/official-search.functions";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { PdfButton } from "@/components/PdfButton";

type SearchParams = { q: string; type: string; page: number };

function validateSearch(
  input: Partial<Record<keyof SearchParams, unknown>>,
): SearchParams {
  const rawPage = Number(input['page']);
  return {
    q: typeof input['q'] === "string" ? input['q'] : "",
    type: typeof input['type'] === "string" ? input['type'] : "all",
    page: Number.isFinite(rawPage) ? Math.trunc(rawPage) : 0,
  };
}

export const Route = createFileRoute("/search")({
  validateSearch,
  head: () => ({
    meta: [
      { title: "جستجوی پیشرفته در قوانین و بخشنامه‌های مالیاتی" },
      {
        name: "description",
        content:
          "جستجوی متن کامل در مواد قانونی و بخشنامه‌های مالیاتی با فیلتر نوع سند و صفحه‌بندی نتایج.",
      },
      { property: "og:title", content: "جستجوی پیشرفته در قوانین و بخشنامه‌های مالیاتی" },
      {
        property: "og:description",
        content: "جستجوی متن کامل در مواد قانونی و بخشنامه‌های مالیاتی",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  errorComponent: ({ error }: { error: unknown }) => (
    <div className="mx-auto max-w-3xl p-8 text-sm text-destructive">{(error as Error).message}</div>
  ),
  notFoundComponent: () => <div className="mx-auto max-w-3xl p-8 text-sm">یافت نشد.</div>,
  component: SearchPage,
});

const TYPES = [
  { value: "all", label: "همه اسناد" },
  { value: "drive", label: "مخزن اسناد" },
  { value: "official", label: "منابع رسمی (امور مالیاتی و مجلس)" },
  { value: "articles", label: "مواد قانونی" },
  { value: "circulars", label: "بخشنامه‌ها" },
] as const;

function highlight(text: string, term: string) {
  if (!term || !text) return text;
  const index = text.toLowerCase().indexOf(term.toLowerCase());
  if (index === -1) return text;
  return (
    <>
      {text.slice(0, index)}
      <mark className="rounded bg-gold/60 px-0.5 text-gold-foreground">
        {text.slice(index, index + term.length)}
      </mark>
      {text.slice(index + term.length)}
    </>
  );
}

function SearchPage() {
  const { q, type, page } = Route.useSearch();
  const navigate = useNavigate({ from: "/search" });
  const [term, setTerm] = useState(q);
  const safeType = TYPES.some((item) => item.value === type) ? type : "all";
  const safePage = Math.max(0, Math.min(500, page));

  const results = useQuery({
    queryKey: ["search-all", q, safeType, safePage],
    queryFn: () => searchAll({ data: { q, type: safeType, page: safePage } }),
    enabled: q.trim().length > 1 && safeType !== "official",
  });

  const wantOfficial = q.trim().length > 1 && (safeType === "all" || safeType === "official");
  const official = useQuery({
    queryKey: ["search-official", q],
    queryFn: () => searchOfficial({ data: { q: q.trim() } }),
    enabled: wantOfficial,
    staleTime: 10 * 60 * 1000,
    retry: false,
  });

  const data = results.data;
  const pages = data ? Math.ceil(data.total / data.size) : 0;

  return (
    <div className="min-h-screen">
      <SiteHeader />

      <header className="print-header bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-5xl px-5 py-10">
          <h1 className="text-xl font-bold sm:text-2xl">جستجوی پیشرفته</h1>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              navigate({ search: { q: term.trim(), type: safeType, page: 0 } });
            }}
            className="no-print mt-5 flex flex-col gap-3 sm:flex-row"
          >
            <input
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              placeholder="عبارت، شماره ماده یا شماره بخشنامه…"
              aria-label="عبارت جستجو"
              className="h-12 flex-1 rounded-xl border border-white/20 bg-white/95 px-5 text-sm text-foreground outline-none focus:ring-2 focus:ring-gold"
            />
            <button
              type="submit"
              className="h-12 rounded-xl bg-gold px-8 text-sm font-semibold text-gold-foreground hover:opacity-90"
            >
              جستجو
            </button>
          </form>

          <div className="no-print mt-4 flex flex-wrap gap-2">
            {TYPES.map((item) => (
              <button
                key={item.value}
                onClick={() =>
                  navigate({ search: { q, type: item.value, page: 0 } })
                }
                className={`h-9 rounded-lg px-4 text-xs transition-colors ${
                  safeType === item.value
                    ? "bg-white/95 font-semibold text-primary"
                    : "bg-white/10 hover:bg-white/20"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-10">
        {q.trim().length < 2 && (
          <p className="text-sm text-muted-foreground">
            برای شروع، عبارتی با حداقل دو حرف جستجو کنید.
          </p>
        )}

        {wantOfficial && (
          <section className="panel mb-8 border-gold/50 p-5">
            <h2 className="text-base font-semibold">نتایج رسمی: سازمان امور مالیاتی و پایگاه قوانین مجلس</h2>
            {official.isLoading && (
              <p className="mt-3 text-sm text-muted-foreground">در حال جستجو در سایت‌های رسمی… (چند ثانیه)</p>
            )}
            {official.data?.error && <p className="mt-3 text-sm text-destructive">{official.data.error}</p>}
            {official.isError && <p className="mt-3 text-sm text-destructive">جستجو در منابع رسمی فعلاً ممکن نیست.</p>}
            {official.data && !official.data.error && official.data.results.length === 0 && (
              <p className="mt-3 text-sm text-muted-foreground">نتیجه رسمی برای این عبارت یافت نشد.</p>
            )}
            <ul className="mt-3 space-y-3">
              {official.data?.results.map((hit) => (
                <li key={hit.url} className="rounded-lg border p-3">
                  <span className="rounded bg-gold/30 px-2 py-0.5 text-xs">{hit.site}</span>
                  <a href={hit.url} target="_blank" rel="noopener noreferrer" className="mt-2 block font-medium text-primary hover:underline">
                    {hit.title}
                  </a>
                  {hit.summary && <p className="mt-1 text-sm text-muted-foreground">{hit.summary}</p>}
                  <p className="mt-1 truncate text-xs text-muted-foreground" dir="ltr">{hit.url}</p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {safeType !== "official" && results.isLoading && <p className="text-sm text-muted-foreground">در حال جستجو…</p>}

        {safeType !== "official" && data && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground">
                {data.total.toLocaleString("fa-IR")} نتیجه برای «{data.term}»
              </p>
              {data.total > 0 && (
                <PdfButton
                  variant="primary"
                  fileName={`نتایج جستجو — ${data.term}`}
                  label="دانلود PDF نتایج"
                />
              )}
            </div>

            <section className="mt-5 space-y-3">
              {data.total === 0 && (
                <p className="text-sm text-muted-foreground">
                  نتیجه‌ای یافت نشد. عبارت کوتاه‌تری را امتحان کنید.
                </p>
              )}

              {data.results.map((hit) =>
                hit.kind === "drive" ? (
                  <a
                    key={hit.key}
                    href={`/api/public/drive/${hit.sourceId}`}
                    target="_blank"
                    rel="noreferrer"
                    className="panel block border-gold/50 p-4 transition-transform hover:-translate-y-0.5"
                  >
                    <ResultBody hit={hit} term={data.term} badge="مخزن اسناد" />
                  </a>
                ) : hit.kind === "article" ? (
                  <Link
                    key={hit.key}
                    to="/books/$sourceId"
                    params={{ sourceId: hit.bookSourceId ?? "" }}
                    hash={hit.sourceId}
                    className="panel block p-4 transition-transform hover:-translate-y-0.5"
                  >
                    <ResultBody hit={hit} term={data.term} badge="ماده قانونی" />
                  </Link>
                ) : (
                  <Link
                    key={hit.key}
                    to="/circulars/$sourceId"
                    params={{ sourceId: hit.sourceId }}
                    className="panel block p-4 transition-transform hover:-translate-y-0.5"
                  >
                    <ResultBody hit={hit} term={data.term} badge="بخشنامه" />
                  </Link>
                ),
              )}

              {pages > 1 && (
                <div className="no-print flex items-center justify-center gap-3 pt-4 text-sm">
                  <button
                    onClick={() =>
                      navigate({ search: { q, type: safeType, page: Math.max(0, safePage - 1) } })
                    }
                    disabled={safePage === 0}
                    className="h-9 rounded-lg border border-border px-4 disabled:opacity-40"
                  >
                    قبلی
                  </button>
                  <span className="text-muted-foreground">
                    صفحه {(safePage + 1).toLocaleString("fa-IR")} از {pages.toLocaleString("fa-IR")}
                  </span>
                  <button
                    onClick={() => navigate({ search: { q, type: safeType, page: safePage + 1 } })}
                    disabled={safePage + 1 >= pages}
                    className="h-9 rounded-lg border border-border px-4 disabled:opacity-40"
                  >
                    بعدی
                  </button>
                </div>
              )}
            </section>
          </>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}

function ResultBody({
  hit,
  term,
  badge,
}: {
  hit: { title: string; meta: string; snippet: string };
  term: string;
  badge: string;
}) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <span className="rounded bg-secondary px-2 py-0.5 text-secondary-foreground">{badge}</span>
        <span>{hit.meta}</span>
      </div>
      <div className="mt-2 text-sm font-semibold leading-7">{highlight(hit.title, term)}</div>
      {hit.snippet && (
        <p className="mt-2 text-xs leading-6 text-muted-foreground">
          {highlight(hit.snippet, term)}
        </p>
      )}
    </>
  );
}
