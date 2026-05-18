import type { Badge } from '@/lib/users'

export function BadgeList({ badges }: { badges: Badge[] }) {
  if (badges.length === 0) {
    return <p className="text-sm text-neutral-500 dark:text-neutral-400">Henüz rozet yok.</p>
  }
  return (
    <div className="flex flex-wrap gap-2">
      {badges.map((b) => (
        <span
          key={b.key}
          title={b.description}
          className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-300"
        >
          {b.label}
        </span>
      ))}
    </div>
  )
}
