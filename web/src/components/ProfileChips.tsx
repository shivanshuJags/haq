import type { Country, Profile } from '../types'
import { formatMoney, type Strings } from '../i18n'

interface Props {
  profile: Profile
  country: Country
  strings: Strings
  onRemove: (field: keyof Profile) => void
}

// Turn each known profile field into a short human label, e.g. income -> "Family income ₹1,50,000"
function chipLabel(field: keyof Profile, value: unknown, country: Country): string | null {
  const money = (n: number) => formatMoney(n, country === 'IN' ? 'INR' : 'GBP')
  switch (field) {
    case 'region': return `📍 ${value}`
    case 'age': return `${value} yrs`
    case 'gender': return String(value)
    case 'caste_category': return String(value)
    case 'marital_status': return String(value)
    case 'residence': return String(value)
    case 'annual_family_income': return `Family income ${money(value as number)}/yr`
    case 'personal_annual_income': return `Income ${money(value as number)}/yr`
    case 'savings': return `Savings ${money(value as number)}`
    case 'has_bpl_card': return value ? 'BPL card' : 'No BPL card'
    case 'land_acres': return `Land ${value} acres`
    case 'occupation': return String(value).replace(/_/g, ' ')
    case 'is_student': return value ? null : 'Not a student' // "student" already shows as occupation
    case 'education_level': return `Education: ${value}`
    case 'has_disability': return value ? 'Disability' : 'No disability'
    case 'disability_percent': return `${value}% disability`
    case 'has_children': return value ? 'Has children' : 'No children'
    case 'children_count': return `${value} children`
    case 'is_pregnant': return value ? 'Pregnant' : null
    case 'is_carer': return value ? 'Carer' : null
    default: return null // needs, receives_benefits: not shown as chips
  }
}

export function ProfileChips({ profile, country, strings, onRemove }: Props) {
  const chips = (Object.keys(profile) as (keyof Profile)[])
    .map((field) => {
      const value = profile[field]
      if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) return null
      const label = chipLabel(field, value, country)
      return label ? { field, label } : null
    })
    .filter((chip) => chip !== null)

  if (chips.length === 0) return null

  return (
    <div className="border-b border-line bg-white px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{strings.whatWeKnow}</p>
      {/* Phones: one row you can swipe sideways, so the chat keeps its space. Larger screens: wrap. */}
      <div className="-mx-4 mt-2 flex gap-1.5 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0">

        {chips.map(({ field, label }) => (
          <span
            key={field}
            className="inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full bg-brand-soft py-1 pl-3 pr-1 text-sm capitalize text-brand-ink"
          >
            {label}
            <button
              onClick={() => onRemove(field)}
              aria-label={`${strings.remove} ${label}`}
              className="flex h-5 w-5 items-center justify-center rounded-full text-brand-ink/60 hover:bg-brand hover:text-white"
            >
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  )
}
