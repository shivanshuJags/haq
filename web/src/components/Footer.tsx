import type { Strings } from '../i18n'

// US-601: guidance-only disclaimer + data attribution (required by the data licences).
// Full version sits at the end of each page's content; the chat screen gets a one-line version
// so the conversation keeps the space on a phone.
export function Footer({ strings, compact = false }: { strings: Strings; compact?: boolean }) {
  if (compact) {
    return (
      <footer className="border-t border-line bg-white px-4 py-1.5 text-center text-[11px] text-muted">
        {strings.disclaimerShort}
      </footer>
    )
  }
  return (
    <footer className="mt-auto border-t border-line px-4 py-4 text-center text-[11px] leading-relaxed text-muted">
      <p>{strings.disclaimer}</p>
      <p>{strings.attribution}</p>
      <p className="mt-1 font-medium text-brand-ink">{strings.poweredBy}</p>
    </footer>
  )
}
