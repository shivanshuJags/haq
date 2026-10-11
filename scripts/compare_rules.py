"""US-104 cross-check: compare Nemotron's extracted rules with myScheme's own tags.

For every Indian scheme and every field we sort the result into one of:
  agree      — both say the same restriction (or both say none)
  missed     — myScheme has a restriction, Nemotron left the field empty.
               Safe: nobody gets wrongly excluded; Ultra still reads the text later.
  conflict   — Nemotron added or changed a restriction that myScheme doesn't have.
               Risky: could wrongly exclude people. These go to a review file.

Run from the project root (after ingest.extract_rules and ingest.india_tags):
    python -m scripts.compare_rules
"""
import json
from collections import Counter

from ingest.common import PROCESSED_DIR, save_json

CASTE = {
    "Scheduled Caste (SC)": "SC",
    "Scheduled Tribe (ST)": "ST",
    "Other Backward Class (OBC)": "OBC",
    "Particularly Vulnerable Tribal Group (PVTG)": "PVTG",
    "General": "General",
    "De-Notified, Nomadic, and Semi-Nomadic (DNT) communities": "DNT",
}
OCCUPATION = {
    "Farmer": "farmer",
    "Student": "student",
    "Unorganized Worker": "unorganised_worker",
    "Construction Worker": "construction_worker",
    "Artisans, Spinners & Weavers": "artisan_weaver",
    "Khadi Artisan": "artisan_weaver",
    "Coir Worker": "artisan_weaver",
    "Sportsperson": "sportsperson",
    "Ex Servicemen": "ex_serviceman",
    "Teacher / Faculty": "teacher",
    "Artists": "artist",
    "Fishermen": "fisherman",
    "Street Vendor": "street_vendor",
}
MARITAL = {"Never Married": "unmarried", "Married": "married", "Widowed": "widowed",
           "Divorced": "divorced", "Separated": "separated"}


def normalise_tags(tags: dict) -> dict:
    """Convert myScheme tag labels into the same values our rule schema uses."""
    return {
        "genders": {g.lower() for g in tags.get("genders", [])} or None,
        "caste_categories": {CASTE[c] for c in tags.get("caste_categories", []) if c in CASTE} or None,
        "occupations": {OCCUPATION[o] for o in tags.get("occupations", []) if o in OCCUPATION} or None,
        "marital_status": {MARITAL[m] for m in tags.get("marital_status", []) if m in MARITAL} or None,
        "residence": {r.lower() for r in tags.get("residence", [])} or None,
        "is_student": tags.get("is_student"),
        "bpl_required": tags.get("bpl_required"),
        "disability_required": tags.get("disability_required"),
    }


def normalise_rule(value):
    if isinstance(value, list):
        return set(value) or None
    if isinstance(value, str):
        return {value}
    if value is False:  # "must NOT be" — myScheme has no tag for that, treat as no positive restriction
        return None
    return value


def main() -> None:
    rules = json.loads((PROCESSED_DIR / "rules.json").read_text(encoding="utf-8"))
    raw_tags = json.loads((PROCESSED_DIR / "india_tags.json").read_text(encoding="utf-8"))
    india_ids = [scheme_id for scheme_id in rules if scheme_id.startswith("in:")]

    stats: dict[str, Counter] = {}
    conflicts = []
    for scheme_id in india_ids:
        tags = normalise_tags(raw_tags.get(scheme_id, {}))
        for field, tag_value in tags.items():
            rule_value = normalise_rule(rules[scheme_id].get(field))
            counter = stats.setdefault(field, Counter())
            if rule_value == tag_value:
                counter["agree"] += 1
            elif rule_value is None:
                counter["missed"] += 1
            else:
                counter["conflict"] += 1
                conflicts.append({"id": scheme_id, "field": field,
                                  "nemotron": sorted(rule_value) if isinstance(rule_value, set) else rule_value,
                                  "myscheme": sorted(tag_value) if isinstance(tag_value, set) else tag_value})

    print(f"Compared {len(india_ids)} Indian schemes\n")
    print(f"{'field':22}{'agree':>8}{'missed':>8}{'conflict':>10}")
    total = Counter()
    for field, counter in stats.items():
        total.update(counter)
        print(f"{field:22}{counter['agree']:>8}{counter['missed']:>8}{counter['conflict']:>10}")
    checks = sum(total.values())
    print(f"{'TOTAL':22}{total['agree']:>8}{total['missed']:>8}{total['conflict']:>10}")
    print(f"\nAgreement: {total['agree'] / checks:.1%} · conflicts to review: {len(conflicts)}")

    save_json(PROCESSED_DIR / "rules_conflicts.json", conflicts)
    print(f"Conflicts saved to {PROCESSED_DIR / 'rules_conflicts.json'}")


if __name__ == "__main__":
    main()
