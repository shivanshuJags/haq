import { useEffect, useRef, useState } from 'react'
import type { Strings } from '../i18n'

export interface ChatMessage {
  role: 'haq' | 'user' | 'note'
  text: string
  options?: string[]
}

interface Props {
  messages: ChatMessage[]
  busy: boolean
  canShowResults: boolean
  strings: Strings
  onSend: (text: string) => void
  onSkip: () => void
  onShowResults: () => void
}

export function Chat({ messages, busy, canShowResults, strings, onSend, onSkip, onShowResults }: Props) {
  const [draft, setDraft] = useState('')
  const listRef = useRef<HTMLDivElement>(null)

  // Keep the newest message in view: after every message, and when the phone keyboard opens or closes.
  // Scroll only the message list — scrollIntoView() would also scroll the whole page up on phones.
  useEffect(() => {
    const list = listRef.current
    list?.scrollTo({ top: list.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  useEffect(() => {
    const viewport = window.visualViewport
    const toBottom = () => listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
    viewport?.addEventListener('resize', toBottom)
    return () => viewport?.removeEventListener('resize', toBottom)
  }, [])

  const lastMessage = messages[messages.length - 1]
  const quickReplies = !busy && lastMessage?.role === 'haq' ? lastMessage.options ?? [] : []
  const waitingForAnswer = !busy && lastMessage?.role === 'haq' && messages.some((m) => m.role === 'user')

  function submit(event: React.FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || busy) return
    onSend(text)
    setDraft('')
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.map((message, index) => (
          <Bubble key={index} message={message} />
        ))}
        {busy && (
          <div className="flex items-center gap-2 text-sm text-muted">
            <span className="h-2 w-2 animate-pulse rounded-full bg-brand" />
            {strings.thinking}
          </div>
        )}
      </div>

      <div className="border-t border-line bg-white px-4 pb-4 pt-3">
        {quickReplies.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {quickReplies.map((option) => (
              <button
                key={option}
                onClick={() => onSend(option)}
                className="rounded-full border border-brand px-3 py-1.5 text-sm text-brand-ink transition hover:bg-brand hover:text-white"
              >
                {option}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={submit} className="flex gap-2">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={strings.placeholder}
            disabled={busy}
            className="min-w-0 flex-1 rounded-xl border border-line bg-paper px-4 py-3 outline-none focus:border-brand disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className="rounded-xl bg-brand px-5 font-semibold text-white transition hover:bg-brand-ink disabled:opacity-40"
          >
            {strings.send}
          </button>
        </form>

        <div className="mt-3 flex items-center justify-between gap-2">
          {waitingForAnswer ? (
            <button onClick={onSkip} className="text-sm text-muted underline-offset-2 hover:underline">
              {strings.skip}
            </button>
          ) : (
            <span />
          )}
          {canShowResults && (
            <button
              onClick={onShowResults}
              disabled={busy}
              className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-ink transition hover:brightness-95 disabled:opacity-40"
            >
              {strings.showResults} →
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function Bubble({ message }: { message: ChatMessage }) {
  if (message.role === 'note') {
    return (
      <p className="mx-auto max-w-sm rounded-lg bg-accent-soft px-3 py-2 text-center text-xs text-ink">
        🔒 {message.text}
      </p>
    )
  }
  const mine = message.role === 'user'
  return (
    <div className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
      <p
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 leading-relaxed ${
          mine ? 'rounded-br-sm bg-brand text-white' : 'rounded-bl-sm border border-line bg-white'
        }`}
      >
        {message.text}
      </p>
    </div>
  )
}
