import Link from 'next/link'
import { redirect } from 'next/navigation'

import { getCurrentUser } from '@/lib/auth'

export default async function FeedPage() {
  // proxy zaten optimistic koruyor; burada asıl/güvenli doğrulama.
  const user = await getCurrentUser()
  if (!user) redirect('/login')

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-xl font-semibold">Profilin</h1>

      <section className="mt-4 rounded-lg border border-neutral-200 p-5 dark:border-neutral-800">
        <p className="text-sm text-neutral-500 dark:text-neutral-400">Giriş yapan kullanıcı</p>
        <p className="mt-1 text-lg font-medium">{user.username}</p>
        <p className="text-sm text-neutral-500 dark:text-neutral-400">{user.email}</p>
        <p className="mt-3 text-sm">
          İtibar: <span className="font-medium">{user.reputation}</span>
        </p>
      </section>

      <Link
        href="/questions"
        className="mt-6 inline-block rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
      >
        Sorulara göz at →
      </Link>
    </main>
  )
}
