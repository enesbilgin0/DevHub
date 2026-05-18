import Link from 'next/link'

import { ThemeToggle } from '@/components/theme-toggle'
import { getCurrentUser } from '@/lib/auth'

export default async function Home() {
  const user = await getCurrentUser()

  return (
    <>
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-8 px-6 text-center">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">DevHub</h1>
          <p className="mt-3 text-neutral-500 dark:text-neutral-400">
            Geliştiricilerin soru sorup yanıtladığı topluluk.
          </p>
        </div>

        {user ? (
          <Link
            href="/questions"
            className="rounded-md bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
          >
            {user.username} olarak devam et →
          </Link>
        ) : (
          <div className="flex gap-3">
            <Link
              href="/login"
              className="rounded-md bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
            >
              Giriş yap
            </Link>
            <Link
              href="/register"
              className="rounded-md border border-neutral-300 px-5 py-2.5 text-sm font-medium hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
            >
              Kayıt ol
            </Link>
          </div>
        )}
      </main>
    </>
  )
}
