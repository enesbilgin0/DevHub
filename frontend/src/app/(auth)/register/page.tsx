import Link from 'next/link'

import { RegisterForm } from './register-form'

export default function RegisterPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6 py-12">
      <div>
        <h1 className="text-2xl font-semibold">Kayıt ol</h1>
        <p className="mt-1 text-sm text-neutral-500">Yeni bir DevHub hesabı oluştur.</p>
      </div>
      <RegisterForm />
      <p className="text-sm text-neutral-500">
        Zaten hesabın var mı?{' '}
        <Link href="/login" className="font-medium underline">
          Giriş yap
        </Link>
      </p>
    </main>
  )
}
