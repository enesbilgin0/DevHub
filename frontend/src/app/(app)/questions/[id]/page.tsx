import Link from 'next/link'
import { notFound } from 'next/navigation'

import {
  acceptAnswer,
  createAnswer,
  deleteAnswer,
  deleteQuestion,
  updateAnswer,
  voteAnswer,
  voteQuestion,
} from '@/app/actions/qa'
import { AnswerEdit } from '@/components/answer-edit'
import { AnswerForm } from '@/components/answer-form'
import { Comments } from '@/components/comments'
import { Markdown } from '@/components/markdown'
import { VoteControl } from '@/components/vote-control'
import { getCurrentUser } from '@/lib/auth'
import { listComments } from '@/lib/comments'
import { timeAgo } from '@/lib/format'
import { getQuestion, listAnswers } from '@/lib/questions'

const metaText = 'text-xs text-neutral-500 dark:text-neutral-400'
const authorName = 'font-medium text-neutral-700 dark:text-neutral-300'

export default async function QuestionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const qid = Number(id)
  if (!Number.isInteger(qid) || qid < 1) notFound()

  const [question, user] = await Promise.all([getQuestion(qid), getCurrentUser()])
  if (!question) notFound()

  const [answers, qComments] = await Promise.all([
    listAnswers(qid),
    listComments('question', qid),
  ])
  const answerComments = await Promise.all(
    answers.map((a) => listComments('answer', a.id)),
  )
  const isOwner = !!user && user.id === question.author.id
  const currentUserId = user?.id ?? null

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <Link
        href="/questions"
        className="text-sm text-blue-700 hover:underline dark:text-blue-400"
      >
        ← Tüm sorular
      </Link>

      <div className="mt-3 border-b border-neutral-200 pb-4 dark:border-neutral-800">
        <h1 className="text-2xl font-semibold">{question.title}</h1>
        <p className={`mt-1 ${metaText}`}>
          {timeAgo(question.created_at)}
          {question.updated_at && (
            <>
              {' '}· <span title={new Date(question.updated_at).toLocaleString('tr-TR')}>
                {timeAgo(question.updated_at)} düzenlendi
              </span>
            </>
          )}{' '}· {question.view_count} görüntüleme
        </p>
      </div>

      <div className="flex gap-4 py-6">
        <VoteControl
          score={question.vote_score}
          canVote={!!user && user.id !== question.author.id}
          vote={voteQuestion.bind(null, question.id)}
        />
        <div className="min-w-0 flex-1">
          <Markdown>{question.body}</Markdown>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {question.tags.map((t) => (
              <Link
                key={t}
                href={`/questions?tag=${encodeURIComponent(t)}`}
                className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700 hover:bg-blue-100 dark:bg-blue-950 dark:text-blue-300 dark:hover:bg-blue-900"
              >
                {t}
              </Link>
            ))}
          </div>
          <div className="mt-4 flex items-center justify-between">
            <p className={metaText}>
              <Link
                href={`/users/${encodeURIComponent(question.author.username)}`}
                className={`${authorName} hover:underline`}
              >
                {question.author.username}
              </Link>{' '}
              · {question.author.reputation} itibar
            </p>
            {isOwner && (
              <div className="flex gap-3">
                <Link
                  href={`/questions/${question.id}/edit`}
                  className="text-xs text-blue-700 hover:underline dark:text-blue-400"
                >
                  Düzenle
                </Link>
                <form action={deleteQuestion.bind(null, question.id)}>
                  <button
                    type="submit"
                    className="text-xs text-red-600 hover:underline dark:text-red-400"
                  >
                    Soruyu sil
                  </button>
                </form>
              </div>
            )}
          </div>

          <Comments
            target="question"
            targetId={question.id}
            qid={question.id}
            comments={qComments}
            currentUserId={currentUserId}
          />
        </div>
      </div>

      <h2 className="border-b border-neutral-200 py-3 text-lg font-semibold dark:border-neutral-800">
        {answers.length} Cevap
      </h2>

      <div>
        {answers.map((a, idx) => {
          const acceptAction = async () => {
            'use server'
            await acceptAnswer(a.id, question.id)
          }
          const editAction = updateAnswer.bind(null, a.id, question.id)
          const isAnswerOwner = !!user && user.id === a.author.id
          return (
            <div
              key={a.id}
              className="flex gap-4 border-b border-neutral-200 py-6 dark:border-neutral-800"
            >
              <div className="flex flex-col items-center gap-2">
                <VoteControl
                  score={a.vote_score}
                  canVote={!!user && user.id !== a.author.id}
                  vote={voteAnswer.bind(null, a.id, question.id)}
                />
                {a.is_accepted && (
                  <span
                    title="Kabul edilen cevap"
                    className="text-xl text-green-600 dark:text-green-400"
                  >
                    ✓
                  </span>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <Markdown>{a.body}</Markdown>
                <div className="mt-3 flex items-center justify-between">
                  <p className={metaText}>
                    <Link
                      href={`/users/${encodeURIComponent(a.author.username)}`}
                      className={`${authorName} hover:underline`}
                    >
                      {a.author.username}
                    </Link>{' '}
                    · {timeAgo(a.created_at)}
                    {a.updated_at && (
                      <>
                        {' '}· <span title={new Date(a.updated_at).toLocaleString('tr-TR')}>
                          {timeAgo(a.updated_at)} düzenlendi
                        </span>
                      </>
                    )}
                  </p>
                  <div className="flex gap-3">
                    {isOwner && !a.is_accepted && (
                      <form action={acceptAction}>
                        <button
                          type="submit"
                          className="text-xs text-green-700 hover:underline dark:text-green-400"
                        >
                          Kabul et
                        </button>
                      </form>
                    )}
                    {isAnswerOwner && (
                      <AnswerEdit defaultValue={a.body} action={editAction} />
                    )}
                    {isAnswerOwner && (
                      <form action={deleteAnswer.bind(null, a.id, question.id)}>
                        <button
                          type="submit"
                          className="text-xs text-red-600 hover:underline dark:text-red-400"
                        >
                          Sil
                        </button>
                      </form>
                    )}
                  </div>
                </div>

                <Comments
                  target="answer"
                  targetId={a.id}
                  qid={question.id}
                  comments={answerComments[idx]}
                  currentUserId={currentUserId}
                />
              </div>
            </div>
          )
        })}
      </div>

      {user ? (
        <AnswerForm action={createAnswer.bind(null, question.id)} />
      ) : (
        <p className="mt-6 text-sm text-neutral-500 dark:text-neutral-400">
          Cevap yazmak için{' '}
          <Link href="/login" className="font-medium text-blue-700 hover:underline dark:text-blue-400">
            giriş yap
          </Link>
          .
        </p>
      )}
    </main>
  )
}
