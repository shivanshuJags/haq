import Markdown from 'react-markdown'
import { formatMoney, type Strings } from '../i18n'
import type { ResultCard } from '../types'

const VERDICT_STYLE = {
  eligible: 'bg-brand text-white',
  likely_eligible: 'bg-brand-soft text-brand-ink',
  need_more_info: 'bg-accent-soft text-ink',
}

const STATUS_ICON = {
  met: { icon: '✓', style: 'bg-brand-soft text-brand-ink' },
  not_met: { icon: '✗', style: 'bg-red-100 text-red-700' },
  unknown: { icon: '?', style: 'bg-accent-soft text-ink' },
}

// Links inside official text open in a new tab, so the user doesn't lose their results
function ExternalLink(props: React.ComponentProps<'a'>) {
  return <a {...props} target="_blank" rel="noreferrer" className="text-brand underline" />
}

interface Props {
  card: ResultCard
  currency: 'INR' | 'GBP'
  strings: Strings
}

export function SchemeCard({ card, currency, strings }: Props) {
  return (
    // [overflow-wrap:anywhere] lets long URLs in official text wrap instead of stretching the card off-screen
    <article className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm [overflow-wrap:anywhere]">
      <div className="p-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${VERDICT_STYLE[card.verdict]}`}>
            {strings.verdict[card.verdict]}
          </span>
          {card.is_state_scheme && (
            <span className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted">{strings.stateScheme}</span>
          )}
        </div>

        <h3 className="mt-3 text-lg font-semibold leading-snug">{card.name}</h3>

        {card.yearly_amount ? (
          <p className="mt-2 text-2xl font-bold text-brand">
            {formatMoney(card.yearly_amount, currency)}
            <span className="ml-1 text-sm font-normal text-muted">/ {strings.perYear}</span>
          </p>
        ) : null}
        <p className="mt-2 leading-relaxed text-ink">{card.benefit}</p>

        {/* US-302: why — every important requirement with ✓ / ✗ / ? */}
        <h4 className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted">{strings.whyThisMatches}</h4>
        <ul className="mt-2 space-y-2">
          {card.reasons.map((reason) => (
            <li key={reason.criterion + reason.explanation} className="flex gap-2.5 text-sm">
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${STATUS_ICON[reason.status].style}`}
                aria-label={reason.status}
              >
                {STATUS_ICON[reason.status].icon}
              </span>
              <span>
                <span className="font-medium">{reason.criterion}:</span> {reason.explanation}
              </span>
            </li>
          ))}
        </ul>

        {/* US-305: the one action that could make them eligible */}
        {card.next_step && (
          <div className="mt-4 flex gap-3 rounded-xl border border-accent bg-accent-soft p-3 text-sm">
            <span aria-hidden>🔓</span>
            <p>
              <span className="font-semibold">{strings.nextStep}:</span> {card.next_step}
            </p>
          </div>
        )}

        {card.to_confirm.length > 0 && (
          <div className="mt-4 rounded-xl bg-accent-soft/60 p-3 text-sm">
            <p className="font-semibold">{strings.toConfirm}</p>
            <ul className="mt-1 list-disc space-y-0.5 pl-5">
              {card.to_confirm.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* US-303 / US-304: details folded away so the list stays scannable */}
      {card.documents.length > 0 && (
        <details className="border-t border-line px-5 py-3">
          <summary className="cursor-pointer font-medium text-brand-ink">
            📄 {strings.documents} ({card.documents.length})
          </summary>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {card.documents.map((document) => (
              <li key={document}>
                {/* Some documents contain markdown links, e.g. "[prescribed format](https://...)" */}
                <Markdown components={{ p: 'span', a: ExternalLink }}>{document}</Markdown>
              </li>
            ))}
          </ul>
        </details>
      )}
      {card.how_to_apply && (
        <details className="border-t border-line px-5 py-3">
          <summary className="cursor-pointer font-medium text-brand-ink">📝 {strings.howToApply}</summary>
          <div className="markdown mt-2 text-sm leading-relaxed">
            <Markdown components={{ a: ExternalLink }}>{card.how_to_apply}</Markdown>
          </div>
        </details>
      )}

      <div className="flex flex-wrap items-center gap-3 border-t border-line bg-paper px-5 py-3">
        {card.apply_url && (
          <a
            href={card.apply_url}
            target="_blank"
            rel="noreferrer"
            className="rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-ink"
          >
            {strings.applyNow} ↗
          </a>
        )}
        <a href={card.source_url} target="_blank" rel="noreferrer" className="text-sm text-brand underline-offset-2 hover:underline">
          {strings.officialSource} ↗
        </a>
        {card.needs_verification && <p className="w-full text-xs text-muted">⚠️ {strings.verify}</p>}
      </div>
    </article>
  )
}
