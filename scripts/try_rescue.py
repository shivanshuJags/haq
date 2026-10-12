"""Try Rejection Rescue on fictional sample letters (calls Nemotron Ultra).

Run from the project root:
    python -m scripts.try_rescue                 # both text samples
    python -m scripts.try_rescue path/to/photo.png IN   # a photo of a letter
"""
import base64
import mimetypes
import sys
import time

from core.rescue import rescue

# Fictional letters, written for testing. Names and numbers are made up.
SAMPLES = {
    "IN": """Government of Bihar
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

District Welfare Officer, Patna""",
    "UK": """Department for Work and Pensions
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

If you disagree, you must ask for a mandatory reconsideration within one month of the date of this letter.""",
}


def show(country: str, language: str, letter_text: str | None = None, image: str | None = None) -> None:
    start = time.perf_counter()
    outcome = rescue(country, language, letter_text=letter_text, image_data_url=image)
    result = outcome.rescue
    print(f"\n=== {country} ({time.perf_counter() - start:.1f}s) scheme: {result.scheme_id} / {result.scheme_name}")
    print(f"SUMMARY: {result.summary}")
    for reason in result.reasons:
        print(f"  ✗ {reason.reason}\n      means: {reason.meaning}\n      fixable: {reason.fixable} — {reason.how_to_fix}")
    print(f"LOOKS CORRECT: {result.rejection_looks_correct} — {result.assessment}")
    print(f"RECOMMENDATION: {result.recommendation} — {result.recommendation_reason}")
    print(f"DEADLINE: {result.deadline}")
    print(f"DOCUMENTS: {result.documents_to_gather}")
    print(f"--- APPEAL LETTER ---\n{result.appeal_letter}\n---")
    if outcome.removed_ids:
        print(f"Removed IDs: {outcome.removed_ids}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path, country = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "IN")
        mime = mimetypes.guess_type(path)[0] or "image/png"
        data_url = f"data:{mime};base64,{base64.b64encode(open(path, 'rb').read()).decode()}"
        show(country, "hinglish" if country == "IN" else "english", image=data_url)
    else:
        show("IN", "hinglish", letter_text=SAMPLES["IN"])
        show("UK", "english", letter_text=SAMPLES["UK"])
