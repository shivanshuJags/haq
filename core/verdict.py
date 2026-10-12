"""US-301 step 3 + US-302: Nemotron Ultra makes the final call on each shortlisted scheme.

The rules engine already removed clear "no"s. Ultra now reads the full official text,
the person's profile and the rules engine's checks, and decides — explaining every
criterion in plain words, so the person can see WHY (US-302).

Each scheme is judged in its own call (in parallel), so one slow or failed answer
never blocks the rest.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator, Literal

from pydantic import BaseModel, Field

from core.candidates import Candidate
from core.llm import chat_json
from core.profile import Country, Profile
from core.profile_agent import LANGUAGE_INSTRUCTIONS, Language

MODEL = "ultra"
WORKERS = 20  # judge the whole shortlist at once: each call mostly waits on the network
MAX_SECTION_CHARS = 3000

VerdictType = Literal["eligible", "likely_eligible", "need_more_info", "not_eligible"]
Fit = Literal["strong", "possible", "weak"]


class Reason(BaseModel):
    criterion: str = Field(description="1–3 words naming the requirement, e.g. 'Income', 'Age', 'Category'")
    status: Literal["met", "not_met", "unknown"]
    explanation: str = Field(description="One short sentence, addressed to the person")


class Verdict(BaseModel):
    verdict: VerdictType
    fit: Fit = Field(description="How realistic a match this is for this person")
    reasons: list[Reason] = Field(description="The 2–5 most important requirements, checked one by one")
    benefit: str = Field(description="One line: what they would get, with the amount if the text states it")
    yearly_amount: int | None = Field(description="Estimated value per year in local currency, only if the text gives a clear number; else null")
    to_confirm: list[str] = Field(description="Things the person should check or provide; empty if none")


SYSTEM_PROMPT = """You are Haq's eligibility checker. Decide whether ONE person qualifies for ONE government scheme,
using ONLY the official text given. Then explain it to the person.

Verdicts:
- "eligible": every stated requirement is clearly met by what we know.
- "likely_eligible": the main requirements are met; only minor or routine things are unconfirmed (documents, residence proof).
- "need_more_info": an important requirement can't be judged from what we know.
- "not_eligible": the person clearly fails a requirement (e.g. wrong age, wrong gender, scheme is for a different group,
  or the scheme is for organisations/institutions rather than individuals), OR the page is not a benefit at all
  (e.g. a calculator or a general information page).

fit (how realistic this match is):
- "strong": the scheme is clearly aimed at someone like this person.
- "possible": they may well qualify, pending a few checks.
- "weak": only fits if something unusual and unmentioned is true (e.g. scheme is for a religious minority,
  for children of construction workers, for PhD researchers, for people in a specific institution) — nothing in the
  profile suggests it.

Rules:
- Never assume facts about the person that aren't in their profile. Missing fact -> "unknown", not "not_met".
- The "Code checks" were computed exactly; trust "pass" results.
- reasons: 2–5 items, the requirements that matter most. criterion = 1–3 words (e.g. "Income", "Age", "Category").
  explanation = one short sentence to the person.
- benefit: what they get, with the amount if the text states it. yearly_amount: money paid TO the person per year in
  {currency} (cash, stipend, pension, allowance, scholarship), only when the text gives a clear figure — convert monthly
  to yearly and use the person's details (e.g. number of children). Null for insurance cover, loans, subsidies on
  purchases, one-off grants, or when unclear. Never guess an amount.
- Write criterion, explanation, benefit and to_confirm in {language}.
"""


def describe_profile(profile: Profile) -> str:
    facts = profile.model_dump(exclude_none=True, exclude_defaults=True)
    return "\n".join(f"- {name}: {value}" for name, value in facts.items()) or "- (nothing known)"


def judge(candidate: Candidate, profile: Profile, country: Country, language: Language) -> Verdict | None:
    scheme = candidate.scheme
    sections = scheme.sections
    checks = "\n".join(f"- {c.criterion}: {c.status} ({c.detail})" for c in candidate.assessment.checks) or "- none"
    other = "\n".join(f"- {c}" for c in scheme.rules.other_conditions) or "- none"
    user_message = f"""PERSON
{describe_profile(profile)}

SCHEME: {scheme.name}
Summary: {scheme.summary or ''}

Eligibility (official text):
{(sections.get('eligibility') or sections.get('overview') or '')[:MAX_SECTION_CHARS]}

Benefits (official text):
{(sections.get('benefits') or '')[:MAX_SECTION_CHARS]}

Other conditions extracted earlier:
{other}

Code checks:
{checks}"""

    currency = "INR" if country == "IN" else "GBP"
    try:
        raw = chat_json(MODEL, [
            {"role": "system", "content": SYSTEM_PROMPT.format(currency=currency, language=LANGUAGE_INSTRUCTIONS[language])},
            {"role": "user", "content": user_message},
        ], schema=Verdict, max_tokens=4000)
        return Verdict.model_validate(raw)
    except Exception:
        return None  # one failed scheme shouldn't break the whole result page


def judge_as_completed(candidates: list[Candidate], profile: Profile, country: Country,
                       language: Language) -> Iterator[tuple[Candidate, Verdict | None]]:
    """Judge all candidates in parallel and yield each result the moment it's ready
    (fastest first) — so the UI can show cards while the slow ones are still running."""
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(judge, c, profile, country, language): c for c in candidates}
        for future in as_completed(futures):
            yield futures[future], future.result()
