"""US-301 steps 1 + 2: find candidate schemes for a profile and rank them.

1. Take EVERY scheme for the person's country + state (not just the top search hits),
   and drop the ones the rules engine says they clearly fail. This way a matching
   state scheme can never be missed just because search ranked it low.
2. Rank what's left by how close its meaning is to the person's situation (vector
   similarity), with a small penalty for each rule we couldn't confirm.
3. Keep the best ones for Nemotron Ultra, reserving a few slots for state schemes,
   which would otherwise be buried under hundreds of national schemes.
"""
from dataclasses import dataclass

from core.catalog import Scheme, catalog
from core.eligibility import Assessment, assess
from core.embeddings import embed_query
from core.profile import Country, Profile

UNKNOWN_PENALTY = 0.02   # per rule we couldn't confirm
PASS_BONUS = 0.03        # per rule the person clearly meets (e.g. "has children" for Child Benefit)
SHORTLIST = 20           # schemes sent to Nemotron Ultra
TOP_STATE = 5            # of those, reserved for state schemes (India) so national ones can't crowd them out

# Pages in the data that are tools or guidance, not benefits someone can claim
NOT_BENEFITS = {
    "uk:benefits-calculators",
    "uk:bills-benefits",
    "uk:support-visit-benefit-claim",
    "uk:universal-credit-reviews",
    "uk:when-someone-dies",
    "uk:check-if-youre-eligible-for-warm-home-discount",  # duplicate of the Warm Home Discount page
}


@dataclass
class Candidate:
    scheme: Scheme
    similarity: float
    assessment: Assessment

    @property
    def score(self) -> float:
        passes = sum(check.status == "pass" for check in self.assessment.checks)
        return self.similarity - UNKNOWN_PENALTY * self.assessment.unknown_count + PASS_BONUS * passes

    @property
    def is_state_scheme(self) -> bool:
        return bool(self.scheme.regions)


def search_query(profile: Profile, country: Country) -> str:
    """Describe the person in one paragraph — searching with the full picture works far
    better than with their raw message (see US-105 finding)."""
    facts = []
    if profile.age:
        facts.append(f"{profile.age} year old")
    if profile.gender:
        facts.append(profile.gender)
    if profile.caste_category:
        facts.append(profile.caste_category)
    if profile.occupation:
        facts.append(profile.occupation.replace("_", " "))
    elif profile.is_student:
        facts.append("student")
    if profile.education_level:
        facts.append(f"education: {profile.education_level}")
    if profile.has_disability:
        facts.append("with a disability")
    if profile.has_children:
        facts.append("has children")
    if profile.is_carer:
        facts.append("carer")
    if profile.region:
        facts.append(f"living in {profile.region}")
    income = profile.annual_family_income or profile.personal_annual_income
    if income is not None:
        currency = "rupees" if country == "IN" else "pounds"
        facts.append(f"yearly income {income} {currency}")
    need = profile.needs or "government support they are eligible for"
    return f"{', '.join(facts)}. Needs: {need}"


def find_candidates(profile: Profile, country: Country) -> tuple[list[Candidate], dict]:
    """Returns (shortlist for Ultra, stats about how many schemes were checked)."""
    # Similarity to every national + state scheme, computed in memory (core/catalog.py)
    rows = catalog().similar(embed_query(search_query(profile, country)), country, profile.region)

    kept: list[Candidate] = []
    failed = 0
    for scheme, similarity in rows:
        if scheme.id in NOT_BENEFITS:
            continue
        assessment = assess(scheme.rules, profile)
        if assessment.status == "fail":
            failed += 1
            continue
        kept.append(Candidate(scheme, similarity, assessment))

    kept.sort(key=lambda c: c.score, reverse=True)
    if profile.region:
        # India with a state: best overall + reserved slots for the best state schemes not already in
        shortlist = kept[: SHORTLIST - TOP_STATE]
        shortlist += [c for c in kept[SHORTLIST - TOP_STATE :] if c.is_state_scheme][:TOP_STATE]
    else:
        # UK (or India without a state): no state schemes to protect, so use every slot
        shortlist = kept[:SHORTLIST]

    stats = {"checked": len(rows), "ruled_out": failed, "possible": len(kept), "shortlisted": len(shortlist)}
    return shortlist, stats
