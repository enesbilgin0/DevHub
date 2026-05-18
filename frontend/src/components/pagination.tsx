import Link from 'next/link'

interface Props {
  page: number
  pageSize: number
  total: number
  makeHref: (page: number) => string
}

export function Pagination({ page, pageSize, total, makeHref }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  if (totalPages <= 1) return null

  const linkClass =
    'rounded-md border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800'
  const disabledClass =
    'rounded-md border border-neutral-200 px-3 py-1.5 text-sm text-neutral-300 dark:border-neutral-800 dark:text-neutral-700'

  return (
    <nav className="mt-8 flex items-center justify-center gap-3">
      {page > 1 ? (
        <Link href={makeHref(page - 1)} className={linkClass}>
          ← Önceki
        </Link>
      ) : (
        <span className={disabledClass}>← Önceki</span>
      )}
      <span className="text-sm text-neutral-500 dark:text-neutral-400">
        Sayfa {page} / {totalPages}
      </span>
      {page < totalPages ? (
        <Link href={makeHref(page + 1)} className={linkClass}>
          Sonraki →
        </Link>
      ) : (
        <span className={disabledClass}>Sonraki →</span>
      )}
    </nav>
  )
}
