import 'server-only'

import { cookies } from 'next/headers'

/** Backend /auth uçlarının döndüğü token çifti. */
export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  access_expires_at: string
  refresh_expires_at: string
}

const ACCESS = 'access_token'
const REFRESH = 'refresh_token'
const isProd = process.env.NODE_ENV === 'production'

const baseCookie = {
  httpOnly: true, // tarayıcı JS'i erişemez → XSS'e dayanıklı
  secure: isProd, // prod'da yalnızca https
  sameSite: 'lax' as const, // CSRF azaltma
  path: '/',
}

/** Giriş/refresh sonrası token'ları httpOnly cookie'ye yazar. */
export async function setSession(tokens: TokenPair): Promise<void> {
  const store = await cookies()
  store.set(ACCESS, tokens.access_token, {
    ...baseCookie,
    expires: new Date(tokens.access_expires_at),
  })
  store.set(REFRESH, tokens.refresh_token, {
    ...baseCookie,
    expires: new Date(tokens.refresh_expires_at),
  })
}

/** Çıkış / geçersiz oturumda cookie'leri temizler. */
export async function clearSession(): Promise<void> {
  const store = await cookies()
  store.delete(ACCESS)
  store.delete(REFRESH)
}

export async function getAccessToken(): Promise<string | undefined> {
  return (await cookies()).get(ACCESS)?.value
}

export async function getRefreshToken(): Promise<string | undefined> {
  return (await cookies()).get(REFRESH)?.value
}
