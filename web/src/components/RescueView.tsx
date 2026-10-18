import { useState } from 'react'
import { sendRescue } from '../api'
import { COUNTRIES, countryConfig } from '../config/countries'
import { t } from '../i18n'
import { SAMPLE_LETTERS } from '../samples'
import type { Country, Language, RescueOutcome } from '../types'
import { Loading } from './Loading'

const MAX_PHOTO_SIDE = 1600 // px — plenty to read text, keeps uploads small

/** Shrink a phone photo in the browser before upload (a 12 MP photo is ~5 MB; this makes it ~300 KB). */
function photoToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => {
      const scale = Math.min(1, MAX_PHOTO_SIDE / Math.max(image.width, image.height))
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(image.width * scale)
      canvas.height = Math.round(image.height * scale)
      canvas.getContext('2d')!.drawImage(image, 0, 0, canvas.width, canvas.height)
      URL.revokeObjectURL(image.src)
      resolve(canvas.toDataURL('image/jpeg', 0.85))
    }
    image.onerror = reject
    image.src = URL.createObjectURL(file)
  })
}

interface Props {
  initialCountry: Country
  initialLanguage: Language
}

// Keep the chosen language if the country offers it, otherwise that country's default
function languageFor(country: Country, preferred: Language): Language {
  const { languages } = countryConfig(country)
  return languages.includes(preferred) ? preferred : languages[0]
}

