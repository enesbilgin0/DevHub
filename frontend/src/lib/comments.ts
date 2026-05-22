import 'server-only'

import { apiFetch } from './api'

import type { PageResult, UserSummary } from './questions'

export type CommentTarget = 'question' | 'answer'

export interface Comment {
  id: number
  target_type: CommentTarget
  target_id: number
  author: UserSummary
  body: string
  created_at: string
}

export async function listComments(
  target: CommentTarget,
  targetId: number,
): Promise<Comment[]> {
  const base = target === 'question' ? 'questions' : 'answers'
  const res = await apiFetch(`/${base}/${targetId}/comments?page=1&page_size=100`)
  if (res.status === 404) return []
  if (!res.ok) throw new Error('Yorumlar yüklenemedi')
  const data: PageResult<Comment> = await res.json()
  return data.items
}
