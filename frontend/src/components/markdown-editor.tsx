'use client'

import { useState } from 'react'

import { Markdown } from './markdown'

interface Props {
  name: string
  defaultValue?: string
  placeholder?: string
  rows?: number
}

/** Yaz / Önizle sekmeli markdown girişi. */
export function MarkdownEditor({ name, defaultValue = '', placeholder, rows = 10 }: Props) {
  const [value, setValue] = useState(defaultValue)
  const [tab, setTab] = useState<'write' | 'preview'>('write')

  const tabClass = (active: boolean) =>
    `px-3 py-1.5 text-sm rounded-t-md border-b-2 ${
      active
        ? 'border-neutral-900 font-medium dark:border-neutral-100'
        : 'border-transparent text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200'
    }`

  return (
    <div className="rounded-md border border-neutral-300 dark:border-neutral-700">
      <div className="flex gap-1 border-b border-neutral-200 px-2 pt-1 dark:border-neutral-800">
        <button type="button" className={tabClass(tab === 'write')} onClick={() => setTab('write')}>
          Yaz
        </button>
        <button
          type="button"
          className={tabClass(tab === 'preview')}
          onClick={() => setTab('preview')}
        >
          Önizle
        </button>
      </div>

      {/* Değer her zaman gönderilir; sekme sadece görünümü değiştirir. */}
      <textarea
        name={name}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className={`w-full resize-y bg-transparent px-3 py-2 font-mono text-sm outline-none ${
          tab === 'write' ? 'block' : 'hidden'
        }`}
      />
      {tab === 'preview' && (
        <div className="min-h-32 px-3 py-2">
          {value.trim() ? (
            <Markdown>{value}</Markdown>
          ) : (
            <p className="text-sm text-neutral-400 dark:text-neutral-500">
              Önizlenecek bir şey yok.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
