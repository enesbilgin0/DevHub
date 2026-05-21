interface Props {
  defaultValue?: string
  className?: string
}

/** Server-friendly arama: GET form, /questions?q=... */
export function SearchBox({ defaultValue, className }: Props) {
  return (
    <form
      action="/questions"
      method="get"
      role="search"
      className={className}
    >
      <input
        type="search"
        name="q"
        defaultValue={defaultValue}
        placeholder="Sorularda ara…"
        maxLength={80}
        aria-label="Sorularda ara"
        className="w-full rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm placeholder:text-neutral-400 focus:border-neutral-500 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:placeholder:text-neutral-500"
      />
    </form>
  )
}
