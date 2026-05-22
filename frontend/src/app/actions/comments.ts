'use server'

import { revalidatePath } from 'next/cache'

import { authedFetch } from '@/lib/server-api'

import type { CommentTarget } from '@/lib/comments'

export interface CommentResult {
  error?: string
  ok?: boolean
}

export async function createComment(
  target: CommentTarget,
  targetId: number,
  qid: number,
  formData: FormData,
): Promise<CommentResult> {
  const body = String(formData.get('body') ?? '').trim()
  if (body.length < 5 || body.length > 600) {
    return { error: 'Yorum 5–600 karakter olmalı.' }
  }
  const base = target === 'question' ? 'questions' : 'answers'
  const res = await authedFetch(`/${base}/${targetId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ body }),
  })
  if (res.status === 401) return { error: 'Yorum için giriş yapmalısın.' }
  if (res.status === 404) return { error: 'Hedef bulunamadı.' }
  if (!res.ok) return { error: 'Yorum eklenemedi.' }
  revalidatePath(`/questions/${qid}`)
  return { ok: true }
}

export async function deleteComment(cid: number, qid: number): Promise<void> {
  await authedFetch(`/comments/${cid}`, { method: 'DELETE' })
  revalidatePath(`/questions/${qid}`)
}
