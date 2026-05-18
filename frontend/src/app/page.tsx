import Link from 'next/link'

import { getCurrentUser } from '@/lib/auth'

export default async function Home() {
  const user = await getCurrentUser()

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-8 px-6 text-center">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">DevHub</h1>
        <p className="mt-3 text-neutral-500">
          Geliştiricilerin soru sorup yanıtladığı topluluk.
        </p>
      </div>

      {user ? (
        <Link
          href="/feed"
          className="rounded-md bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-neutral-700"
        >
          {user.username} olarak devam et →
        </Link>
      ) : (
        <div className="flex gap-3">
          <Link
            href="/login"
            className="rounded-md bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-neutral-700"
          >
            Giriş yap
          </Link>
          <Link
            href="/register"
            className="rounded-md border border-neutral-300 px-5 py-2.5 text-sm font-medium hover:bg-neutral-100"
          >
            Kayıt ol
          </Link>
        </div>
      )}
    </main>
  )
}
