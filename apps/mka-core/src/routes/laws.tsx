import { createFileRoute, Link } from "@tanstack/react-router";
import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import { listBooks } from "@/lib/library.functions";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { PdfButton } from "@/components/PdfButton";

const booksQueryOptions = queryOptions({
  queryKey: ["books"],
  queryFn: () => listBooks(),
});

export const Route = createFileRoute("/laws")({
  head: () => ({
    meta: [
      { title: "فهرست قوانین مالیاتی ایران" },
      {
        name: "description",
        content:
          "فهرست دسته‌بندی‌شده قوانین مالیاتی ایران به همراه تعداد مواد ذخیره‌شده و متن کامل هر ماده.",
      },
      { property: "og:title", content: "فهرست قوانین مالیاتی ایران" },
      {
        property: "og:description",
        content: "قوانین مالیاتی ایران به تفکیک دسته‌بندی با متن کامل مواد",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(booksQueryOptions),
  errorComponent: ({ error }: { error: unknown }) => (
    <div className="mx-auto max-w-3xl p-8 text-sm text-destructive">{(error as Error).message}</div>
  ),
  notFoundComponent: () => <div className="mx-auto max-w-3xl p-8 text-sm">یافت نشد.</div>,
  component: LawsPage,
});

function LawsPage() {
  const { data } = useSuspenseQuery(booksQueryOptions);

  const grouped = data.books.reduce<Record<string, typeof data.books>>((acc, book) => {
    const key = book.category ?? "سایر";
    (acc[key] ??= []).push(book);
    return acc;
  }, {});

  return (
    <div className="min-h-screen">
      <SiteHeader />

      <header className="print-header bg-gradient-header text-primary-foreground">
        <div className="mx-auto max-w-6xl px-5 py-12">
          <h1 className="text-2xl font-bold sm:text-3xl">قوانین مالیاتی</h1>
          <p className="mt-3 max-w-2xl text-sm leading-8 opacity-90">
            {data.books.length.toLocaleString("fa-IR")} قانون و{" "}
            {data.totalArticles.toLocaleString("fa-IR")} ماده ذخیره‌شده. روی هر قانون بزنید تا فهرست
            و متن کامل مواد آن را ببینید.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-10">
        <div className="mb-6 flex flex-wrap gap-3">
          <PdfButton
            variant="primary"
            fileName="فهرست قوانین مالیاتی"
            label="دانلود PDF فهرست قوانین"
          />
        </div>

        {data.books.length === 0 && (
          <p className="text-sm text-muted-foreground">
            هنوز قانونی ذخیره نشده است. از پنل مدیریت محتوا، فهرست قوانین را دریافت کنید.
          </p>
        )}

        <div className="space-y-8">
          {Object.entries(grouped).map(([category, books]) => (
            <section key={category}>
              <h2 className="mb-3 border-b border-border pb-2 text-base font-semibold text-primary">
                {category}
                <span className="mr-2 text-xs font-normal text-muted-foreground">
                  ({books.length.toLocaleString("fa-IR")} قانون)
                </span>
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {books.map((book) => (
                  <Link
                    key={book.source_id}
                    to="/books/$sourceId"
                    params={{ sourceId: book.source_id }}
                    className="panel p-4 transition-transform hover:-translate-y-0.5"
                  >
                    <div className="text-sm font-semibold leading-7">{book.title}</div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {book.articles_count > 0
                        ? `${book.articles_count.toLocaleString("fa-IR")} ماده`
                        : "متن مواد ذخیره نشده"}
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