export function RescueView({ initialCountry, initialLanguage }: Props) {
  const [country, setCountry] = useState<Country>(initialCountry)
  const [text, setText] = useState('')
  const [photo, setPhoto] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [outcome, setOutcome] = useState<RescueOutcome | null>(null)

  const language = languageFor(country, initialLanguage)
  const strings = t(language)
  const r = strings.rescue

  async function choosePhoto(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) setPhoto(await photoToDataUrl(file))
    event.target.value = '' // allow choosing the same file again
  }

  async function submit() {
    if (!text.trim() && !photo) {
      setError(r.needText)
      return
    }
    setError(null)
    setBusy(true)
    try {
      setOutcome(await sendRescue({ country, language, ...(photo ? { image: photo } : { letter_text: text }) }))
    } catch {
      setError(strings.error)
    } finally {
      setBusy(false)
    }
  }

  function reset() {
    setOutcome(null)
    setText('')
    setPhoto(null)
  }

  if (busy) return <Loading steps={r.working} />
  if (outcome) return <RescueResult outcome={outcome} language={language} onAnother={reset} />

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <h1 className="text-2xl font-bold text-brand">📄 {r.title}</h1>
      <p className="mt-2 leading-relaxed text-ink">{r.intro}</p>

      <div className="mt-5 inline-flex rounded-xl border border-line bg-white p-1">
        {COUNTRIES.map((option) => (
          <button
            key={option.code}
            onClick={() => setCountry(option.code)}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium ${
              country === option.code ? 'bg-brand text-white' : 'text-muted hover:text-ink'
            }`}
          >
            {option.symbol} {option.name}
          </button>
        ))}
      </div>

      {photo ? (
        <div className="mt-4 flex items-center gap-4 rounded-2xl border border-line bg-white p-3">
          <img src={photo} alt="" className="h-24 w-20 rounded-lg border border-line object-cover" />
          <div>
            <p className="font-medium text-brand-ink">✓ {r.photoReady}</p>
            <button onClick={() => setPhoto(null)} className="mt-1 text-sm text-muted underline">
              {r.removePhoto}
            </button>
          </div>
        </div>
      ) : (
        <>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder={r.pastePlaceholder}
            rows={9}
            className="mt-4 w-full rounded-2xl border border-line bg-white p-4 font-mono text-sm leading-relaxed outline-none focus:border-brand"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <label className="cursor-pointer rounded-xl border border-brand px-4 py-2 text-sm font-medium text-brand-ink hover:bg-brand-soft">
              {r.uploadPhoto}
              {/* capture="environment" opens the back camera directly on phones */}
              <input type="file" accept="image/*" capture="environment" onChange={choosePhoto} className="hidden" />
            </label>
            <button
              onClick={() => setText(SAMPLE_LETTERS[country])}
              className="rounded-xl px-4 py-2 text-sm text-muted underline-offset-2 hover:underline"
            >
              {r.trySample}
            </button>
          </div>
        </>
      )}

      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}

      <button
        onClick={submit}
        className="mt-5 w-full rounded-xl bg-brand py-3 font-semibold text-white hover:bg-brand-ink"
      >
        {r.submit} →
      </button>
      <p className="mt-3 text-xs text-muted">🔒 {r.privacy}</p>
    </div>
  )
}

const VERDICT_STYLE = {
  yes: 'bg-paper text-ink',
  no: 'bg-accent-soft text-ink',
  unclear: 'bg-paper text-ink',
}

function RescueResult({ outcome, language, onAnother }: {
  outcome: RescueOutcome
  language: Language
  onAnother: () => void
}) {
  const r = t(language).rescue
  const result = outcome.rescue
  const [letter, setLetter] = useState(result.appeal_letter)
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(letter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function download() {
    const url = URL.createObjectURL(new Blob([letter], { type: 'text/plain;charset=utf-8' }))
    const link = Object.assign(document.createElement('a'), { href: url, download: 'appeal-letter.txt' })
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 [overflow-wrap:anywhere]">
      <section className="rounded-3xl bg-brand p-6 text-white shadow-lg">
        <p className="text-sm text-white/80">{r.whatHappened}</p>
        <p className="mt-2 text-lg leading-relaxed">{result.summary}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="rounded-full bg-accent px-3 py-1 text-sm font-semibold text-ink">
            → {r.recommendation[result.recommendation]}
          </span>
          {result.deadline && (
            <span className="rounded-full bg-white/15 px-3 py-1 text-sm">⏰ {r.deadline}: {result.deadline}</span>
          )}
        </div>
      </section>

      {(result.scheme_name || outcome.scheme_source_url) && (
        <p className="mt-4 text-sm text-muted">
          {r.scheme}: <span className="font-medium text-ink">{result.scheme_name}</span>
          {outcome.scheme_source_url && (
            <>
              {' · '}
              <a href={outcome.scheme_source_url} target="_blank" rel="noreferrer" className="text-brand underline">
                {r.officialRules} ↗
              </a>
            </>
          )}
        </p>
      )}

      <h2 className="mt-6 text-xs font-semibold uppercase tracking-wide text-muted">{r.reasons}</h2>
      <div className="mt-2 space-y-3">
        {result.reasons.map((reason) => (
          <article key={reason.reason} className="rounded-2xl border border-line bg-white p-4">
            <div className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-red-100 text-sm font-bold text-red-700">✗</span>
              <div>
                <p className="font-semibold">{reason.reason}</p>
                <p className="mt-1 text-sm leading-relaxed">{reason.meaning}</p>
                <span
                  className={`mt-2 inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    reason.fixable ? 'bg-brand-soft text-brand-ink' : 'bg-accent-soft text-ink'
                  }`}
                >
                  {reason.fixable ? r.fixable : r.notFixable}
                </span>
                {reason.how_to_fix && (
                  <p className="mt-2 text-sm">
                    <span className="font-medium">{r.howToFix}:</span> {reason.how_to_fix}
                  </p>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>

      <div className={`mt-4 rounded-2xl border border-line p-4 text-sm ${VERDICT_STYLE[result.rejection_looks_correct]}`}>
        <p className="font-semibold">{r.looksCorrect[result.rejection_looks_correct]}</p>
        <p className="mt-1 leading-relaxed">{result.assessment}</p>
        <p className="mt-2 leading-relaxed text-muted">{result.recommendation_reason}</p>
      </div>

      {result.documents_to_gather.length > 0 && (
        <>
          <h2 className="mt-6 text-xs font-semibold uppercase tracking-wide text-muted">{r.documents}</h2>
          <ul className="mt-2 space-y-1.5 rounded-2xl border border-line bg-white p-4 text-sm">
            {result.documents_to_gather.map((document) => (
              <li key={document} className="flex gap-2">
                <span className="text-brand">☐</span>
                {document}
              </li>
            ))}
          </ul>
        </>
      )}

      <h2 className="mt-6 text-xs font-semibold uppercase tracking-wide text-muted">✉️ {r.letter}</h2>
      <p className="mt-1 text-sm text-muted">{r.letterHint}</p>
      <textarea
        value={letter}
        onChange={(event) => setLetter(event.target.value)}
        rows={16}
        className="mt-2 w-full rounded-2xl border border-line bg-white p-4 font-mono text-sm leading-relaxed outline-none focus:border-brand"
      />
      <div className="mt-2 flex gap-2">
        <button onClick={copy} className="rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-ink">
          {copied ? r.copied : r.copy}
        </button>
        <button onClick={download} className="rounded-xl border border-brand px-4 py-2 text-sm font-semibold text-brand-ink hover:bg-brand-soft">
          ⬇ {r.download}
        </button>
      </div>

      <button
        onClick={onAnother}
        className="mt-8 w-full rounded-xl border border-brand py-3 font-semibold text-brand-ink hover:bg-brand-soft"
      >
        {r.another}
      </button>
    </div>
  )
}
