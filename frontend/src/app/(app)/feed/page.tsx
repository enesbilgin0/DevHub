import { redirect } from 'next/navigation'

import { logout } from '@/app/actions/auth'
import { getCurrentUser } from '@/lib/auth'

export default async function FeedPage() {
  // proxy zaten optimistic koruyor; burada asıl/güvenli doğrulama.
  const user = await getCurrentUser()
  if (!user) redirect('/login')

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <header className="flex items-center justify-between border-b border-neutral-200 pb-4">
        <h1 className="text-xl font-semibold">Akış</h1>
        <form action={logout}>
          <button
            type="submit"
            className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100"
          >
            Çıkış yap
          </button>
        </form>
      </header>

      <section className="mt-6 rounded-lg border border-neutral-200 p-5">
        <p className="text-sm text-neutral-500">Giriş yapan kullanıcı</p>
        <p className="mt-1 text-lg font-medium">{user.username}</p>
        <p className="text-sm text-neutral-500">{user.email}</p>
        <p className="mt-3 text-sm">
          İtibar: <span className="font-medium">{user.reputation}</span>
        </p>
      </section>

      <p className="mt-6 text-sm text-neutral-400">
        Soru akışı Görev 02&apos;de eklenecek.
      </p>
    </main>
  )
}
