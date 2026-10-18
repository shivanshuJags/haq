// Countries, states and languages Haq offers — the one place to edit.
//
// To add a country: add an entry here, add its code to `Country` in types.ts, add its UI language
// file in src/i18n/, and give the backend its data pack (ingest + core/languages.py BY_COUNTRY).
import type { Country, Language } from '../types'

export interface StateOption {
  name: string // as the backend expects it, in English
  coverage: 'full' | 'central' // full = we hold this state's own schemes too
}

export interface CountryConfig {
  code: Country
  name: string
  nativeName?: string
  symbol: string // shown as the country's mark (flag emoji don't render on Windows)
  currency: 'INR' | 'GBP'
  languages: Language[] // the first is the default
  states?: StateOption[]
  stateLabel?: string
}

const INDIA_STATES_WITH_DATA = ['Bihar', 'Uttar Pradesh']

const INDIA_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana',
  'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
  'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  // Union Territories
  'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra & Nagar Haveli and Daman & Diu', 'Delhi',
  'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry',
]

export const COUNTRIES: CountryConfig[] = [
  {
    code: 'IN',
    name: 'India',
    nativeName: 'भारत',
    symbol: '₹',
    currency: 'INR',
    languages: ['hinglish', 'english', 'hindi', 'marathi', 'bengali'],
    // States with data first, then the rest alphabetically
    states: [
      ...INDIA_STATES_WITH_DATA.map((name) => ({ name, coverage: 'full' as const })),
      ...INDIA_STATES.filter((name) => !INDIA_STATES_WITH_DATA.includes(name)).map((name) => ({
        name,
        coverage: 'central' as const,
      })),
    ],
  },
  {
    code: 'UK',
    name: 'United Kingdom',
    symbol: '£',
    currency: 'GBP',
    languages: ['english'],
  },
]

export function countryConfig(code: Country): CountryConfig {
  return COUNTRIES.find((country) => country.code === code) ?? COUNTRIES[0]
}

// How each language names itself, for the language picker
export const LANGUAGE_NAMES: Record<Language, { native: string; english: string }> = {
  english: { native: 'English', english: 'English' },
  hinglish: { native: 'Hinglish', english: 'Hindi in Latin letters' },
  hindi: { native: 'हिंदी', english: 'Hindi' },
  marathi: { native: 'मराठी', english: 'Marathi' },
  bengali: { native: 'বাংলা', english: 'Bengali' },
}
