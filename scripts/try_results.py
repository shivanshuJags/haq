"""Run the full results pipeline for the demo personas (calls Nemotron Ultra).

Run from the project root:
    python -m scripts.try_results            # all personas
    python -m scripts.try_results Priya      # one persona
"""
import sys

from core.profile import Profile
from core.results import find_results

PERSONAS = {
    "Priya": ("IN", "hinglish", Profile(
        region="Bihar", age=20, gender="female", caste_category="OBC", annual_family_income=150000,
        occupation="student", is_student=True, education_level="graduate", needs="money for college fees")),
    "Ramesh": ("IN", "hinglish", Profile(
        region="Uttar Pradesh", age=58, gender="male", caste_category="General", annual_family_income=80000,
        occupation="farmer", land_acres=2.5, needs="information about government schemes")),
    "Sarah": ("UK", "english", Profile(
        age=31, gender="female", has_children=True, children_count=2, personal_annual_income=10800, savings=500,
        has_disability=False, needs="help with rent")),
}


def show(name: str) -> None:
    country, language, profile = PERSONAS[name]
    results = find_results(profile, country, language)
    symbol = "₹" if results.currency == "INR" else "£"
    print(f"\n=== {name} === {results.stats}")
    print(f"Estimated total: {symbol}{results.total_yearly:,}/year (up to {symbol}{results.potential_yearly:,}) "
          f"from {len(results.cards)} schemes")
    print(f"Weak matches (collapsed): {[c.name[:40] for c in results.other_cards]}")
    for card in results.cards:
        print(f"\n  [{card.verdict} / {card.fit}] {card.name}{'  (state)' if card.is_state_scheme else ''}")
        print(f"    benefit: {card.benefit}  | yearly: {card.yearly_amount}")
        for reason in card.reasons:
            mark = {"met": "✓", "not_met": "✗", "unknown": "?"}[reason.status]
            print(f"    {mark} {reason.criterion}: {reason.explanation}")
        if card.to_confirm:
            print(f"    confirm: {card.to_confirm}")
        print(f"    documents: {card.documents[:4]}{' ...' if len(card.documents) > 4 else ''}")


if __name__ == "__main__":
    for persona in sys.argv[1:] or PERSONAS:
        show(persona)
