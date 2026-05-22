'use client'

import { useRef, useState, useTransition } from 'react'

import { createComment, type CommentResult } from '@/app/actions/comments'

import type { CommentTarget } from '@/lib/comments'

interface Props {
  target: CommentTarget
  targetId: number
  qid: number
}

/** Tek satırlık yorum girişi; başarıda kapanır, formu temizler. */
export function CommentForm({ target, targetId, qid }: Props) {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pending, startTransition] = useTransition()
  const ref = useRef<HTMLTextAreaElement>(null)

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="text-xs text-blue-700 hover:underline dark:text-blue-400"
      >
        Yorum ekle
      </button>
    )
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        setError(null)
        const fd = new FormData(e.currentTarget)
        startTransition(async () => {
          const res: CommentResult = await createComment(target, targetId, qid, fd)
          if (res.error) {
            setError(res.error)
            return
          }
          if (ref.current) ref.current.value = ''
          setOpen(false)
        })
      }}
      className="mt-2 flex flex-col gap-2"
    >
      <textarea
        ref={ref}
        name="body"
        rows={2}
        maxLength={600}
        placeholder="Yorum (5–600 karakter). Düz metin; düzenleme yok."
        className="w-full resize-y rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm outline-none focus:border-neutral-500 dark:border-neutral-700"
      />
      {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-neutral-900 px-3 py-1 text-xs font-medium text-white hover:bg-neutral-700 disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
        >
          {pending ? 'Gönderiliyor…' : 'Gönder'}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false)
            setError(null)
          }}
          className="rounded-md border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
        >
          Vazgeç
        </button>
      </div>
    </form>
  )
}
