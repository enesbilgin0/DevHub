'use client'

import { useActionState } from 'react'

import { register, type AuthState } from '@/app/actions/auth'

const fieldClass =
  'w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900'

export function RegisterForm() {
  const [state, formAction, pending] = useActionState<AuthState, FormData>(
    register,
    {},
  )

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div>
        <label htmlFor="username" className="text-sm font-medium">
          Kullanıcı adı
        </label>
        <input id="username" name="username" className={fieldClass} autoComplete="username" />
        {state?.fieldErrors?.username && (
          <p className="mt-1 text-xs text-red-600">{state.fieldErrors.username[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="email" className="text-sm font-medium">
          E-posta
        </label>
        <input id="email" name="email" type="email" className={fieldClass} autoComplete="email" />
        {state?.fieldErrors?.email && (
          <p className="mt-1 text-xs text-red-600">{state.fieldErrors.email[0]}</p>
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
          autoComplete="new-password"
        />
        {state?.fieldErrors?.password && (
          <p className="mt-1 text-xs text-red-600">{state.fieldErrors.password[0]}</p>
        )}
      </div>

      <div>
        <label htmlFor="bio" className="text-sm font-medium">
          Hakkında <span className="text-neutral-400">(opsiyonel)</span>
        </label>
        <textarea id="bio" name="bio" rows={2} className={fieldClass} />
        {state?.fieldErrors?.bio && (
          <p className="mt-1 text-xs text-red-600">{state.fieldErrors.bio[0]}</p>
        )}
      </div>

      {state?.error && <p className="text-sm text-red-600">{state.error}</p>}

      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 disabled:opacity-60"
      >
        {pending ? 'Hesap oluşturuluyor…' : 'Kayıt ol'}
      </button>
    </form>
  )
}
