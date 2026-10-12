"""US-301/302/303/304: the full "what am I entitled to?" pipeline, producing result cards.

profile -> candidates (rules engine + vector ranking) -> Ultra verdicts -> sorted cards + total
"""
import html
import re
import time
from typing import Iterator

from pydantic import BaseModel

from core.candidates import Candidate, find_candidates
from core.profile import Country, Profile
from core.profile_agent import Language
from core.verdict import Fit, Reason, Verdict, VerdictType, judge_as_completed

VERDICT_ORDER = {"eligible": 0, "likely_eligible": 1, "need_more_info": 2}
COUNTED_FOR_TOTAL = {"eligible", "likely_eligible"}

# Strips list markers: "1. ", "* ", "- ", "> "
LIST_MARKER = re.compile(r"^\s*(?:\d+[.)]|[*\-•>])\s+")
HTML_TAG = re.compile(r"<[^>]+>")


def clean_text(text: str) -> str:
    """myScheme text sometimes contains HTML entities, even double-encoded ("&amp;amp;"), and stray tags."""
    for _ in range(3):  # unescape until stable: "&amp;amp;" -> "&amp;" -> "&"
        unescaped = html.unescape(text)
        if unescaped == text:
            break
        text = unescaped
    return HTML_TAG.sub(" ", text).strip()


class ResultCard(BaseModel):
    id: str
    name: str
    summary: str | None
    is_state_scheme: bool
    relevance: float  # used to order cards that arrive one by one
    verdict: VerdictType
    fit: Fit
    reasons: list[Reason]
    benefit: str
    yearly_amount: int | None
    to_confirm: list[str]
    documents: list[str]
    how_to_apply: str
    apply_url: str | None
    source_url: str
    source: str | None
    needs_verification: bool


class Results(BaseModel):
    cards: list[ResultCard]
    other_cards: list[ResultCard]  # weak matches — shown collapsed ("you could also check")
    total_yearly: int              # from schemes they (likely) qualify for
    potential_yearly: int          # + schemes that need a few more checks
    currency: str
    stats: dict


def documents_list(markdown: str) -> list[str]:
    """Turn a markdown list of documents into plain strings (US-303)."""
    items = []
    for line in clean_text(markdown).splitlines():
        text = LIST_MARKER.sub("", line).strip().strip("*").strip()
        if text and not text.startswith("#"):
            items.append(text.rstrip("."))
    return items


def build_card(candidate: Candidate, verdict: Verdict) -> ResultCard:
    scheme = candidate.scheme
    return ResultCard(
        id=scheme.id,
        name=scheme.name,
        summary=scheme.summary,
        is_state_scheme=candidate.is_state_scheme,
        relevance=round(candidate.score, 4),
        verdict=verdict.verdict,
        fit=verdict.fit,
        reasons=verdict.reasons,
        benefit=verdict.benefit,
        yearly_amount=verdict.yearly_amount,
        to_confirm=verdict.to_confirm,
        documents=documents_list(scheme.sections.get("documents") or ""),
        how_to_apply=clean_text(scheme.sections.get("how_to_apply") or ""),
        apply_url=scheme.apply_url,
        source_url=scheme.source_url,
        source=scheme.source,
        needs_verification=bool(scheme.meta.get("needs_verification")),
    )


def sort_key(card: ResultCard) -> tuple:
    """Best verdict first; within a verdict, most relevant first."""
    return VERDICT_ORDER[card.verdict], -card.relevance


def totals(cards: list[ResultCard]) -> tuple[int, int]:
    main = [c for c in cards if c.fit != "weak"]
    total = sum(c.yearly_amount or 0 for c in main if c.verdict in COUNTED_FOR_TOTAL)
    potential = sum(c.yearly_amount or 0 for c in main)
    return total, potential


def stream_results(profile: Profile, country: Country, language: Language) -> Iterator[dict]:
    """Yield events as soon as each piece is ready, so the UI can show cards one by one:
         {"type": "start", "checking": 20, "stats": {...}}   after the rules engine (~2s)
         {"type": "card", "card": {...}}                     when Ultra finds a scheme that may apply
         {"type": "progress", "judged": 7}                   after every scheme Ultra finishes
         {"type": "done", "total_yearly": ..., ...}          at the end
    """
    started = time.perf_counter()
    currency = "INR" if country == "IN" else "GBP"
    candidates, stats = find_candidates(profile, country)
    stats["search_seconds"] = round(time.perf_counter() - started, 1)
    yield {"type": "start", "checking": len(candidates), "currency": currency, "stats": stats}

    cards: list[ResultCard] = []
    failures = 0
    for judged, (candidate, verdict) in enumerate(judge_as_completed(candidates, profile, country, language), start=1):
        if verdict is None:
            failures += 1
        elif verdict.verdict != "not_eligible":
            card = build_card(candidate, verdict)
            cards.append(card)
            yield {"type": "card", "card": card.model_dump()}
        yield {"type": "progress", "judged": judged}  # for the progress bar, including "not eligible" ones

    stats["judge_seconds"] = round(time.perf_counter() - started - stats["search_seconds"], 1)
    stats["judge_failures"] = failures
    stats["not_eligible"] = len(candidates) - failures - len(cards)
    total, potential = totals(cards)
    yield {"type": "done", "total_yearly": total, "potential_yearly": potential, "currency": currency, "stats": stats}


def find_results(profile: Profile, country: Country, language: Language) -> Results:
    """Same pipeline, all at once (used by scripts and the non-streaming endpoint)."""
    cards: list[ResultCard] = []
    done: dict = {}
    for event in stream_results(profile, country, language):
        if event["type"] == "card":
            cards.append(ResultCard.model_validate(event["card"]))
        elif event["type"] == "done":
            done = event
    cards.sort(key=sort_key)
    return Results(
        cards=[c for c in cards if c.fit != "weak"],
        other_cards=[c for c in cards if c.fit == "weak"],
        total_yearly=done["total_yearly"],
        potential_yearly=done["potential_yearly"],
        currency=done["currency"],
        stats=done["stats"],
    )
