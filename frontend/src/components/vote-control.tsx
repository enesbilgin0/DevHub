'use client'

import { useState, useTransition } from 'react'

interface Props {
  score: number
  canVote: boolean
  vote: (value: number) => Promise<{ score?: number; error?: string }>
}

/** Optimistic oy kontrolü (▲ / ▼). Sunucu yanıtıyla mutabakat. */
export function VoteControl({ score: initialScore, canVote, vote }: Props) {
  const [score, setScore] = useState(initialScore)
  const [myVote, setMyVote] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [pending, startTransition] = useTransition()

  function cast(dir: 1 | -1) {
    if (!canVote || pending) return
    const target = myVote === dir ? 0 : dir
    const prevScore = score
    const prevVote = myVote

    setError(null)
    setScore(score + (target - myVote)) // optimistik
    setMyVote(target)

    startTransition(async () => {
      const res = await vote(target)
      if (res.error) {
        setScore(prevScore)
        setMyVote(prevVote)
        setError(res.error)
      } else if (typeof res.score === 'number') {
        setScore(res.score)
      }
    })
  }

  const arrow = (dir: 1 | -1) =>
    `flex h-8 w-8 items-center justify-center rounded text-lg ${
      myVote === dir ? 'text-orange-500' : 'text-neutral-400 dark:text-neutral-500'
    } ${
      canVote
        ? 'hover:bg-neutral-100 hover:text-orange-500 dark:hover:bg-neutral-800'
        : 'cursor-not-allowed'
    }`

  return (
    <div
      className="flex flex-col items-center gap-1"
      title={!canVote ? 'Oy vermek için giriş yap' : ''}
    >
      <button
        type="button"
        aria-label="Yukarı oy"
        className={arrow(1)}
        onClick={() => cast(1)}
        disabled={!canVote || pending}
      >
        ▲
      </button>
      <span className="text-sm font-semibold tabular-nums">{score}</span>
      <button
        type="button"
        aria-label="Aşağı oy"
        className={arrow(-1)}
        onClick={() => cast(-1)}
        disabled={!canVote || pending}
      >
        ▼
      </button>
      {error && (
        <span className="mt-1 max-w-24 text-center text-[10px] text-red-600 dark:text-red-400">
          {error}
        </span>
      )}
    </div>
  )
}
