import { useEffect, useState } from 'react'
import { fetchHighlights } from '../api'
import { COUNTRIES, LANGUAGE_NAMES, countryConfig } from '../config/countries'
import { t } from '../i18n'
import { Dots } from './Dots'
import type { Country, Highlights, Language, SchemeLink } from '../types'

interface Props {
  onStart: (country: Country, region: string | null, language: Language, need?: string) => void
  onRescue: (country: Country, language: Language) => void
}

// An icon per category (names come from myScheme / our UK groups). Unknown names get a generic one.
const CATEGORY_ICONS: [RegExp, string][] = [
  [/educat|learning/i, '🎓'],
  [/business|entrepreneur/i, '💼'],
  [/agricultur|rural/i, '🌾'],
  [/skill|employment|looking for work/i, '🛠️'],
  [/bank|financ|insurance|low income/i, '🏦'],
  [/health/i, '🩺'],
  [/women|child|famil/i, '👪'],
  [/social|welfare/i, '🤝'],
  [/housing|shelter/i, '🏠'],
  [/science|it &|communication/i, '💻'],
  [/sport|culture/i, '🏅'],
  [/disab|unable to work/i, '♿'],
  [/carer/i, '🫶'],
  [/bereave/i, '🕊️'],
]

function categoryIcon(name: string): string {
  return CATEGORY_ICONS.find(([pattern]) => pattern.test(name))?.[1] ?? '📋'
}

// Dates in the reader's language (e.g. "6 नव॰ 2024")
const LOCALES: Record<Language, string> = {
  english: 'en-IN', hinglish: 'en-IN', hindi: 'hi-IN', marathi: 'mr-IN', bengali: 'bn-IN',
}

function formatDate(date: string, language: Language, country: Country): string {
  const locale = country === 'UK' ? 'en-GB' : LOCALES[language]
  return new Date(date).toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' })
}

