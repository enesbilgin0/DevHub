'use client'

import { useActionState, useState } from 'react'

import type { FormState } from '@/app/actions/qa'

import { MarkdownEditor } from './markdown-editor'

interface Props {
  defaultValue: string
  action: (prev: FormState | undefined, formData: FormData) => Promise<FormState>
}

/** Cevap kartı içinde "Düzenle / Vazgeç" toggle'lı inline form. */
export function AnswerEdit({ defaultValue, action }: Props) {
  const [open, setOpen] = useState(false)
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {})
  const sent = state && !state.error && !state.fieldErrors

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="text-xs text-blue-700 hover:underline dark:text-blue-400"
      >
        Düzenle
      </button>
    )
  }

  return (
    <form action={formAction} className="mt-3 flex flex-col gap-2">
      <MarkdownEditor name="body" rows={8} defaultValue={defaultValue} />
      {state?.fieldErrors?.body && (
        <p className="text-xs text-red-600 dark:text-red-400">{state.fieldErrors.body[0]}</p>
      )}
      {state?.error && (
        <p className="text-sm text-red-600 dark:text-red-400">{state.error}</p>
      )}
      {sent && (
        <p className="text-xs text-green-700 dark:text-green-400">Kaydedildi.</p>
      )}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-neutral-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-neutral-700 disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
        >
          {pending ? 'Kaydediliyor…' : 'Kaydet'}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-md border border-neutral-300 px-3 py-1.5 text-xs hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
        >
          Vazgeç
        </button>
      </div>
    </form>
  )
}
