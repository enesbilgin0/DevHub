'use client'

import { useActionState } from 'react'

import { updateQuestion, type FormState } from '@/app/actions/qa'
import { MarkdownEditor } from '@/components/markdown-editor'

const inputClass =
  'w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-neutral-900 dark:border-neutral-700 dark:focus:border-neutral-300'
const errClass = 'mt-1 text-xs text-red-600 dark:text-red-400'

interface Props {
  qid: number
  initial: {
    title: string
    body: string
    tags: string[]
  }
}

export function EditQuestionForm({ qid, initial }: Props) {
  const action = updateQuestion.bind(null, qid)
  const [state, formAction, pending] = useActionState<FormState, FormData>(action, {})

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
          defaultValue={initial.title}
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
          defaultValue={initial.body}
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
          defaultValue={initial.tags.join(', ')}
        />
        {state?.fieldErrors?.tags && <p className={errClass}>{state.fieldErrors.tags[0]}</p>}
      </div>

      {state?.error && (
        <p className="text-sm text-red-600 dark:text-red-400">{state.error}</p>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-neutral-900 px-5 py-2 text-sm font-medium text-white hover:bg-neutral-700 disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
        >
          {pending ? 'Kaydediliyor…' : 'Kaydet'}
        </button>
        <a
          href={`/questions/${qid}`}
          className="rounded-md border border-neutral-300 px-5 py-2 text-sm font-medium hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
        >
          Vazgeç
        </a>
      </div>
    </form>
  )
}
