'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import * as z from 'zod'

import { authedFetch } from '@/lib/server-api'

export interface FormState {
  error?: string
  fieldErrors?: Record<string, string[]>
}

interface VoteResult {
  score?: number
  error?: string
}

const QuestionSchema = z.object({
  title: z.string().min(10, { error: 'Başlık en az 10 karakter.' }).max(300),
  body: z.string().min(20, { error: 'İçerik en az 20 karakter.' }).max(20000),
  tags: z.array(z.string()).max(5, { error: 'En fazla 5 etiket.' }),
})

function parseTags(raw: FormDataEntryValue | null): string[] {
  return String(raw ?? '')
    .split(',')
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean)
    .slice(0, 5)
}

function flatten(error: z.ZodError): Record<string, string[]> {
  const out: Record<string, string[]> = {}
  for (const issue of error.issues) {
    const key = String(issue.path[0] ?? 'form')
    ;(out[key] ??= []).push(issue.message)
  }
  return out
}

export async function createQuestion(
  _prev: FormState | undefined,
  formData: FormData,
): Promise<FormState> {
  const parsed = QuestionSchema.safeParse({
    title: formData.get('title'),
    body: formData.get('body'),
    tags: parseTags(formData.get('tags')),
  })
  if (!parsed.success) return { fieldErrors: flatten(parsed.error) }

  const res = await authedFetch('/questions', {
    method: 'POST',
    body: JSON.stringify(parsed.data),
  })
  if (res.status === 401) return { error: 'Soru sormak için giriş yapmalısın.' }
  if (!res.ok) return { error: 'Soru oluşturulamadı. Tekrar dene.' }

  const created = (await res.json()) as { id: number }
  revalidatePath('/questions')
  redirect(`/questions/${created.id}`)
}

export async function updateQuestion(
  qid: number,
  _prev: FormState | undefined,
  formData: FormData,
): Promise<FormState> {
  const parsed = QuestionSchema.safeParse({
    title: formData.get('title'),
    body: formData.get('body'),
    tags: parseTags(formData.get('tags')),
  })
  if (!parsed.success) return { fieldErrors: flatten(parsed.error) }

  const res = await authedFetch(`/questions/${qid}`, {
    method: 'PATCH',
    body: JSON.stringify(parsed.data),
  })
  if (res.status === 401) return { error: 'Giriş yapmalısın.' }
  if (res.status === 403) return { error: 'Bu soruyu düzenleyemezsin.' }
  if (res.status === 404) return { error: 'Soru bulunamadı.' }
  if (!res.ok) return { error: 'Soru güncellenemedi.' }

  revalidatePath(`/questions/${qid}`)
  revalidatePath('/questions')
  redirect(`/questions/${qid}`)
}

export async function updateAnswer(
  aid: number,
  qid: number,
  _prev: FormState | undefined,
  formData: FormData,
): Promise<FormState> {
  const body = String(formData.get('body') ?? '').trim()
  if (body.length < 10 || body.length > 20000) {
    return { fieldErrors: { body: ['Cevap 10–20000 karakter olmalı.'] } }
  }
  const res = await authedFetch(`/answers/${aid}`, {
    method: 'PATCH',
    body: JSON.stringify({ body }),
  })
  if (res.status === 401) return { error: 'Giriş yapmalısın.' }
  if (res.status === 403) return { error: 'Bu cevabı düzenleyemezsin.' }
  if (!res.ok) return { error: 'Cevap güncellenemedi.' }
  revalidatePath(`/questions/${qid}`)
  return {}
}

export async function createAnswer(
  qid: number,
  _prev: FormState | undefined,
  formData: FormData,
): Promise<FormState> {
  const body = String(formData.get('body') ?? '').trim()
  if (body.length < 10) {
    return { fieldErrors: { body: ['Cevap en az 10 karakter.'] } }
  }

  const res = await authedFetch(`/questions/${qid}/answers`, {
    method: 'POST',
    body: JSON.stringify({ body }),
  })
  if (res.status === 401) return { error: 'Cevap yazmak için giriş yapmalısın.' }
  if (!res.ok) return { error: 'Cevap gönderilemedi. Tekrar dene.' }

  revalidatePath(`/questions/${qid}`)
  return {}
}

async function castVote(
  base: string,
  qid: number,
  value: number,
): Promise<VoteResult> {
  const res =
    value === 0
      ? await authedFetch(`${base}/vote`, { method: 'DELETE' })
      : await authedFetch(`${base}/vote`, {
          method: 'POST',
          body: JSON.stringify({ value }),
        })
  if (res.status === 401) return { error: 'Oy vermek için giriş yapmalısın.' }
  if (res.status === 400) return { error: 'Kendi içeriğine oy veremezsin.' }
  if (!res.ok) return { error: 'Oy işlenemedi.' }
  const data = (await res.json()) as { score: number }
  revalidatePath(`/questions/${qid}`)
  return { score: data.score }
}

export async function voteQuestion(qid: number, value: number): Promise<VoteResult> {
  return castVote(`/questions/${qid}`, qid, value)
}

export async function voteAnswer(
  aid: number,
  qid: number,
  value: number,
): Promise<VoteResult> {
  return castVote(`/answers/${aid}`, qid, value)
}

export async function acceptAnswer(
  aid: number,
  qid: number,
): Promise<{ ok?: boolean; error?: string }> {
  const res = await authedFetch(`/answers/${aid}/accept`, { method: 'POST' })
  if (res.status === 403) return { error: 'Sadece soru sahibi kabul edebilir.' }
  if (!res.ok) return { error: 'İşlem başarısız.' }
  revalidatePath(`/questions/${qid}`)
  return { ok: true }
}

export async function deleteQuestion(qid: number): Promise<void> {
  const res = await authedFetch(`/questions/${qid}`, { method: 'DELETE' })
  if (res.ok || res.status === 204) {
    revalidatePath('/questions')
    redirect('/questions')
  }
}

export async function deleteAnswer(aid: number, qid: number): Promise<void> {
  await authedFetch(`/answers/${aid}`, { method: 'DELETE' })
  revalidatePath(`/questions/${qid}`)
}
