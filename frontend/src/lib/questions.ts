import 'server-only'

import { apiFetch } from './api'

export interface UserSummary {
  id: number
  username: string
  reputation: number
}

export interface QuestionSummary {
  id: number
  title: string
  author: UserSummary
  tags: string[]
  created_at: string
  view_count: number
  vote_score: number
  answer_count: number
  has_accepted: boolean
}

export interface QuestionDetail extends QuestionSummary {
  body: string
}

export interface AnswerOut {
  id: number
  question_id: number
  author: UserSummary
  body: string
  created_at: string
  is_accepted: boolean
  vote_score: number
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type QuestionSort = 'created' | 'votes' | 'views' | 'answers'

export interface ListParams {
  page?: number
  sort?: QuestionSort
  tag?: string
  author?: string
  q?: string
  pageSize?: number
}

/** Soru listesi (public okuma). */
export async function listQuestions({
  page = 1,
  sort = 'created',
  tag,
  author,
  q,
  pageSize = 20,
}: ListParams): Promise<PageResult<QuestionSummary>> {
  const qs = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    sort,
    desc: 'true',
  })
  if (tag) qs.set('tag', tag)
  if (author) qs.set('author', author)
  if (q) qs.set('q', q)
  const res = await apiFetch(`/questions?${qs.toString()}`)
  if (!res.ok) throw new Error('Sorular yüklenemedi')
  return res.json()
}

/** Soru detayı; bulunamazsa null. */
export async function getQuestion(id: number): Promise<QuestionDetail | null> {
  const res = await apiFetch(`/questions/${id}`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Soru yüklenemedi')
  return res.json()
}

/** Sorunun cevapları (kabul edilen önce, sonra oy, sonra tarih). */
export async function listAnswers(qid: number): Promise<AnswerOut[]> {
  const res = await apiFetch(`/questions/${qid}/answers?page=1&page_size=100`)
  if (res.status === 404) return []
  if (!res.ok) throw new Error('Cevaplar yüklenemedi')
  const data: PageResult<AnswerOut> = await res.json()
  return data.items
}
