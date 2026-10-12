import { useState } from 'react'
import type { Country } from '../types'

const INDIA_STATES = ['Uttar Pradesh', 'Bihar']

interface Props {
  onStart: (country: Country, region: string | null) => void
  onRescue: () => void
}

export function Welcome({ onStart, onRescue }: Props) {
  // Which country button was tapped. India needs one more step (state).
  const [country, setCountry] = useState<Country | null>(null)

  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col justify-center px-6 py-10">
      <h1 className="text-5xl font-bold tracking-tight text-brand">Haq</h1>
      <p className="mt-1 text-sm font-medium text-accent">हक़ · what's yours</p>
      <p className="mt-6 text-lg leading-relaxed text-ink">
        Find the government benefits you're entitled to — and exactly how to claim them.
      </p>
      <p className="mt-2 text-muted">
        Jaaniye aap kin sarkari yojanaon ke haqdaar hain.
      </p>

      <h2 className="mt-10 text-sm font-semibold uppercase tracking-wide text-muted">
        Where do you live? · Aap kahan rehte hain?
      </h2>
      <div className="mt-3 grid grid-cols-2 gap-3">
        {/* Currency symbols instead of flag emoji: Windows doesn't render flag emoji */}
        <CountryButton label="India" symbol="₹" selected={country === 'IN'} onClick={() => setCountry('IN')} />
        <CountryButton label="United Kingdom" symbol="£" selected={false} onClick={() => onStart('UK', null)} />
      </div>

      {country === 'IN' && (
        <>
          <h2 className="mt-8 text-sm font-semibold uppercase tracking-wide text-muted">
            Which state? · Kaunsa rajya?
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {INDIA_STATES.map((state) => (
              <button
                key={state}
                onClick={() => onStart('IN', state)}
                className="rounded-full border border-brand bg-white px-5 py-2.5 font-medium text-brand-ink transition hover:bg-brand hover:text-white"
              >
                {state}
              </button>
            ))}
            <button
              onClick={() => onStart('IN', null)}
              className="rounded-full border border-line bg-white px-5 py-2.5 text-muted transition hover:border-brand"
            >
              Other state · Koi aur
            </button>
          </div>
          <p className="mt-3 text-xs text-muted">
            Other states: you'll see national (central) schemes only.
          </p>
        </>
      )}

      {/* US-501: second way in — for people who already applied and were rejected */}
      <button
        onClick={onRescue}
        className="mt-10 flex items-center gap-4 rounded-2xl border border-line bg-white p-4 text-left transition hover:border-brand"
      >
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-accent-soft text-2xl" aria-hidden>
          📄
        </span>
        <span>
          <span className="block font-semibold">Got a rejection letter? · Rejection letter mila?</span>
          <span className="block text-sm text-muted">Rejection Rescue: understand why, and appeal →</span>
        </span>
      </button>
    </div>
  )
}

function CountryButton(props: { label: string; symbol: string; selected: boolean; onClick: () => void }) {
  return (
    <button
      onClick={props.onClick}
      className={`flex flex-col items-center gap-2 rounded-2xl border-2 bg-white px-4 py-6 transition hover:border-brand ${
        props.selected ? 'border-brand shadow-md' : 'border-line'
      }`}
    >
      <span
        className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-soft text-3xl font-bold text-brand"
        aria-hidden
      >
        {props.symbol}
      </span>
      <span className="font-semibold">{props.label}</span>
    </button>
  )
}
