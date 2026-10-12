import { formatMoney, type Strings } from '../i18n'
import type { Progress, Results } from '../types'
import { SchemeCard } from './SchemeCard'

interface Props {
  results: Results
  progress: Progress
  strings: Strings
  onStartOver: () => void
}

export function ResultsView({ results, progress, strings, onStartOver }: Props) {
  const { cards, other_cards, currency } = results
  const showRange = results.potential_yearly > results.total_yearly
  const percent = progress.checking ? Math.round((progress.judged / progress.checking) * 100) : 0

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <section className="rounded-3xl bg-brand p-6 text-white shadow-lg">
        <p className="text-sm text-white/80">{strings.yourEntitlements}</p>
        {results.potential_yearly > 0 ? (
          <p className="mt-1 text-4xl font-bold tabular-nums">
            {formatMoney(results.total_yearly || results.potential_yearly, currency)}
            <span className="ml-2 text-base font-normal text-white/80">/ {strings.perYear}</span>
          </p>
        ) : null}
        {showRange && results.total_yearly > 0 && (
          <p className="mt-1 text-sm text-white/80">
            {strings.upTo} {formatMoney(results.potential_yearly, currency)}
          </p>
        )}
        {/* "0 schemes found" reads like bad news while Ultra is still checking — wait for the first card */}
        {(cards.length > 0 || progress.finished) && (
          <p className="mt-3 font-medium">{strings.schemesFound(cards.length)}</p>
        )}

        {/* While Ultra is still judging: a live progress bar */}
        {!progress.finished && (
          <div className="mt-4" role="status" aria-live="polite">
            <div className="h-1.5 overflow-hidden rounded-full bg-white/25">
              <div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${percent}%` }} />
            </div>
            <p className="mt-2 text-xs text-white/85">{strings.checking(progress.judged, progress.checking)}</p>
          </div>
        )}
      </section>

      <div className="mt-6 space-y-4">
        {cards.map((card) => (
          <SchemeCard key={card.id} card={card} currency={currency} strings={strings} />
        ))}
        {/* Placeholder card while we wait for the first result */}
        {!progress.finished && cards.length === 0 && (
          <div className="h-48 animate-pulse rounded-2xl border border-line bg-white" aria-hidden />
        )}
        {progress.finished && cards.length === 0 && <p className="text-center text-muted">{strings.noneFound}</p>}
      </div>

      {other_cards.length > 0 && (
        <details className="mt-6 rounded-2xl border border-line bg-white p-4">
          <summary className="cursor-pointer font-medium text-muted">{strings.otherSchemes(other_cards.length)}</summary>
          <div className="mt-4 space-y-4">
            {other_cards.map((card) => (
              <SchemeCard key={card.id} card={card} currency={currency} strings={strings} />
            ))}
          </div>
        </details>
      )}

      <button
        onClick={onStartOver}
        className="mt-8 w-full rounded-xl border border-brand py-3 font-semibold text-brand-ink hover:bg-brand-soft"
      >
        {strings.startOver}
      </button>
    </div>
  )
}
