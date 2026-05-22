import { notFound, redirect } from 'next/navigation'

import { getCurrentUser } from '@/lib/auth'
import { getQuestion } from '@/lib/questions'

import { EditQuestionForm } from './edit-form'

export default async function EditQuestionPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const qid = Number(id)
  if (!Number.isInteger(qid) || qid < 1) notFound()

  const user = await getCurrentUser()
  if (!user) redirect(`/login?next=/questions/${qid}/edit`)

  const question = await getQuestion(qid)
  if (!question) notFound()

  // Yetki kontrolünü server tarafında ve net mesajla yap;
  // backend zaten PATCH'i 403 ile koruyor ama UI'da hiç göstermeyelim.
  if (question.author.id !== user.id) {
    redirect(`/questions/${qid}`)
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <h1 className="text-2xl font-semibold">Soruyu düzenle</h1>
      <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
        Değişikliklerin geçmişi tutulmaz; başlık, içerik veya etiketleri güncelle.
      </p>
      <EditQuestionForm
        qid={qid}
        initial={{
          title: question.title,
          body: question.body,
          tags: question.tags,
        }}
      />
    </main>
  )
}
