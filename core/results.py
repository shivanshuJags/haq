"""US-301/302/303/304: the full "what am I entitled to?" pipeline, producing result cards.

profile -> candidates (rules engine + vector ranking) -> Ultra verdicts -> sorted cards + total
"""
import html
import re
import time

from pydantic import BaseModel

from core.candidates import find_candidates
from core.profile import Country, Profile
from core.profile_agent import Language
from core.verdict import Fit, Reason, VerdictType, judge_all

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


def find_results(profile: Profile, country: Country, language: Language) -> Results:
    started = time.perf_counter()
    candidates, stats = find_candidates(profile, country)
    stats["search_seconds"] = round(time.perf_counter() - started, 1)

    judged = judge_all(candidates, profile, country, language)
    stats["judge_seconds"] = round(time.perf_counter() - started - stats["search_seconds"], 1)
    stats["judge_failures"] = sum(v is None for _, v in judged)

    cards = []
    for candidate, verdict in judged:
        if verdict is None or verdict.verdict == "not_eligible":
            continue
        scheme = candidate.scheme
        cards.append((candidate.score, ResultCard(
            id=scheme.id,
            name=scheme.name,
            summary=scheme.summary,
            is_state_scheme=candidate.is_state_scheme,
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
        )))

    # Best verdict first; within a verdict, most relevant first
    cards.sort(key=lambda pair: (VERDICT_ORDER[pair[1].verdict], -pair[0]))
    ordered = [card for _, card in cards]
    stats["not_eligible"] = len(judged) - stats["judge_failures"] - len(ordered)

    main = [c for c in ordered if c.fit != "weak"]
    other = [c for c in ordered if c.fit == "weak"]
    total = sum(c.yearly_amount or 0 for c in main if c.verdict in COUNTED_FOR_TOTAL)
    potential = sum(c.yearly_amount or 0 for c in main)
    return Results(cards=main, other_cards=other, total_yearly=total, potential_yearly=potential,
                   currency="INR" if country == "IN" else "GBP", stats=stats)
