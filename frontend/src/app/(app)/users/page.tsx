import Link from 'next/link'

import { Pagination } from '@/components/pagination'
import { timeAgo } from '@/lib/format'
import { listUsers, type UserSort } from '@/lib/users'

const SORTS: { key: UserSort; label: string }[] = [
  { key: 'reputation', label: 'İtibar' },
  { key: 'joined', label: 'Yeni' },
  { key: 'username', label: 'A → Z' },
]

const SEARCH_MAX = 64

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; sort?: string; search?: string }>
}) {
  const sp = await searchParams
  const page = Math.max(1, Number(sp.page) || 1)
  const sort = SORTS.find((s) => s.key === sp.sort)?.key ?? 'reputation'
  const search = sp.search?.trim().slice(0, SEARCH_MAX) || undefined

  const data = await listUsers({ page, sort, search })

  const hrefWith = (next: { sort?: UserSort; page?: number }) => {
    const params = new URLSearchParams()
    const s = next.sort ?? sort
    const p = next.page ?? 1
    if (s !== 'reputation') params.set('sort', s)
    if (search) params.set('search', search)
    if (p > 1) params.set('page', String(p))
    const qs = params.toString()
    return qs ? `/users?${qs}` : '/users'
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Kullanıcılar</h1>
        <span className="text-sm text-neutral-500 dark:text-neutral-400">
          {data.total} kullanıcı
        </span>
      </div>

      <form
        action="/users"
        method="get"
        role="search"
        className="mt-5 flex gap-2"
      >
        <input
          type="search"
          name="search"
          defaultValue={search}
          placeholder="Kullanıcı ara…"
          maxLength={SEARCH_MAX}
          aria-label="Kullanıcı ara"
          className="w-full max-w-sm rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm placeholder:text-neutral-400 focus:border-neutral-500 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:placeholder:text-neutral-500"
        />
        {sort !== 'reputation' && <input type="hidden" name="sort" value={sort} />}
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
          {search ? 'Eşleşen kullanıcı bulunamadı.' : 'Henüz kullanıcı yok.'}
        </p>
      ) : (
        <ul className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((u) => (
            <li
              key={u.id}
              className="rounded-lg border border-neutral-200 p-4 hover:border-neutral-300 dark:border-neutral-800 dark:hover:border-neutral-700"
            >
              <Link
                href={`/users/${encodeURIComponent(u.username)}`}
                className="font-medium text-neutral-900 hover:underline dark:text-neutral-100"
              >
                {u.username}
              </Link>
              <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
                <span className="font-medium text-neutral-700 dark:text-neutral-300">
                  {u.reputation}
                </span>{' '}
                itibar · {u.question_count} soru · {u.answer_count} cevap
              </p>
              {u.bio && (
                <p className="mt-2 line-clamp-2 text-sm text-neutral-600 dark:text-neutral-400">
                  {u.bio}
                </p>
              )}
              <p className="mt-3 text-[11px] text-neutral-500 dark:text-neutral-500">
                {timeAgo(u.joined_at)} katıldı
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
