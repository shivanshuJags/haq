// Fictional rejection letters for trying Rejection Rescue (and for the demo video).
// Clearly marked as samples; names and numbers are made up.
import type { Country } from './types'

export const SAMPLE_LETTERS: Record<Country, string> = {
  IN: `[SAMPLE LETTER — FICTIONAL]
Government of Bihar
Backward Classes & Extremely Backward Classes Welfare Department
Post-Matric Scholarship 2026-27

Application No: PMS/2026/BH/000000
Date: 05/09/2026

Dear Applicant,

Your application for the Post-Matric Scholarship has been REJECTED for the following reasons:
1. Family income certificate is expired (issued more than one year ago).
2. Bonafide certificate from the institution not uploaded.

You may correct the above and re-apply on the portal, or file an appeal with the District
Welfare Officer within 30 days of this notice.

District Welfare Officer, Patna`,
  UK: `[SAMPLE LETTER — FICTIONAL]
Department for Work and Pensions
Personal Independence Payment

Date: 1 September 2026

Dear Mr Sample,

Decision on your claim for Personal Independence Payment

We have looked at your claim and decided that you are not entitled to Personal Independence Payment
from 14 July 2026.

Daily living component: you scored 4 points. You need at least 8 points.
Mobility component: you scored 0 points. You need at least 8 points.

We based this on your PIP2 questionnaire and the health professional's assessment report.
The assessor noted that you can prepare a simple meal unaided and can walk more than 200 metres.

If you disagree, you must ask for a mandatory reconsideration within one month of the date of this letter.`,
}
