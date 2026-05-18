import 'server-only'

import { cache } from 'react'

import { apiFetch } from './api'
import { getAccessToken } from './session'

export interface CurrentUser {
  id: number
  username: string
  email: string
  bio: string | null
  joined_at: string
  reputation: number
}

/**
 * Mevcut kullanıcıyı backend'den doğrular (asıl/güvenli kontrol).
 *
 * Salt-okunurdur: cookie yazmaz. Access token süresi dolmuşsa yenileme
 * işini `proxy.ts` render'dan önce yapar (cookie sadece orada/Server
 * Action'larda yazılabilir). `cache` ile aynı render içinde tek çağrı.
 */
export const getCurrentUser = cache(async (): Promise<CurrentUser | null> => {
  const token = await getAccessToken()
  if (!token) return null

  const res = await apiFetch('/auth/me', { token })
  if (!res.ok) return null

  return (await res.json()) as CurrentUser
})
