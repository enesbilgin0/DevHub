import Link from 'next/link'
import { notFound } from 'next/navigation'

import { ActivityGraph } from '@/components/activity-graph'
import { BadgeList } from '@/components/badge-list'
import { QuestionCard } from '@/components/question-card'
import { timeAgo } from '@/lib/format'
import { listQuestions } from '@/lib/questions'
import { getActivity, getProfile, getUserAnswers } from '@/lib/users'

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-neutral-200 px-4 py-3 text-center dark:border-neutral-800">
      <div className="text-xl font-semibold tabular-nums">{value}</div>
      <div className="text-xs text-neutral-500 dark:text-neutral-400">{label}</div>
    </div>
  )
}

export default async function ProfilePage({
  params,
}: {
  params: Promise<{ username: string }>
}) {
  const { username } = await params
  const profile = await getProfile(username)
  if (!profile) notFound()

  const [activity, questions, answers] = await Promise.all([
    getActivity(profile.username),
    listQuestions({ author: profile.username, pageSize: 10 }),
    getUserAnswers(profile.username),
  ])

  const joined = new Date(profile.joined_at).toLocaleDateString('tr-TR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <header className="border-b border-neutral-200 pb-5 dark:border-neutral-800">
        <h1 className="text-2xl font-semibold">{profile.username}</h1>
        {profile.bio && (
          <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400">{profile.bio}</p>
        )}
        <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
          {joined} tarihinde katıldı · {profile.reputation} itibar
        </p>
      </header>

      <section className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Soru" value={profile.stats.questions} />
        <Stat label="Cevap" value={profile.stats.answers} />
        <Stat label="Kabul edilen" value={profile.stats.accepted_answers} />
        <Stat label="Alınan oy" value={profile.stats.votes_received} />
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Rozetler</h2>
        <BadgeList badges={profile.badges} />
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Son bir yıl</h2>
        <ActivityGraph data={activity} />
      </section>

      <section className="mt-8">
        <h2 className="mb-1 text-lg font-semibold">Son sorular</h2>
        {questions.items.length === 0 ? (
          <p className="py-4 text-sm text-neutral-500 dark:text-neutral-400">Henüz soru yok.</p>
        ) : (
          questions.items.map((q) => <QuestionCard key={q.id} q={q} />)
        )}
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Son cevaplar</h2>
        {answers.length === 0 ? (
          <p className="text-sm text-neutral-500 dark:text-neutral-400">Henüz cevap yok.</p>
        ) : (
          <ul className="divide-y divide-neutral-200 dark:divide-neutral-800">
            {answers.map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-4 py-3">
                <Link
                  href={`/questions/${a.question_id}`}
                  className="min-w-0 flex-1 truncate text-sm text-blue-700 hover:underline dark:text-blue-400"
                >
                  {a.question_title}
                </Link>
                <span className="shrink-0 text-xs text-neutral-500 dark:text-neutral-400">
                  {a.is_accepted && <span className="mr-2 text-green-600 dark:text-green-400">✓ kabul</span>}
                  {a.vote_score} oy · {timeAgo(a.created_at)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
