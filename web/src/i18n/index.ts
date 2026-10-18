// UI text in every conversation language. The backend decides the language;
// the UI follows it so buttons and messages match the chat.
// To add a language: copy english.ts, translate it, and add it below (and to Language in types.ts).
import type { Language } from '../types'
import bengali from './bengali'
import english, { type Strings } from './english'
import hindi from './hindi'
import hinglish from './hinglish'
import marathi from './marathi'

export type { Strings }

const text: Record<Language, Strings> = { english, hinglish, hindi, marathi, bengali }

export function t(language: Language): Strings {
  return text[language] ?? english
}

export function formatMoney(amount: number, currency: 'INR' | 'GBP'): string {
  return new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-GB', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}
