import Link from 'next/link'

import { Pagination } from '@/components/pagination'
import { QuestionCard } from '@/components/question-card'
import { listQuestions, type QuestionSort } from '@/lib/questions'

const SORTS: { key: QuestionSort; label: string }[] = [
  { key: 'created', label: 'Yeni' },
  { key: 'votes', label: 'Oy' },
  { key: 'answers', label: 'Cevap' },
  { key: 'views', label: 'Görüntüleme' },
]

export default async function QuestionsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; sort?: string; tag?: string }>
}) {
  const sp = await searchParams
  const page = Math.max(1, Number(sp.page) || 1)
  const sort = SORTS.find((s) => s.key === sp.sort)?.key ?? 'created'
  const tag = sp.tag

  const data = await listQuestions({ page, sort, tag })

  const hrefWith = (next: { sort?: QuestionSort; page?: number }) => {
    const q = new URLSearchParams()
    const s = next.sort ?? sort
    const p = next.page ?? 1
    if (s !== 'created') q.set('sort', s)
    if (tag) q.set('tag', tag)
    if (p > 1) q.set('page', String(p))
    const qs = q.toString()
    return qs ? `/questions?${qs}` : '/questions'
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          {tag ? `#${tag} soruları` : 'Tüm sorular'}
        </h1>
        <span className="text-sm text-neutral-500 dark:text-neutral-400">
          {data.total} soru
        </span>
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
          Henüz soru yok.
        </p>
      ) : (
        <div>
          {data.items.map((q) => (
            <QuestionCard key={q.id} q={q} />
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
