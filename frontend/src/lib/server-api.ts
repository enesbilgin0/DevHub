import 'server-only'

import { apiFetch } from './api'
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  setSession,
  type TokenPair,
} from './session'

/**
 * Kimlikli backend isteği — yalnızca Server Action'lardan çağrılır.
 *
 * Access token süresi dolmuşsa (401) refresh token ile bir kez yeniler,
 * yeni token'ları cookie'ye yazar ve isteği tekrarlar. Cookie yazımı
 * sadece Server Action / Route Handler içinde mümkün olduğundan burada.
 */
export async function authedFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const access = await getAccessToken()
  const res = await apiFetch(path, { ...init, token: access })
  if (res.status !== 401) return res

  const refresh = await getRefreshToken()
  if (!refresh) return res

  const r = await apiFetch('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refresh }),
  })
  if (!r.ok) {
    await clearSession()
    return res
  }
  const tokens = (await r.json()) as TokenPair
  await setSession(tokens)
  return apiFetch(path, { ...init, token: tokens.access_token })
}
