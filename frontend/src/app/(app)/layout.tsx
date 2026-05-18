import Link from 'next/link'

import { logout } from '@/app/actions/auth'
import { ThemeToggle } from '@/components/theme-toggle'
import { getCurrentUser } from '@/lib/auth'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser()

  return (
    <div className="min-h-screen">
      <header className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-950">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3">
          <nav className="flex items-center gap-5 text-sm">
            <Link href="/" className="text-base font-bold">
              DevHub
            </Link>
            <Link
              href="/questions"
              className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
            >
              Sorular
            </Link>
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <ThemeToggle />
            {user ? (
              <>
                <Link
                  href="/questions/ask"
                  className="rounded-md bg-neutral-900 px-3 py-1.5 font-medium text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
                >
                  Soru sor
                </Link>
                <Link
                  href={`/users/${encodeURIComponent(user.username)}`}
                  className="text-neutral-700 hover:underline dark:text-neutral-300"
                >
                  {user.username}
                </Link>
                <form action={logout}>
                  <button
                    type="submit"
                    className="text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
                  >
                    Çıkış
                  </button>
                </form>
              </>
            ) : (
              <>
                <Link href="/login" className="hover:underline">
                  Giriş
                </Link>
                <Link
                  href="/register"
                  className="rounded-md bg-neutral-900 px-3 py-1.5 font-medium text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
                >
                  Kayıt ol
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      {children}
    </div>
  )
}
