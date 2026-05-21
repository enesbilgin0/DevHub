import 'server-only'

import { apiFetch } from './api'
import type { PageResult } from './questions'

export interface TagOut {
  id: number
  name: string
  description: string | null
  question_count: number
}

export type TagSort = 'questions' | 'name'

export interface ListTagsParams {
  page?: number
  pageSize?: number
  sort?: TagSort
  search?: string
}

export async function listTags({
  page = 1,
  pageSize = 30,
  sort = 'questions',
  search,
}: ListTagsParams): Promise<PageResult<TagOut>> {
  const qs = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    sort,
  })
  if (search) qs.set('search', search)
  const res = await apiFetch(`/tags?${qs.toString()}`)
  if (!res.ok) throw new Error('Etiketler yüklenemedi')
  return res.json()
}
