import 'server-only'

const API_URL = process.env.API_URL ?? 'http://127.0.0.1:8000'

/** Backend'e sunucu tarafından istek atan ince sarmalayıcı. */
export async function apiFetch(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<Response> {
  const { token, headers, ...rest } = init
  return fetch(`${API_URL}${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    // Auth verisi asla cache'lenmemeli.
    cache: 'no-store',
  })
}
