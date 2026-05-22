import Link from 'next/link'

import { deleteComment } from '@/app/actions/comments'
import { timeAgo } from '@/lib/format'

import { CommentForm } from './comment-form'

import type { Comment, CommentTarget } from '@/lib/comments'

interface Props {
  target: CommentTarget
  targetId: number
  qid: number
  comments: Comment[]
  currentUserId: number | null
}

/**
 * Yorum bölümü — listeleme + (giriş yapanlar için) form + (sahibi için) silme.
 *
 * Yorum gövdesi DÜZ METİNDİR (Markdown YOK): XSS yüzeyini küçültür ve
 * react-markdown'a gerek bırakmaz. URL'leri kullanıcı tarayıcıda manuel kopyalar.
 */
export function Comments({ target, targetId, qid, comments, currentUserId }: Props) {
  return (
    <div className="mt-3 border-t border-dashed border-neutral-200 pt-2 dark:border-neutral-800">
      {comments.length > 0 && (
        <ul className="divide-y divide-neutral-200 text-sm dark:divide-neutral-800">
          {comments.map((c) => (
            <li key={c.id} className="py-2">
              <span className="whitespace-pre-wrap text-neutral-700 dark:text-neutral-200">
                {c.body}
              </span>{' '}
              <span className="text-xs text-neutral-500 dark:text-neutral-400">
                –{' '}
                <Link
                  href={`/users/${encodeURIComponent(c.author.username)}`}
                  className="hover:underline"
                >
                  {c.author.username}
                </Link>{' '}
                · {timeAgo(c.created_at)}
                {currentUserId === c.author.id && (
                  <>
                    {' '}
                    ·{' '}
                    <form
                      action={deleteComment.bind(null, c.id, qid)}
                      className="inline"
                    >
                      <button
                        type="submit"
                        className="text-red-600 hover:underline dark:text-red-400"
                      >
                        sil
                      </button>
                    </form>
                  </>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-2">
        {currentUserId !== null ? (
          <CommentForm target={target} targetId={targetId} qid={qid} />
        ) : (
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            Yorum yazmak için{' '}
            <Link href="/login" className="hover:underline">
              giriş yap
            </Link>
            .
          </p>
        )}
      </div>
    </div>
  )
}
