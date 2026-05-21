import Link from 'next/link'

import { Pagination } from '@/components/pagination'
import { listTags, type TagSort } from '@/lib/tags'

const SORTS: { key: TagSort; label: string }[] = [
  { key: 'questions', label: 'Popüler' },
  { key: 'name', label: 'A → Z' },
]

const SEARCH_MAX = 64

export default async function TagsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; sort?: string; search?: string }>
}) {
  const sp = await searchParams
  const page = Math.max(1, Number(sp.page) || 1)
  const sort = SORTS.find((s) => s.key === sp.sort)?.key ?? 'questions'
  const search = sp.search?.trim().slice(0, SEARCH_MAX) || undefined

  const data = await listTags({ page, sort, search })

  const hrefWith = (next: { sort?: TagSort; page?: number; search?: string | null }) => {
    const params = new URLSearchParams()
    const s = next.sort ?? sort
    const p = next.page ?? 1
    const sr = next.search === null ? undefined : (next.search ?? search)
    if (s !== 'questions') params.set('sort', s)
    if (sr) params.set('search', sr)
    if (p > 1) params.set('page', String(p))
    const qs = params.toString()
    return qs ? `/tags?${qs}` : '/tags'
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Etiketler</h1>
        <span className="text-sm text-neutral-500 dark:text-neutral-400">
          {data.total} etiket
        </span>
      </div>

      <p className="mt-2 max-w-2xl text-sm text-neutral-600 dark:text-neutral-400">
        Bir etiket, sorunun konusunu özetler. Aradığını bulmak için arama kutusunu
        kullan ya da etikete tıklayıp ilgili soruları gör.
      </p>

      <form
        action="/tags"
        method="get"
        role="search"
        className="mt-5 flex gap-2"
      >
        <input
          type="search"
          name="search"
          defaultValue={search}
          placeholder="Etiket ara (ör. python)…"
          maxLength={SEARCH_MAX}
          aria-label="Etiket ara"
          className="w-full max-w-sm rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm placeholder:text-neutral-400 focus:border-neutral-500 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:placeholder:text-neutral-500"
        />
        {sort !== 'questions' && <input type="hidden" name="sort" value={sort} />}
      </form>

      <div className="mt-4 flex gap-1 border-b border-neutral-200 dark:border-neutral-800">
        {SORTS.map((s) => (
          <Link
            key={s.key}
            href={hrefWith({ sort: s.key, page: 1 })}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${
              s.key === sort
                ? 'border-neutral-900 font-medium dark:border-neutral-100'
                : 'border-transparent text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200'
            }`}
          >
            {s.label}
          </Link>
        ))}
      </div>

      {data.items.length === 0 ? (
        <p className="py-16 text-center text-neutral-500 dark:text-neutral-400">
          {search ? 'Eşleşen etiket bulunamadı.' : 'Henüz etiket yok.'}
        </p>
      ) : (
        <ul className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((t) => (
            <li
              key={t.id}
              className="rounded-lg border border-neutral-200 p-4 hover:border-neutral-300 dark:border-neutral-800 dark:hover:border-neutral-700"
            >
              <Link
                href={`/questions?tag=${encodeURIComponent(t.name)}`}
                className="inline-block rounded bg-blue-50 px-2 py-0.5 text-sm font-medium text-blue-700 hover:bg-blue-100 dark:bg-blue-950 dark:text-blue-300 dark:hover:bg-blue-900"
              >
                {t.name}
              </Link>
              {t.description && (
                <p className="mt-2 line-clamp-3 text-sm text-neutral-600 dark:text-neutral-400">
                  {t.description}
                </p>
              )}
              <p className="mt-3 text-xs text-neutral-500 dark:text-neutral-500">
                {t.question_count} soru
              </p>
            </li>
          ))}
        </ul>
      )}

      <Pagination
        page={data.page}
        pageSize={data.page_size}
        total={data.total}
        makeHref={(p) => hrefWith({ page: p })}
      />
    </main>
  )
}
