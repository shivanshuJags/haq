import { useEffect, useState } from 'react'
import type { Strings } from '../i18n'

// Ultra takes ~10–15 seconds. Show what's happening, one step at a time, so the wait feels purposeful.
export function Loading({ strings }: { strings: Strings }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((current) => Math.min(current + 1, strings.loadingSteps.length - 1))
    }, 3500)
    return () => clearInterval(timer) // cleanup when the component disappears (like ngOnDestroy)
  }, [strings])

  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col justify-center px-6 py-10">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-brand-soft border-t-brand" />
      <ol className="mt-8 space-y-3">
        {strings.loadingSteps.map((text, index) => (
          <li
            key={text}
            className={`flex items-start gap-3 transition-opacity duration-500 ${
              index <= step ? 'opacity-100' : 'opacity-25'
            }`}
          >
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${index < step ? 'bg-brand' : index === step ? 'animate-pulse bg-accent' : 'bg-line'}`} />
            <span className={index === step ? 'font-medium' : 'text-muted'}>{text}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}
