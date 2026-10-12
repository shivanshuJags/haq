import { useEffect, useRef, useState } from 'react'
import { sendProfileTurn, streamResults } from './api'
import { applyEvent, emptyResults } from './results'
import { Chat, type ChatMessage } from './components/Chat'
import { Footer } from './components/Footer'
import { Loading } from './components/Loading'
import { ProfileChips } from './components/ProfileChips'
import { ResultsView } from './components/ResultsView'
import { Welcome } from './components/Welcome'
import { t } from './i18n'
import type { Country, Language, Profile, Progress, Results } from './types'

type Screen = 'welcome' | 'chat' | 'loading' | 'results' | 'error'

export default function App() {
  // All app state lives here and flows down to components as props
  // (in Angular you'd likely keep this in a service with signals).
  const [screen, setScreen] = useState<Screen>('welcome')
  const [country, setCountry] = useState<Country>('IN')
  const [language, setLanguage] = useState<Language>('english')
  const [profile, setProfile] = useState<Profile>({})
  const [asked, setAsked] = useState<string[]>([])
  const [answering, setAnswering] = useState<string[]>([])
  const [rounds, setRounds] = useState(0)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [busy, setBusy] = useState(false)
  const [results, setResults] = useState<Results | null>(null)
  const [progress, setProgress] = useState<Progress>({ checking: 0, judged: 0, finished: false })
  const [retry, setRetry] = useState<(() => void) | null>(null)

  const strings = t(language)
  const mainRef = useRef<HTMLElement>(null)

  // A new screen should start at the top, not wherever the chat was scrolled to
  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0 })
  }, [screen])

  function start(chosen: Country, region: string | null) {
    const startLanguage: Language = chosen === 'IN' ? 'hinglish' : 'english'
    setCountry(chosen)
    setLanguage(startLanguage)
    setProfile(region ? { region } : {})
    setMessages([{ role: 'haq', text: t(startLanguage).greeting(chosen) }])
    setScreen('chat')
  }

  async function send(text: string, shownAs: string = text) {
    setMessages((current) => [...current, { role: 'user', text: shownAs }])
    setBusy(true)
    try {
      const reply = await sendProfileTurn({ country, message: text, profile, asked, answering, rounds, language })
      setProfile(reply.profile)
      setLanguage(reply.language)
      setAsked((current) => [...current, ...reply.asking])
      setAnswering(reply.asking)

      const newMessages: ChatMessage[] = []
      if (reply.privacy_note) newMessages.push({ role: 'note', text: reply.privacy_note })
      if (reply.follow_up) {
        setRounds((current) => current + 1)
        newMessages.push({ role: 'haq', text: reply.follow_up.question, options: reply.follow_up.options })
      }
      setMessages((current) => [...current, ...newMessages])

      if (reply.ready) {
        await loadResults(reply.profile, reply.language)
      }
    } catch {
      setMessages((current) => [...current, { role: 'haq', text: t(language).error }])
    } finally {
      setBusy(false)
    }
  }

  async function loadResults(finalProfile: Profile, finalLanguage: Language) {
    setScreen('loading')
    try {
      await streamResults(country, finalProfile, finalLanguage, (event) => {
        if (event.type === 'start') {
          // Rules engine done (~2s): open the results page now, cards will fill in
          setResults(emptyResults(event.currency))
          setProgress({ checking: event.checking, judged: 0, finished: false })
          setScreen('results')
        } else if (event.type === 'progress') {
          setProgress((current) => ({ ...current, judged: event.judged }))
        } else if (event.type === 'done') {
          setProgress((current) => ({ ...current, finished: true }))
        }
        setResults((current) => (current ? applyEvent(current, event) : current))
      })
    } catch {
      setRetry(() => () => loadResults(finalProfile, finalLanguage))
      setScreen('error')
    }
  }

  function removeFact(field: keyof Profile) {
    setProfile((current) => ({ ...current, [field]: null }))
    setAsked((current) => current.filter((name) => name !== field)) // allow Haq to ask again
  }

  function startOver() {
    setProfile({})
    setAsked([])
    setAnswering([])
    setRounds(0)
    setMessages([])
    setResults(null)
    setScreen('welcome')
  }

  return (
    <div className="flex h-full flex-col">
      {screen !== 'welcome' && (
        <header className="flex items-center justify-between border-b border-line bg-white px-4 py-3">
          <button onClick={startOver} className="text-xl font-bold text-brand">
            Haq
          </button>
          <span className="text-sm text-muted">
            {country === 'IN' ? `₹ India${profile.region ? ` · ${profile.region}` : ''}` : '£ United Kingdom'}
          </span>
        </header>
      )}

      <main ref={mainRef} className="flex min-h-0 flex-1 flex-col overflow-x-hidden overflow-y-auto">
        {screen === 'welcome' && <Welcome onStart={start} />}

        {screen === 'chat' && (
          <div className="mx-auto flex min-h-0 w-full max-w-2xl flex-1 flex-col">
            <ProfileChips profile={profile} country={country} strings={strings} onRemove={removeFact} />
            <p className="px-4 pt-3 text-xs text-muted">🔒 {strings.privacy}</p>
            <Chat
              messages={messages}
              busy={busy}
              canShowResults={messages.some((m) => m.role === 'user')}
              strings={strings}
              onSend={(text) => send(text)}
              onSkip={() => send('skip', strings.skip)}
              onShowResults={() => loadResults(profile, language)}
            />
          </div>
        )}

        {screen === 'loading' && <Loading strings={strings} />}

        {screen === 'results' && results && (
          <ResultsView results={results} progress={progress} strings={strings} onStartOver={startOver} />
        )}

        {screen === 'error' && (
          <div className="mx-auto flex max-w-md flex-col items-center gap-4 px-6 py-16 text-center">
            <p>{strings.error}</p>
            <button onClick={() => retry?.()} className="rounded-xl bg-brand px-5 py-2.5 font-semibold text-white">
              {strings.retry}
            </button>
          </div>
        )}
      </main>

      <Footer strings={strings} />
    </div>
  )
}
