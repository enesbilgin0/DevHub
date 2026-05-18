'use client'

import { useActionState } from 'react'

import { createQuestion, type FormState } from '@/app/actions/qa'
import { MarkdownEditor } from '@/components/markdown-editor'

const inputClass =
  'w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-neutral-900 dark:border-neutral-700 dark:focus:border-neutral-300'
const errClass = 'mt-1 text-xs text-red-600 dark:text-red-400'

export function AskForm() {
  const [state, formAction, pending] = useActionState<FormState, FormData>(
    createQuestion,
    {},
  )

  return (
    <form action={formAction} className="mt-6 flex flex-col gap-5">
      <div>
        <label htmlFor="title" className="text-sm font-medium">
          Başlık
        </label>
        <input
          id="title"
          name="title"
          className={inputClass}
          placeholder="Sorunu tek cümleyle özetle"
        />
        {state?.fieldErrors?.title && <p className={errClass}>{state.fieldErrors.title[0]}</p>}
      </div>

      <div>
        <label htmlFor="body" className="text-sm font-medium">
          Detay
        </label>
        <MarkdownEditor
          name="body"
          rows={12}
          placeholder="Sorununu detaylandır. Kod blokları için ``` kullan."
        />
        {state?.fieldErrors?.body && <p className={errClass}>{state.fieldErrors.body[0]}</p>}
      </div>

      <div>
        <label htmlFor="tags" className="text-sm font-medium">
          Etiketler{' '}
          <span className="text-neutral-400 dark:text-neutral-500">
            (virgülle ayır, en fazla 5)
          </span>
        </label>
        <input
          id="tags"
          name="tags"
          className={inputClass}
          placeholder="python, fastapi, postgresql"
        />
        {state?.fieldErrors?.tags && <p className={errClass}>{state.fieldErrors.tags[0]}</p>}
      </div>

      {state?.error && (
        <p className="text-sm text-red-600 dark:text-red-400">{state.error}</p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="self-start rounded-md bg-neutral-900 px-5 py-2 text-sm font-medium text-white hover:bg-neutral-700 disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
      >
        {pending ? 'Yayınlanıyor…' : 'Soruyu yayınla'}
      </button>
    </form>
  )
}
