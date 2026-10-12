// Small typed client for the Haq API — like an Angular service wrapping HttpClient.
import type { Country, Language, Profile, ProfileReply, ProfileTurn, StreamEvent } from './types'

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new Error(`${path} failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function sendProfileTurn(turn: ProfileTurn): Promise<ProfileReply> {
  return post<ProfileReply>('/api/profile', turn)
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
  const response = await fetch('/api/results/stream', {
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
