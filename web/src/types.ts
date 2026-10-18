// TypeScript mirrors of the backend's Pydantic models (core/profile.py, api/routes/*.py, core/results.py).
// If the backend changes a field, change it here too.

export type Country = 'UK' | 'IN'
export type Language = 'hinglish' | 'english'

export interface Profile {
  region?: string | null
  age?: number | null
  gender?: 'male' | 'female' | 'transgender' | null
  caste_category?: string | null
  marital_status?: string | null
  residence?: 'rural' | 'urban' | null
  annual_family_income?: number | null
  personal_annual_income?: number | null
  savings?: number | null
  has_bpl_card?: boolean | null
  land_acres?: number | null
  occupation?: string | null
  is_student?: boolean | null
  education_level?: string | null
  has_disability?: boolean | null
  disability_percent?: number | null
  has_children?: boolean | null
  children_count?: number | null
  is_pregnant?: boolean | null
  is_carer?: boolean | null
  receives_benefits?: string[]
  needs?: string | null
}

export interface FollowUp {
  question: string
  options: string[]
}

export interface ProfileTurn {
  country: Country
  message: string
  profile: Profile
  asked: string[]
  answering: string[]
  rounds: number
  language: Language | null
}

export interface ProfileReply {
  profile: Profile
  follow_up: FollowUp | null
  asking: string[]
  ready: boolean
  language: Language
  privacy_note: string | null
}

export type Verdict = 'eligible' | 'likely_eligible' | 'need_more_info'

export interface Reason {
  criterion: string
  status: 'met' | 'not_met' | 'unknown'
  explanation: string
}

export interface ResultCard {
  id: string
  name: string
  summary: string | null
  is_state_scheme: boolean
  relevance: number
  verdict: Verdict
  fit: 'strong' | 'possible' | 'weak'
  reasons: Reason[]
  benefit: string
  yearly_amount: number | null
  to_confirm: string[]
  next_step: string | null
  documents: string[]
  how_to_apply: string
  apply_url: string | null
  source_url: string
  source: string | null
  needs_verification: boolean
}

export interface Results {
  cards: ResultCard[]
  other_cards: ResultCard[]
  total_yearly: number
  potential_yearly: number
  currency: 'INR' | 'GBP'
  stats: Record<string, number>
}

// Events from POST /api/results/stream (one JSON object per line)
export type StreamEvent =
  | { type: 'start'; checking: number; currency: 'INR' | 'GBP'; stats: Record<string, number> }
  | { type: 'card'; card: ResultCard }
  | { type: 'progress'; judged: number }
  | { type: 'done'; total_yearly: number; potential_yearly: number; currency: 'INR' | 'GBP'; stats: Record<string, number> }
  | { type: 'error' }

// POST /api/rescue (core/rescue.py)
export interface RejectionReason {
  reason: string
  meaning: string
  fixable: boolean
  how_to_fix: string
}

export interface Rescue {
  scheme_id: string | null
  scheme_name: string | null
  summary: string
  reasons: RejectionReason[]
  rejection_looks_correct: 'yes' | 'no' | 'unclear'
  assessment: string
  recommendation: 'reapply' | 'appeal' | 'reapply_or_appeal' | 'not_eligible'
  recommendation_reason: string
  deadline: string | null
  documents_to_gather: string[]
  appeal_letter: string
}

export interface RescueOutcome {
  letter_text: string
  removed_ids: string[]
  rescue: Rescue
  scheme_source_url: string | null
  scheme_apply_url: string | null
}

export interface Progress {
  checking: number
  judged: number
  finished: boolean
}
