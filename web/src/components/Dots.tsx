/** Three softly pulsing dots — a light "loading" sign. The animation lives in index.css (.loading-dot). */
export function Dots({ label }: { label: string }) {
  return (
    <div role="status" aria-label={label} className="flex items-center justify-center gap-1.5 py-6">
      {[0, 1, 2].map((index) => (
        <span
          key={index}
          className="loading-dot h-2.5 w-2.5 rounded-full bg-brand"
          style={{ animationDelay: `${index * 0.16}s` }}
        />
      ))}
    </div>
  )
}
