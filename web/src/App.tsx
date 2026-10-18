import { useEffect, useRef, useState } from 'react'
import { sendProfileTurn, streamResults } from './api'
import { applyEvent, emptyResults } from './results'
import { Chat, type ChatMessage } from './components/Chat'
import { Footer } from './components/Footer'
import { Loading } from './components/Loading'
import { ProfileChips } from './components/ProfileChips'
import { RescueView } from './components/RescueView'
import { ResultsView } from './components/ResultsView'
import { Welcome } from './components/Welcome'
import { countryConfig } from './config/countries'
import { t } from './i18n'
import { hideIdNumbers } from './privacy'
import type { Country, Language, Profile, Progress, Results } from './types'

type Screen = 'welcome' | 'chat' | 'loading' | 'results' | 'error' | 'rescue'

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

  // Each chat/search gets a number. Going back bumps it, so a reply or results stream that is still
  // arriving from the old chat is ignored instead of pulling the user back into it.
  const runRef = useRef(0)

  // Phone/browser back button: leaving the welcome screen adds one history entry, so "back"
  // returns to welcome (and resets) instead of leaving the site.
  useEffect(() => {
    if (screen !== 'welcome' && !window.history.state?.haq) {
      window.history.pushState({ haq: true }, '')
    }
  }, [screen])

  useEffect(() => {
    const onBack = () => reset()
    window.addEventListener('popstate', onBack)
    return () => window.removeEventListener('popstate', onBack)
  }, [])

  // `need` is set when the user tapped a category on the welcome screen
  function start(chosen: Country, region: string | null, chosenLanguage: Language, need?: string) {
    const strings = t(chosenLanguage)
    setCountry(chosen)
    setLanguage(chosenLanguage)
    setProfile({ ...(region ? { region } : {}), ...(need ? { needs: need } : {}) })
    setMessages([{ role: 'haq', text: need ? strings.greetingWithNeed(need) : strings.greeting(chosen) }])
    setScreen('chat')
  }

  function openRescue(chosen: Country, chosenLanguage: Language) {
    setCountry(chosen)
    setLanguage(chosenLanguage)
    setScreen('rescue')
  }

  async function send(text: string, shownAs: string = text) {
    const run = runRef.current
    setMessages((current) => [...current, { role: 'user', text: shownAs }])
    setBusy(true)
    try {
      const reply = await sendProfileTurn({ country, message: text, profile, asked, answering, rounds, language })
      if (run !== runRef.current) return // user went back meanwhile
      setProfile(reply.profile)
      setLanguage(reply.language)
      setAsked((current) => [...current, ...reply.asking])
      setAnswering(reply.asking)

      if (reply.privacy_note) {
        // The server removed an ID number — hide it in the user's own bubble too
        setMessages((current) =>
          current.map((message, index) =>
            index === current.length - 1 && message.role === 'user' ? { ...message, text: hideIdNumbers(message.text) } : message,
          ),
        )
      }
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
      if (run !== runRef.current) return
      setMessages((current) => [...current, { role: 'haq', text: t(language).error }])
    } finally {
      setBusy(false)
    }
  }

  async function loadResults(finalProfile: Profile, finalLanguage: Language) {
    const run = runRef.current
    setScreen('loading')
    try {
      await streamResults(country, finalProfile, finalLanguage, (event) => {
        if (run !== runRef.current) return // user went back meanwhile
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
      if (run !== runRef.current) return
      setRetry(() => () => loadResults(finalProfile, finalLanguage))
      setScreen('error')
    }
  }

  function removeFact(field: keyof Profile) {
    setProfile((current) => ({ ...current, [field]: null }))
    setAsked((current) => current.filter((name) => name !== field)) // allow Haq to ask again
  }

  // Back to the welcome screen with a clean slate
  function reset() {
    runRef.current += 1
    setBusy(false)
    setProfile({})
    setAsked([])
    setAnswering([])
    setRounds(0)
    setMessages([])
    setResults(null)
    setScreen('welcome')
  }

  // In-app back/home buttons: go through browser history so the phone's back button stays in sync
  function startOver() {
    if (window.history.state?.haq) window.history.back() // fires popstate -> reset()
    else reset()
  }

  return (
    <div className="flex h-full flex-col">
      {screen !== 'welcome' && (
        <header className="flex items-center justify-between border-b border-line bg-white px-4 py-3">
          <button onClick={startOver} className="flex items-center gap-2 text-xl font-bold text-brand" aria-label={strings.back}>
            <span aria-hidden className="text-lg font-normal">←</span>
            Haq
          </button>
          <span className="text-sm text-muted">
            {screen === 'rescue'
              ? '📄 Rejection Rescue'
              : `${countryConfig(country).symbol} ${countryConfig(country).name}${profile.region ? ` · ${profile.region}` : ''}`}
          </span>
        </header>
      )}

      <main ref={mainRef} className="flex min-h-0 flex-1 flex-col overflow-x-hidden overflow-y-auto">
        {screen === 'welcome' && <Welcome onStart={start} onRescue={openRescue} />}

        {screen === 'chat' && (
          <div className="mx-auto flex min-h-0 w-full max-w-2xl flex-1 flex-col">
            <ProfileChips profile={profile} country={country} strings={strings} onRemove={removeFact} />
            <p className="hide-when-typing px-4 pt-3 text-xs text-muted">🔒 {strings.privacy}</p>
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

        {screen === 'loading' && <Loading steps={strings.loadingSteps} />}

        {screen === 'rescue' && <RescueView initialCountry={country} initialLanguage={language} />}

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

        {/* Full disclaimer scrolls with the page; the chat keeps its space with a one-line version below */}
        {screen !== 'chat' && <Footer strings={strings} />}
      </main>

      {screen === 'chat' && (
        <div className="hide-when-typing">
          <Footer strings={strings} compact />
        </div>
      )}
    </div>
  )
}
