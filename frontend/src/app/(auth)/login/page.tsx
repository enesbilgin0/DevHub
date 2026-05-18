import Link from 'next/link'

import { LoginForm } from './login-form'

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-6">
      <div>
        <h1 className="text-2xl font-semibold">Giriş yap</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Kullanıcı adı veya e-posta ile giriş yapın.
        </p>
      </div>
      <LoginForm />
      <p className="text-sm text-neutral-500">
        Hesabın yok mu?{' '}
        <Link href="/register" className="font-medium underline">
          Kayıt ol
        </Link>
      </p>
    </main>
  )
}
