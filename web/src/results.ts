// Builds the results page step by step from stream events.
// A pure function: (old results, event) -> new results. No fetch, no React — easy to reason about.
import type { ResultCard, Results, StreamEvent } from './types'

const VERDICT_ORDER = { eligible: 0, likely_eligible: 1, need_more_info: 2 }
const COUNTED_FOR_TOTAL = new Set(['eligible', 'likely_eligible'])

export function emptyResults(currency: 'INR' | 'GBP'): Results {
  return { cards: [], other_cards: [], total_yearly: 0, potential_yearly: 0, currency, stats: {} }
}

// Same order as the backend: best verdict first, then most relevant
function byVerdictThenRelevance(a: ResultCard, b: ResultCard): number {
  return VERDICT_ORDER[a.verdict] - VERDICT_ORDER[b.verdict] || b.relevance - a.relevance
}

export function addCard(results: Results, card: ResultCard): Results {
  const weak = card.fit === 'weak'
  const cards = weak ? results.cards : [...results.cards, card].sort(byVerdictThenRelevance)
  const other_cards = weak ? [...results.other_cards, card].sort(byVerdictThenRelevance) : results.other_cards
  // Running totals while streaming; the server's final numbers replace them on "done"
  const total_yearly = cards
    .filter((c) => COUNTED_FOR_TOTAL.has(c.verdict))
    .reduce((sum, c) => sum + (c.yearly_amount ?? 0), 0)
  const potential_yearly = cards.reduce((sum, c) => sum + (c.yearly_amount ?? 0), 0)
  return { ...results, cards, other_cards, total_yearly, potential_yearly }
}

export function applyEvent(results: Results, event: StreamEvent): Results {
  switch (event.type) {
    case 'card':
      return addCard(results, event.card)
    case 'done':
      return {
        ...results,
        total_yearly: event.total_yearly,
        potential_yearly: event.potential_yearly,
        stats: event.stats,
      }
    default:
      return results
  }
}
