import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Next 16: `middleware.ts` kaldırıldı, dosya adı `proxy.ts`. src/ kullandığımız
// için app/ ile aynı seviyede (src/proxy.ts) durur.

const API_URL = process.env.API_URL ?? 'http://127.0.0.1:8000'
const isProd = process.env.NODE_ENV === 'production'

const PROTECTED = ['/feed']
const AUTH_PAGES = ['/login', '/register']

interface TokenPair {
  access_token: string
  refresh_token: string
  access_expires_at: string
  refresh_expires_at: string
}

function applyTokens(res: NextResponse, t: TokenPair): void {
  const base = { httpOnly: true, secure: isProd, sameSite: 'lax' as const, path: '/' }
  res.cookies.set('access_token', t.access_token, {
    ...base,
    expires: new Date(t.access_expires_at),
  })
  res.cookies.set('refresh_token', t.refresh_token, {
    ...base,
    expires: new Date(t.refresh_expires_at),
  })
}

async function tryRefresh(refreshToken: string): Promise<TokenPair | null> {
  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: 'no-store',
    })
    return res.ok ? ((await res.json()) as TokenPair) : null
  } catch {
    return null
  }
}

export default async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname
  const access = req.cookies.get('access_token')?.value
  const refresh = req.cookies.get('refresh_token')?.value

  const isProtected = PROTECTED.some((p) => path === p || path.startsWith(`${p}/`))
  const isAuthPage = AUTH_PAGES.includes(path)

  // Giriş yapmış kullanıcı login/register görmesin.
  if (isAuthPage && refresh) {
    return NextResponse.redirect(new URL('/feed', req.nextUrl))
  }

  if (!isProtected) {
    return NextResponse.next()
  }

  // Optimistic kontrol: access cookie varsa geçir (asıl doğrulamayı sayfa yapar).
  if (access) {
    return NextResponse.next()
  }

  // Access süresi dolmuş ama refresh varsa: bir kez yenile.
  if (refresh) {
    const tokens = await tryRefresh(refresh)
    if (tokens) {
      // Aynı URL'e yönlendir; tarayıcı yeni cookie ile tekrar gelir.
      const res = NextResponse.redirect(req.nextUrl)
      applyTokens(res, tokens)
      return res
    }
  }

  // Oturum yok/geçersiz → temizle ve login'e gönder.
  const res = NextResponse.redirect(new URL('/login', req.nextUrl))
  res.cookies.delete('access_token')
  res.cookies.delete('refresh_token')
  return res
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
