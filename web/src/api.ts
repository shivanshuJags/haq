// Small typed client for the Haq API — like an Angular service wrapping HttpClient.
import type { Country, Highlights, Language, Profile, ProfileReply, ProfileTurn, RescueOutcome, StreamEvent } from './types'

// Where the API lives. Locally it's empty: Vite proxies /api to localhost:8000.
// In production (Vercel) set VITE_API_URL to the backend's URL, e.g. https://xxxx.nebius.cloud
const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')


async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(API_URL + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new Error(`${path} failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

/** What the welcome screen shows for a country (and Indian state): counts, categories, popular and new schemes. */
// The lists only change when the backend is redeployed, so each country/state is fetched once per visit.
// We keep the *promise*, so two quick requests for the same place share one network call
// (like shareReplay(1) on an RxJS Observable). The browser also caches it for an hour (Cache-Control).
const highlightsCache = new Map<string, Promise<Highlights>>()

export function fetchHighlights(country: Country, region: string | null): Promise<Highlights> {
  const query = new URLSearchParams({ country, ...(region ? { region } : {}) }).toString()
  let request = highlightsCache.get(query)
  if (!request) {
    request = fetch(`${API_URL}/api/highlights?${query}`).then((response) => {
      if (!response.ok) throw new Error(`/api/highlights failed with ${response.status}`)
      return response.json() as Promise<Highlights>
    })
    request.catch(() => highlightsCache.delete(query)) // a failed call may be retried later
    highlightsCache.set(query, request)
  }
  return request
}

export async function sendProfileTurn(turn: ProfileTurn): Promise<ProfileReply> {
  return post<ProfileReply>('/api/profile', turn)
}

export async function sendRescue(request: {
  country: Country
  language: Language
  letter_text?: string
  image?: string // data URL of a photo of the letter
}): Promise<RescueOutcome> {
  return post<RescueOutcome>('/api/rescue', request)
}

/**
 * Results arrive as a stream: one JSON event per line (start, card, progress, ..., done).
 * `onEvent` is called for each one as soon as it arrives — like subscribing to an RxJS Observable.
 */
export async function streamResults(
  country: Country,
  profile: Profile,
  language: Language,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(API_URL + '/api/results/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ country, profile, language }),
  })
  if (!response.ok || !response.body) {
    throw new Error(`/api/results/stream failed with ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // A network chunk can end mid-line, so only handle complete lines and keep the rest
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.trim()) continue
      const event = JSON.parse(line) as StreamEvent
      if (event.type === 'error') throw new Error('The server could not finish the results')
      onEvent(event)
    }
  }
}
