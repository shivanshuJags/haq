import type { Strings } from '../i18n'

// US-601: guidance-only disclaimer + data attribution (required by the data licences), on every screen
export function Footer({ strings }: { strings: Strings }) {
  return (
    <footer className="border-t border-line bg-white px-4 py-3 text-center text-[11px] leading-relaxed text-muted">
      <p>{strings.disclaimer}</p>
      <p>{strings.attribution}</p>
      <p className="mt-1 font-medium text-brand-ink">{strings.poweredBy}</p>
    </footer>
  )
}
