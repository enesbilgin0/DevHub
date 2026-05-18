import * as z from 'zod'

// Kurallar backend'deki Pydantic şemalarıyla aynı (devhub/api/schemas.py).

export const LoginSchema = z.object({
  identifier: z
    .string()
    .min(3, { error: 'En az 3 karakter.' })
    .max(255)
    .trim(),
  password: z.string().min(1, { error: 'Şifre gerekli.' }).max(128),
})

export const RegisterSchema = z.object({
  username: z
    .string()
    .min(3, { error: 'En az 3 karakter.' })
    .max(64)
    .regex(/^[A-Za-z0-9_.-]+$/, {
      error: 'Sadece harf, rakam ve . _ - kullanılabilir.',
    })
    .trim(),
  email: z.email({ error: 'Geçerli bir e-posta girin.' }).trim(),
  password: z
    .string()
    .min(8, { error: 'En az 8 karakter.' })
    .max(128),
  bio: z.string().max(500).trim().optional(),
})

export type LoginInput = z.infer<typeof LoginSchema>
export type RegisterInput = z.infer<typeof RegisterSchema>
