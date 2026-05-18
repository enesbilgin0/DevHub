import 'server-only'

import { apiFetch } from './api'
import type { PageResult } from './questions'

export interface UserStats {
  questions: number
  answers: number
  accepted_answers: number
  votes_received: number
}

export interface Badge {
  key: string
  label: string
  description: string
}

export interface UserProfile {
  id: number
  username: string
  bio: string | null
  joined_at: string
  reputation: number
  stats: UserStats
  badges: Badge[]
}

export interface ActivityDay {
  day: string
  count: number
}

export interface UserAnswer {
  id: number
  question_id: number
  question_title: string
  created_at: string
  is_accepted: boolean
  vote_score: number
}

/** Public profil; kullanıcı yoksa null. */
export async function getProfile(username: string): Promise<UserProfile | null> {
  const res = await apiFetch(`/users/${encodeURIComponent(username)}`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Profil yüklenemedi')
  return res.json()
}

export async function getActivity(username: string): Promise<ActivityDay[]> {
  const res = await apiFetch(
    `/users/${encodeURIComponent(username)}/activity?days=365`,
  )
  if (!res.ok) return []
  return res.json()
}

export async function getUserAnswers(username: string): Promise<UserAnswer[]> {
  const res = await apiFetch(
    `/users/${encodeURIComponent(username)}/answers?page=1&page_size=10`,
  )
  if (!res.ok) return []
  const data: PageResult<UserAnswer> = await res.json()
  return data.items
}
