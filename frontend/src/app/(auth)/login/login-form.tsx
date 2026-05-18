'use client'

import { useActionState } from 'react'

import { login, type AuthState } from '@/app/actions/auth'

const fieldClass =
  'w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-neutral-900 dark:border-neutral-700 dark:focus:border-neutral-300'
const errClass = 'mt-1 text-xs text-red-600 dark:text-red-400'

export function LoginForm() {
  const [state, formAction, pending] = useActionState<AuthState, FormData>(
    login,
    {},
  )

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div>
        <label htmlFor="identifier" className="text-sm font-medium">
          Kullanıcı adı veya e-posta
        </label>
        <input id="identifier" name="identifier" className={fieldClass} autoComplete="username" />
        {state?.fieldErrors?.identifier && (
          <p className={errClass}>{state.fieldErrors.identifier[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="text-sm font-medium">
          Şifre
        </label>
        <input
          id="password"
          name="password"
          type="password"
          className={fieldClass}
          autoComplete="current-password"
        />
        {state?.fieldErrors?.password && (
          <p className={errClass}>{state.fieldErrors.password[0]}</p>
        )}
      </div>

      {state?.error && (
        <p className="text-sm text-red-600 dark:text-red-400">{state.error}</p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
      >
        {pending ? 'Giriş yapılıyor…' : 'Giriş yap'}
      </button>
    </form>
  )
}
