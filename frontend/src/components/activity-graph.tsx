import type { ActivityDay } from '@/lib/users'

const MONTHS = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']

const LEVEL_FILL = [
  'fill-neutral-200 dark:fill-neutral-800',
  'fill-green-200 dark:fill-green-900',
  'fill-green-400 dark:fill-green-700',
  'fill-green-500 dark:fill-green-600',
  'fill-green-600 dark:fill-green-500',
]

function level(count: number): number {
  if (count <= 0) return 0
  if (count <= 2) return 1
  if (count <= 4) return 2
  if (count <= 6) return 3
  return 4
}

function isoDay(d: Date): string {
  return d.toISOString().slice(0, 10)
}

/** GitHub tarzı yıllık katkı ısı haritası (SVG). */
export function ActivityGraph({ data }: { data: ActivityDay[] }) {
  const counts = new Map(data.map((d) => [d.day, d.count]))

  const today = new Date()
  const end = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
  const start = new Date(end)
  start.setUTCDate(start.getUTCDate() - 364)
  start.setUTCDate(start.getUTCDate() - start.getUTCDay()) // haftanın başına (Pazar) hizala

  const CELL = 13
  const SIZE = 11
  const cells: { x: number; y: number; key: string; count: number; lvl: number }[] = []
  const monthLabels: { x: number; label: string }[] = []
  let lastMonth = -1

  const cur = new Date(start)
  let week = 0
  while (cur <= end) {
    const dow = cur.getUTCDay()
    if (dow === 0) {
      week = Math.round((cur.getTime() - start.getTime()) / (7 * 86400000))
      const m = cur.getUTCMonth()
      if (m !== lastMonth) {
        monthLabels.push({ x: week * CELL, label: MONTHS[m] })
        lastMonth = m
      }
    }
    const key = isoDay(cur)
    const count = counts.get(key) ?? 0
    cells.push({ x: week * CELL, y: dow * CELL, key, count, lvl: level(count) })
    cur.setUTCDate(cur.getUTCDate() + 1)
  }

  const weeks = Math.ceil((end.getTime() - start.getTime()) / (7 * 86400000)) + 1
  const width = weeks * CELL
  const height = 7 * CELL + 16

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height} className="text-[10px]" role="img" aria-label="Katkı aktivitesi">
        {monthLabels.map((m) => (
          <text key={`${m.x}-${m.label}`} x={m.x} y={9} className="fill-neutral-500 dark:fill-neutral-400">
            {m.label}
          </text>
        ))}
        <g transform="translate(0, 16)">
          {cells.map((c) => (
            <rect
              key={c.key}
              x={c.x}
              y={c.y}
              width={SIZE}
              height={SIZE}
              rx={2}
              className={LEVEL_FILL[c.lvl]}
            >
              <title>{`${c.key}: ${c.count} katkı`}</title>
            </rect>
          ))}
        </g>
      </svg>
      <div className="mt-2 flex items-center gap-1 text-xs text-neutral-500 dark:text-neutral-400">
        <span>Az</span>
        <svg width={5 * CELL} height={SIZE}>
          {LEVEL_FILL.map((f, i) => (
            <rect key={i} x={i * CELL} y={0} width={SIZE} height={SIZE} rx={2} className={f} />
          ))}
        </svg>
        <span>Çok</span>
      </div>
    </div>
  )
}
