import { useState } from 'react'
import { checklistAsText, combinedChecklist } from '../documents'
import type { Strings } from '../i18n'
import type { ResultCard } from '../types'

interface Props {
  cards: ResultCard[]
  strings: Strings
}

// US-303: one combined list of documents for every scheme the person likely qualifies for
export function DocumentChecklist({ cards, strings }: Props) {
  const items = combinedChecklist(cards)
  const [done, setDone] = useState<Set<string>>(new Set()) // ticked off (this visit only)
  const [copied, setCopied] = useState(false)

  if (items.length === 0) return null

  function toggle(document: string) {
    setDone((current) => {
      const next = new Set(current)
      if (next.has(document)) next.delete(document)
      else next.add(document)
      return next
    })
  }

  async function copy() {
    await navigator.clipboard.writeText(checklistAsText(items, strings.checklistTitle, done))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function download() {
    const blob = new Blob([checklistAsText(items, strings.checklistTitle, done)], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    Object.assign(document.createElement('a'), { href: url, download: 'haq-documents.txt' }).click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="rounded-2xl border border-line bg-white p-5 [overflow-wrap:anywhere]">
      <h2 className="text-lg font-semibold">📋 {strings.checklistTitle}</h2>
      <p className="mt-1 text-sm text-muted">{strings.checklistHint}</p>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item.document}>
            <label className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={done.has(item.document)}
                onChange={() => toggle(item.document)}
                className="mt-1 h-4 w-4 shrink-0 accent-[var(--color-brand)]"
              />
              <span className={done.has(item.document) ? 'text-muted line-through' : ''}>
                {item.document}
                <span className="ml-2 text-xs text-muted" title={item.schemes.join(', ')}>
                  · {strings.neededFor(item.schemes.length)}
                </span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      <div className="mt-4 flex gap-2">
        <button onClick={copy} className="rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-ink">
          {copied ? strings.copied : strings.copyList}
        </button>
        <button
          onClick={download}
          className="rounded-xl border border-brand px-4 py-2 text-sm font-semibold text-brand-ink hover:bg-brand-soft"
        >
          ⬇ {strings.downloadList}
        </button>
      </div>
    </section>
  )
}
