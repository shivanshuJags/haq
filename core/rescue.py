"""US-501 / US-502: Rejection Rescue.

Someone's application was rejected. They paste the letter (or upload a photo of it).
We explain why in plain words, check the reasons against the scheme's official rules,
tell them what to fix, and draft an appeal letter.

    photo -> (vision model) -> letter text -> remove ID numbers -> find the scheme (vector search)
          -> Nemotron Ultra: reasons, fixes, should you appeal?, appeal letter
"""
import base64
import re
from typing import Literal

from pydantic import BaseModel, Field

from core.catalog import catalog
from core.llm import chat, chat_json
from core.privacy import redact
from core.profile import Country
from core.profile_agent import LANGUAGE_INSTRUCTIONS, Language
from core.search import search

MAX_LETTER_CHARS = 6000
CANDIDATE_SCHEMES = 5

DATA_URL = re.compile(r"^data:(image/(?:png|jpe?g|webp));base64,(.+)$", re.DOTALL)


class RejectionReason(BaseModel):
    reason: str = Field(description="The reason as the letter states it, shortened")
    meaning: str = Field(description="What it means, in simple words, to the person")
    fixable: bool = Field(description="Can the person fix this (e.g. a missing document) — or is it a real ineligibility?")
    how_to_fix: str = Field(description="Exactly what to do; empty if not fixable")


class Rescue(BaseModel):
    scheme_id: str | None = Field(description="id of the matching scheme from the list given, or null if none matches")
    scheme_name: str | None = Field(description="The scheme's name as written in the letter, if any")
    summary: str = Field(description="2 short sentences: what happened and the main way forward")
    reasons: list[RejectionReason]
    rejection_looks_correct: Literal["yes", "no", "unclear"] = Field(
        description="Compared with the official rules, does the rejection look right?")
    assessment: str = Field(description="1–2 sentences explaining that judgement against the official rules")
    recommendation: Literal["reapply", "appeal", "reapply_or_appeal", "not_eligible"]
    recommendation_reason: str
    deadline: str | None = Field(description="Any deadline the letter states (e.g. 'within 30 days of the letter'), else null")
    documents_to_gather: list[str]
    appeal_letter: str = Field(description="A complete, polite, formal letter. Use [placeholders] for unknown personal details")


class RescueOutcome(BaseModel):
    letter_text: str
    removed_ids: list[str]
    rescue: Rescue
    scheme_source_url: str | None = None
    scheme_apply_url: str | None = None


TRANSCRIBE_PROMPT = (
    "Transcribe all the text in this letter exactly, line by line, in its original language. "
    "Output only the letter's text, nothing else."
)

SYSTEM_PROMPT = """You are Haq's Rejection Rescue. A person's application for a government benefit or scheme was rejected.
Country: {country}

You get: the rejection letter, and a few candidate schemes from our database with their OFFICIAL eligibility text.

Do this:
1. scheme_id: pick the candidate the letter is about, or null if none clearly matches. If several candidates fit
   (e.g. "Post-Matric Scholarship" exists for SC, OBC and minorities) and the letter doesn't say which, use null —
   don't guess, and don't assume the person's category in anything you write.
2. reasons: every rejection reason in the letter. Explain each simply. Decide if it's fixable
   (missing/expired/wrong document, form error, late submission -> usually fixable) or a real ineligibility.
3. rejection_looks_correct + assessment: compare the reasons with the official rules. Say "no" only if the rules
   clearly don't support the rejection; "unclear" if you can't tell. Never invent rules.
4. recommendation: "reapply" (fix and apply again), "appeal" (the decision looks wrong), "reapply_or_appeal",
   or "not_eligible" (a real ineligibility — say so kindly and suggest checking other schemes).
5. deadline: copy any deadline the letter states. documents_to_gather: concrete documents to collect.
6. appeal_letter: a complete formal letter addressed to the office that sent the rejection, in {letter_language},
   referencing the rejection and each reason, explaining the correction or why the decision is wrong, listing
   enclosures, and asking for reconsideration. Use [placeholders] like [Your full name], [Application number],
   [Address], [Date] for details not in the letter. Do not invent facts about the person.

Write summary, meaning, how_to_fix, assessment, recommendation_reason and documents_to_gather in {language}.
The appeal letter itself must be in {letter_language}.
"""


def transcribe(image_data_url: str) -> str:
    """Read the text off a photo of a letter."""
    match = DATA_URL.match(image_data_url.strip())
    if not match:
        raise ValueError("Image must be a PNG, JPEG or WebP data URL")
    base64.b64decode(match.group(2), validate=True)  # reject corrupt uploads early
    return chat("vision", [{"role": "user", "content": [
        {"type": "text", "text": TRANSCRIBE_PROMPT},
        {"type": "image_url", "image_url": {"url": image_data_url}},
    ]}], max_tokens=2000, temperature=0)


def candidate_schemes(letter: str, country: Country) -> list[dict]:
    """Schemes whose meaning is closest to the letter — usually the scheme it's about is #1."""
    schemes = catalog()
    found = search(letter[:2000], country, region=None, limit=CANDIDATE_SCHEMES)
    # search() filters region-specific schemes out when region is None; also try every region
    if country == "IN":
        for region in ("Bihar", "Uttar Pradesh"):
            found += search(letter[:2000], country, region=region, limit=2)
    seen, result = set(), []
    for row in sorted(found, key=lambda r: r["similarity"], reverse=True):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        scheme = schemes[row["id"]]
        eligibility = scheme.sections.get("eligibility") or scheme.sections.get("overview") or ""
        result.append({"id": scheme.id, "name": scheme.name, "eligibility": eligibility[:1500]})
    return result[:CANDIDATE_SCHEMES + 2]


def rescue(country: Country, language: Language, letter_text: str | None = None,
           image_data_url: str | None = None) -> RescueOutcome:
    if image_data_url:
        letter_text = transcribe(image_data_url)
    if not letter_text or not letter_text.strip():
        raise ValueError("No letter text")

    letter, removed = redact(letter_text[:MAX_LETTER_CHARS])
    candidates = candidate_schemes(letter, country)
    candidates_text = "\n\n".join(
        f"[{c['id']}] {c['name']}\nOfficial eligibility:\n{c['eligibility']}" for c in candidates
    )

    letter_language = "English" if country == "UK" else "formal English (the usual language for such letters in India)"
    raw = chat_json("ultra", [
        {"role": "system", "content": SYSTEM_PROMPT.format(
            country=country, language=LANGUAGE_INSTRUCTIONS[language], letter_language=letter_language)},
        {"role": "user", "content": f"REJECTION LETTER:\n{letter}\n\nCANDIDATE SCHEMES:\n{candidates_text}"},
    ], schema=Rescue, max_tokens=8000)
    result = Rescue.model_validate(raw)

    # Only trust a scheme id that we actually offered
    scheme = catalog().get(result.scheme_id) if result.scheme_id in {c["id"] for c in candidates} else None
    if scheme is None:
        result.scheme_id = None
    return RescueOutcome(
        letter_text=letter,
        removed_ids=removed,
        rescue=result,
        scheme_source_url=scheme.source_url if scheme else None,
        scheme_apply_url=scheme.apply_url if scheme else None,
    )
