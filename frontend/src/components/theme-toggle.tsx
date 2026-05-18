'use client'

import { useSyncExternalStore } from 'react'

// `.dark` sınıfı tarayıcı durumudur; React dışı olduğu için
// useSyncExternalStore ile okunur (effect içinde setState yok).
function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange)
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })
  return () => observer.disconnect()
}

function isDark() {
  return document.documentElement.classList.contains('dark')
}

/** Açık/koyu tema geçişi; seçim localStorage'da saklanır. */
export function ThemeToggle() {
  const dark = useSyncExternalStore(subscribe, isDark, () => false)

  function toggle() {
    const next = !dark
    document.documentElement.classList.toggle('dark', next)
    try {
      localStorage.setItem('theme', next ? 'dark' : 'light')
    } catch {}
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Tema değiştir"
      title="Tema değiştir"
      className="rounded-md border border-neutral-300 px-2 py-1 text-sm hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
    >
      {dark ? '☀️' : '🌙'}
    </button>
  )
}
