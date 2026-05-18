import { redirect } from 'next/navigation'

import { getCurrentUser } from '@/lib/auth'

import { AskForm } from './ask-form'

export default async function AskPage() {
  // proxy zaten koruyor; sayfada da çift kontrol.
  const user = await getCurrentUser()
  if (!user) redirect('/login')

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <h1 className="text-2xl font-semibold">Yeni soru sor</h1>
      <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
        Açık ve aranabilir bir başlık yaz; detayda ne denediğini anlat.
      </p>
      <AskForm />
    </main>
  )
}
