// US-303: one combined, de-duplicated document checklist across the schemes someone qualifies for.
// Official lists name the same paper many ways ("Aadhar card", "Proof of identity (Aadhaar Card)"),
// so common documents are recognised by keyword and given one name.
import type { ResultCard } from './types'

const KNOWN_DOCUMENTS: [RegExp, string][] = [
  [/aadha?a?r/i, 'Aadhaar card'],
  [/income (cert|proof)|cert\w*\b.{0,40}\bincome|aay praman|salary slip/i, 'Income certificate'],
  [/caste|jati praman|community cert/i, 'Caste certificate'],
  [/domicile|residen(ce|tial) (cert|proof)|niwas|address proof|proof of (address|residence)/i, 'Domicile / residence proof'],
  [/bank|passbook|cancelled cheque/i, 'Bank account details (passbook)'],
  [/photo/i, 'Passport-size photographs'],
  [/mark ?sheet|marks? (card|cert)|qualification cert|educational cert/i, 'Marksheets / educational certificates'],
  [/bonafide|admission|enrol|fee receipt/i, 'Admission / bonafide certificate'],
  [/ration card|bpl|antyodaya/i, 'Ration card / BPL card'],
  [/\bpan\b/i, 'PAN card'],
  [/disab/i, 'Disability certificate'],
  [/land|khatauni|khasra|khatoni/i, 'Land records (khatauni)'],
  [/birth cert|date of birth|age proof/i, 'Age proof (birth certificate)'],
  [/national insurance/i, 'National Insurance number'],
  [/mobile|phone number/i, 'Mobile number'],
]

export interface ChecklistItem {
  document: string
  schemes: string[] // which schemes need it
}

// Lines in official lists that aren't actual documents
const NOT_A_DOCUMENT =
  /^(\**\s*note\b|any other|other (necessary |relevant |required )?documents?|as required|documents? as (required|applicable))/i

function canonical(document: string): string {
  if (NOT_A_DOCUMENT.test(document.trim())) return ''
  const match = KNOWN_DOCUMENTS.find(([pattern]) => pattern.test(document))
  if (match) return match[1]
  // Unknown documents: tidy whitespace and markdown links, keep the official wording
  return document.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\s+/g, ' ').trim()
}

export function combinedChecklist(cards: ResultCard[]): ChecklistItem[] {
  const byDocument = new Map<string, Set<string>>()
  for (const card of cards) {
    for (const document of card.documents) {
      const name = canonical(document)
      if (!name || name.length > 140) continue // skip long paragraphs that aren't really list items
      if (!byDocument.has(name)) byDocument.set(name, new Set())
      byDocument.get(name)!.add(card.name)
    }
  }
  // Documents needed by the most schemes first — those are the ones worth getting today
  return [...byDocument.entries()]
    .map(([document, schemes]) => ({ document, schemes: [...schemes] }))
    .sort((a, b) => b.schemes.length - a.schemes.length || a.document.localeCompare(b.document))
}

// `done` = documents the person already ticked off; they keep their tick in the copy
export function checklistAsText(items: ChecklistItem[], title: string, done: Set<string> = new Set()): string {
  const line = (item: ChecklistItem) => `${done.has(item.document) ? '☑' : '☐'} ${item.document}  (${item.schemes.length})`
  return [title, '', ...items.map(line)].join('\n')
}
