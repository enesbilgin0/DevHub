'use client'

import { useActionState } from 'react'

import type { FormState } from '@/app/actions/qa'
import { MarkdownEditor } from '@/components/markdown-editor'

export function AnswerForm({
  action,
}: {
  action: (prev: FormState | undefined, formData: FormData) => Promise<FormState>
}) {
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {})
  const sent = state && !state.error && !state.fieldErrors

  return (
    <form action={formAction} className="mt-4 flex flex-col gap-3">
      <h3 className="text-lg font-medium">Cevabın</h3>
      <MarkdownEditor name="body" rows={8} placeholder="Markdown destekler. Kod için ``` kullan." />
      {state?.fieldErrors?.body && (
        <p className="text-xs text-red-600 dark:text-red-400">{state.fieldErrors.body[0]}</p>
      )}
      {state?.error && (
        <p className="text-sm text-red-600 dark:text-red-400">{state.error}</p>
      )}
      {sent && (
        <p className="text-sm text-green-700 dark:text-green-400">Cevabın eklendi.</p>
      )}
      <button
        type="submit"
        disabled={pending}
        className="self-start rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
      >
        {pending ? 'Gönderiliyor…' : 'Cevap gönder'}
      </button>
    </form>
  )
}
