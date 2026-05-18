import Link from 'next/link'

import { ThemeToggle } from '@/components/theme-toggle'

import { RegisterForm } from './register-form'

export default function RegisterPage() {
  return (
    <>
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6 py-12">
        <div>
          <h1 className="text-2xl font-semibold">Kayıt ol</h1>
          <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
            Yeni bir DevHub hesabı oluştur.
          </p>
        </div>
        <RegisterForm />
        <p className="text-sm text-neutral-500 dark:text-neutral-400">
          Zaten hesabın var mı?{' '}
          <Link href="/login" className="font-medium underline">
            Giriş yap
          </Link>
        </p>
      </main>
    </>
  )
}
