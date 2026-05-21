import Link from 'next/link'

import { Pagination } from '@/components/pagination'
import { QuestionCard } from '@/components/question-card'
import { SearchBox } from '@/components/search-box'
import { listQuestions, type QuestionSort } from '@/lib/questions'

const SORTS: { key: QuestionSort; label: string }[] = [
  { key: 'created', label: 'Yeni' },
  { key: 'votes', label: 'Oy' },
  { key: 'answers', label: 'Cevap' },
  { key: 'views', label: 'Görüntüleme' },
]

const Q_MAX = 80

export default async function QuestionsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; sort?: string; tag?: string; q?: string }>
}) {
  const sp = await searchParams
  const page = Math.max(1, Number(sp.page) || 1)
  const sort = SORTS.find((s) => s.key === sp.sort)?.key ?? 'created'
  const tag = sp.tag
  // q'yu kısalt — backend zaten 80 karakteri kabul ediyor.
  const q = sp.q?.trim().slice(0, Q_MAX) || undefined

  const data = await listQuestions({ page, sort, tag, q })

  const hrefWith = (next: { sort?: QuestionSort; page?: number }) => {
    const params = new URLSearchParams()
    const s = next.sort ?? sort
    const p = next.page ?? 1
    if (s !== 'created') params.set('sort', s)
    if (tag) params.set('tag', tag)
    if (q) params.set('q', q)
    if (p > 1) params.set('page', String(p))
    const qs = params.toString()
    return qs ? `/questions?${qs}` : '/questions'
  }

  let heading: string
  if (q && tag) heading = `#${tag} içinde "${q}"`
  else if (q) heading = `"${q}" için sonuçlar`
  else if (tag) heading = `#${tag} soruları`
  else heading = 'Tüm sorular'

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="min-w-0 truncate text-2xl font-semibold">{heading}</h1>
        <span className="text-sm text-neutral-500 dark:text-neutral-400">
          {data.total} sonuç
        </span>
      </div>

      <div className="mt-4">
        <SearchBox defaultValue={q} className="max-w-md" />
      </div>

      <div className="mt-4 flex gap-1 border-b border-neutral-200 dark:border-neutral-800">
        {SORTS.map((s) => (
          <Link
            key={s.key}
            href={hrefWith({ sort: s.key })}
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
          {q ? 'Aramanla eşleşen soru bulunamadı.' : 'Henüz soru yok.'}
        </p>
      ) : (
        <div>
          {data.items.map((qq) => (
            <QuestionCard key={qq.id} q={qq} />
          ))}
        </div>
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
