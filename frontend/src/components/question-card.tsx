import Link from 'next/link'

import { timeAgo } from '@/lib/format'
import type { QuestionSummary } from '@/lib/questions'

function Stat({ value, label, highlight }: { value: number; label: string; highlight?: boolean }) {
  return (
    <div
      className={`flex w-16 flex-col items-center rounded-md border px-1 py-1.5 text-center ${
        highlight
          ? 'border-green-600 text-green-700 dark:text-green-400'
          : 'border-neutral-200 text-neutral-600 dark:border-neutral-800 dark:text-neutral-400'
      }`}
    >
      <span className="text-sm font-semibold tabular-nums">{value}</span>
      <span className="text-[11px]">{label}</span>
    </div>
  )
}

export function QuestionCard({ q }: { q: QuestionSummary }) {
  return (
    <article className="flex gap-4 border-b border-neutral-200 py-5 dark:border-neutral-800">
      <div className="flex shrink-0 gap-2">
        <Stat value={q.vote_score} label="oy" />
        <Stat value={q.answer_count} label="cevap" highlight={q.has_accepted} />
        <Stat value={q.view_count} label="görüntüleme" />
      </div>

      <div className="min-w-0 flex-1">
        <h2 className="truncate text-lg font-medium text-blue-700 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300">
          <Link href={`/questions/${q.id}`}>{q.title}</Link>
        </h2>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {q.tags.map((t) => (
            <Link
              key={t}
              href={`/questions?tag=${encodeURIComponent(t)}`}
              className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700 hover:bg-blue-100 dark:bg-blue-950 dark:text-blue-300 dark:hover:bg-blue-900"
            >
              {t}
            </Link>
          ))}
        </div>
        <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
          <Link
            href={`/users/${encodeURIComponent(q.author.username)}`}
            className="font-medium text-neutral-700 hover:underline dark:text-neutral-300"
          >
            {q.author.username}
          </Link>{' '}
          · {q.author.reputation} itibar · {timeAgo(q.created_at)}
        </p>
      </div>
    </article>
  )
}