export function Welcome({ onStart, onRescue }: Props) {
  const [country, setCountry] = useState<Country>(COUNTRIES[0].code)
  const [region, setRegion] = useState<string>('')
  const [language, setLanguage] = useState<Language>(COUNTRIES[0].languages[0])
  const [showAllPopular, setShowAllPopular] = useState(false)
  // Remember which country/state the lists belong to, so old lists never show for a new choice
  const [loaded, setLoaded] = useState<{ key: string; data: Highlights } | null>(null)
  const [failedKey, setFailedKey] = useState<string | null>(null)

  const config = countryConfig(country)
  const strings = t(language)
  const chosenState = config.states?.find((state) => state.name === region)
  const key = `${country}|${region}`
  const highlights = loaded?.key === key ? loaded.data : null
  const loadingLists = !highlights && failedKey !== key

  // Reload the welcome lists when the country or state changes (like an Angular effect on a signal).
  // `ignore` drops a slow answer that arrives after the user already picked something else.
  useEffect(() => {
    let ignore = false
    fetchHighlights(country, region || null)
      .then((data) => !ignore && setLoaded({ key: `${country}|${region}`, data }))
      .catch(() => !ignore && setFailedKey(`${country}|${region}`)) // the lists are extra; the app works without them
    return () => {
      ignore = true
    }
  }, [country, region])

  function chooseCountry(code: Country) {
    setCountry(code)
    setRegion('')
    setLanguage(countryConfig(code).languages[0]) // each country starts in its own default language
  }

  const start = (need?: string) => onStart(country, region || null, language, need)

  return (
    <div className="mx-auto w-full max-w-2xl px-4 pb-10 pt-8 sm:px-6">
      {/* Hero */}
      <h1 className="text-5xl font-bold tracking-tight text-brand">Haq</h1>
      <p className="mt-1 text-sm font-medium text-accent">हक़ · what's yours</p>
      <p className="mt-4 text-lg leading-relaxed text-ink">{strings.tagline}</p>

      {/* Choices — one card, like myScheme's eligibility form */}
      <section className="mt-6 rounded-2xl border border-line bg-white p-4 shadow-sm sm:p-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={strings.chooseCountry}>
            <select
              value={country}
              onChange={(event) => chooseCountry(event.target.value as Country)}
              className={SELECT}
              aria-label={strings.selectCountry}
            >
              {COUNTRIES.map((option) => (
                <option key={option.code} value={option.code}>
                  {option.symbol}  {option.name}
                  {option.nativeName ? ` · ${option.nativeName}` : ''}
                </option>
              ))}
            </select>
          </Field>

          {config.states && (
            <Field label={strings.chooseState}>
              <select
                value={region}
                onChange={(event) => setRegion(event.target.value)}
                className={SELECT}
                aria-label={strings.selectState}
              >
                <option value="">{strings.selectState}</option>
                {config.states.map((state) => (
                  <option key={state.name} value={state.name}>
                    {state.name}
                    {state.coverage === 'full' ? ' ★' : ''}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-muted">
                {chosenState?.coverage === 'full' ? `★ ${strings.stateFull}` : strings.stateCentral}
              </p>
            </Field>
          )}
        </div>

        {config.languages.length > 1 && (
          <Field label={strings.chooseLanguage} className="mt-4">
            <div className="flex flex-wrap gap-2" role="radiogroup" aria-label={strings.chooseLanguage}>
              {config.languages.map((option) => (
                <button
                  key={option}
                  role="radio"
                  aria-checked={language === option}
                  onClick={() => setLanguage(option)}
                  title={LANGUAGE_NAMES[option].english}
                  className={`rounded-full border px-4 py-1.5 text-sm font-medium transition ${
                    language === option
                      ? 'border-brand bg-brand text-white'
                      : 'border-line bg-white text-ink hover:border-brand'
                  }`}
                >
                  {LANGUAGE_NAMES[option].native}
                </button>
              ))}
            </div>
          </Field>
        )}

        <button
          onClick={() => start()}
          className="mt-5 w-full rounded-xl bg-brand px-5 py-3 text-lg font-semibold text-white transition hover:bg-brand-ink"
        >
          {strings.findBenefits} →
        </button>
        <p className="mt-2 text-center text-xs text-muted">{strings.moreCountries}</p>
      </section>

      {loadingLists && <Dots label={strings.loadingSchemes} />}

      {/* Numbers */}
      {highlights && (
        <p className="mt-6 text-center text-sm text-muted">
          <span className="text-2xl font-bold text-brand">{strings.schemesCount(highlights.schemes)}</span>
          <br />
          {strings.schemesSplit(highlights.national, highlights.state)}
        </p>
      )}

      {/* Categories — tapping one starts the chat with that need */}
      {highlights && highlights.categories.length > 0 && (
        <section className="mt-8">
          <h2 className={HEADING}>{strings.browseCategories}</h2>
          <p className="mt-1 text-xs text-muted">{strings.categoryHint}</p>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {highlights.categories.map((category) => (
              <button
                key={category.name}
                onClick={() => start(category.name)}
                className="flex flex-col items-start gap-1 rounded-xl border border-line bg-white p-3 text-left transition hover:border-brand"
              >
                <span className="text-2xl" aria-hidden>
                  {categoryIcon(category.name)}
                </span>
                <span className="text-sm font-medium leading-snug">{category.name}</span>
                <span className="text-xs text-muted">{category.count}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {highlights && highlights.popular.length > 0 && (
        <section className="mt-8">
          <h2 className={HEADING}>{strings.popularHeading}</h2>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {highlights.popular.slice(0, showAllPopular ? undefined : POPULAR_SHOWN).map((scheme) => (
              <SchemeItem key={scheme.id} scheme={scheme} badge={scheme.is_state_scheme ? strings.stateScheme : null} />
            ))}
          </ul>
          {!showAllPopular && highlights.popular.length > POPULAR_SHOWN && (
            <button onClick={() => setShowAllPopular(true)} className="mt-2 text-sm font-medium text-brand hover:underline">
              {strings.showMore(highlights.popular.length - POPULAR_SHOWN)} ↓
            </button>
          )}
        </section>
      )}

      {highlights && highlights.recent.length > 0 && (
        <section className="mt-8">
          <h2 className={HEADING}>{strings.recentHeading(country)}</h2>
          <ul className="mt-3 grid gap-2">
            {highlights.recent.map((scheme) => (
              <SchemeItem
                key={scheme.id}
                scheme={scheme}
                badge={scheme.date ? `${strings.dateLabel(country)} ${formatDate(scheme.date, language, country)}` : null}
              />
            ))}
          </ul>
        </section>
      )}

      {/* US-501: second way in — for people who already applied and were rejected */}
      <button
        onClick={() => onRescue(country, language)}
        className="mt-10 flex w-full items-center gap-4 rounded-2xl border border-line bg-white p-4 text-left transition hover:border-brand"
      >
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-accent-soft text-2xl" aria-hidden>
          📄
        </span>
        <span>
          <span className="block font-semibold">{strings.rescue.entry}</span>
          <span className="block text-sm text-muted">{strings.rescue.entryHint} →</span>
        </span>
      </button>
    </div>
  )
}

const POPULAR_SHOWN = 6
const SELECT =
  'w-full rounded-xl border border-line bg-white px-3 py-2.5 text-base text-ink focus:border-brand focus:outline-none'
const HEADING = 'text-sm font-semibold uppercase tracking-wide text-muted'

function Field({ label, className = '', children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <div className={className}>
      <span className="mb-1.5 block text-sm font-semibold text-ink">{label}</span>
      {children}
    </div>
  )
}

/** A scheme name linking to its official page — the full check happens in the chat. */
function SchemeItem({ scheme, badge }: { scheme: SchemeLink; badge: string | null }) {
  return (
    <li>
      <a
        href={scheme.source_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block h-full rounded-xl border border-line bg-white p-3 transition hover:border-brand"
      >
        {badge && (
          <span className="mb-1 inline-block rounded bg-brand-soft px-1.5 py-0.5 text-[11px] font-medium text-brand-ink">
            {badge}
          </span>
        )}
        <span className="block font-medium leading-snug text-ink">{scheme.name} ↗</span>
        {scheme.summary && <span className="mt-1 line-clamp-2 block text-sm text-muted">{scheme.summary}</span>}
      </a>
    </li>
  )
}
