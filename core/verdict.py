"""US-301 step 3 + US-302: Nemotron Ultra makes the final call on each shortlisted scheme.

The rules engine already removed clear "no"s. Ultra now reads the full official text,
the person's profile and the rules engine's checks, and decides — explaining every
criterion in plain words, so the person can see WHY (US-302).

Each scheme is judged in its own call (in parallel), so one slow or failed answer
never blocks the rest.
"""
import json
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
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
    next_step: str | None = Field(
        description="If not clearly eligible yet: the ONE most useful concrete action that could make them eligible "
                    "(e.g. 'Get an income certificate from your tehsildar'). Null if eligible or if no action can help.")


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
- "weak": only fits if something unusual and unmentioned is true — nothing in the profile suggests it. E.g. the
  scheme is for a religious minority, children of construction workers, PhD researchers, a specific institution,
  or depends on a life event the person hasn't mentioned: pregnancy or a new baby, a bereavement, being a guardian
  of someone else's child, a terminal illness.

Rules:
- Where they live is CONFIRMED (they chose it in the app — see "Lives in"). Treat a residence requirement for that
  country/state as met. Only the finer points stay unknown (e.g. "England only", years of residence, immigration status).
- Never assume facts about the person that aren't in their profile. Missing fact -> "unknown", not "not_met".
- The "Code checks" were computed exactly; trust "pass" results.
- reasons: 2–5 items, the requirements that matter most. criterion = 1–3 words (e.g. "Income", "Age", "Category").
  explanation = one short sentence to the person.
- benefit: what they get, with the amount if the text states it. yearly_amount: money paid TO the person per year in
  {currency} (cash, stipend, pension, allowance, scholarship), only when the text gives a clear figure — convert monthly
  to yearly and use the person's details (e.g. number of children). Null for insurance cover, loans, subsidies on
  purchases, one-off grants, or when unclear. Never guess an amount.
- next_step (US-305, "almost eligible"): for "likely_eligible" or "need_more_info" with a strong or possible fit, the single
  most useful thing the person can DO to become eligible or prove it — specific and practical (which certificate, from
  which office; which form). Null for "eligible", "not_eligible", or when nothing they can do would help.
- Write criterion, explanation, benefit, to_confirm and next_step in {language}.
"""


COUNTRY_NAMES = {"UK": "the United Kingdom", "IN": "India"}


def describe_profile(profile: Profile, country: Country) -> str:
    where = COUNTRY_NAMES[country] + (f", {profile.region}" if profile.region else "")
    facts = profile.model_dump(exclude_none=True, exclude_defaults=True)
    facts.pop("region", None)
    lines = [f"- Lives in: {where} (confirmed — chosen in the app)"]
    lines += [f"- {name}: {value}" for name, value in facts.items()]
    return "\n".join(lines)


# Same person + same scheme + same language -> the same answer, instantly.
# Keeps results stable when someone runs the same search again (and makes it free and fast).
# In memory only: it holds profiles of the anonymous facts people typed, never IDs (those are
# redacted earlier), and is lost on restart. Bounded so it can't grow forever.
CACHE_SIZE = 5000
_cache: OrderedDict[str, Verdict] = OrderedDict()
_cache_lock = Lock()


def _cache_key(candidate: Candidate, profile: Profile, country: Country, language: Language) -> str:
    return json.dumps([candidate.scheme.id, profile.model_dump(exclude_none=True), country, language], sort_keys=True)


def judge(candidate: Candidate, profile: Profile, country: Country, language: Language) -> Verdict | None:
    key = _cache_key(candidate, profile, country, language)
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    verdict = _judge(candidate, profile, country, language)
    if verdict is not None:  # never cache failures — let the next request retry
        with _cache_lock:
            _cache[key] = verdict
            if len(_cache) > CACHE_SIZE:
                _cache.popitem(last=False)  # drop the least recently used
    return verdict


def _judge(candidate: Candidate, profile: Profile, country: Country, language: Language) -> Verdict | None:
    scheme = candidate.scheme
    sections = scheme.sections
    checks = "\n".join(f"- {c.criterion}: {c.status} ({c.detail})" for c in candidate.assessment.checks) or "- none"
    other = "\n".join(f"- {c}" for c in scheme.rules.other_conditions) or "- none"
    user_message = f"""PERSON
{describe_profile(profile, country)}

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
