import Link from 'next/link'

import { ThemeToggle } from '@/components/theme-toggle'

import { LoginForm } from './login-form'

export default function LoginPage() {
  return (
    <>
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6">
        <div>
          <h1 className="text-2xl font-semibold">Giriş yap</h1>
          <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
            Kullanıcı adı veya e-posta ile giriş yapın.
          </p>
        </div>
        <LoginForm />
        <p className="text-sm text-neutral-500 dark:text-neutral-400">
          Hesabın yok mu?{' '}
          <Link href="/register" className="font-medium underline">
            Kayıt ol
          </Link>
        </p>
      </main>
    </>
  )
}
