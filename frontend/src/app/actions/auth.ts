'use server'

import { redirect } from 'next/navigation'

import { apiFetch } from '@/lib/api'
import { clearSession, getAccessToken, setSession, type TokenPair } from '@/lib/session'
import { LoginSchema, RegisterSchema } from '@/lib/validation'

export interface AuthState {
  error?: string
  fieldErrors?: Record<string, string[]>
}

export async function login(
  _prev: AuthState | undefined,
  formData: FormData,
): Promise<AuthState> {
  const parsed = LoginSchema.safeParse({
    identifier: formData.get('identifier'),
    password: formData.get('password'),
  })
  if (!parsed.success) {
    return { fieldErrors: z_flatten(parsed.error) }
  }

  const res = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify(parsed.data),
  })
  if (res.status === 401) {
    return { error: 'Kullanıcı adı/e-posta veya şifre hatalı.' }
  }
  if (!res.ok) {
    return { error: 'Beklenmeyen bir hata oluştu. Tekrar deneyin.' }
  }

  await setSession((await res.json()) as TokenPair)
  redirect('/feed')
}

export async function register(
  _prev: AuthState | undefined,
  formData: FormData,
): Promise<AuthState> {
  const bio = formData.get('bio')
  const parsed = RegisterSchema.safeParse({
    username: formData.get('username'),
    email: formData.get('email'),
    password: formData.get('password'),
    bio: bio ? bio : undefined,
  })
  if (!parsed.success) {
    return { fieldErrors: z_flatten(parsed.error) }
  }

  const res = await apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify(parsed.data),
  })
  if (res.status === 409) {
    return { error: 'Bu kullanıcı adı veya e-posta zaten kullanımda.' }
  }
  if (!res.ok) {
    return { error: 'Kayıt başarısız. Tekrar deneyin.' }
  }

  await setSession((await res.json()) as TokenPair)
  redirect('/feed')
}

export async function logout(): Promise<void> {
  const token = await getAccessToken()
  if (token) {
    // Backend'de bu kullanıcının tüm refresh token'larını revoke et.
    await apiFetch('/auth/logout', { method: 'POST', token }).catch(() => {})
  }
  await clearSession()
  redirect('/login')
}

/** Zod hata listesini { alan: [mesaj] } biçimine indirger. */
function z_flatten(error: {
  issues: { path: PropertyKey[]; message: string }[]
}): Record<string, string[]> {
  const out: Record<string, string[]> = {}
  for (const issue of error.issues) {
    const key = String(issue.path[0] ?? 'form')
    ;(out[key] ??= []).push(issue.message)
  }
  return out
}
