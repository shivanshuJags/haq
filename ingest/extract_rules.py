"""US-104: turn each scheme's eligibility text into structured rules with Nemotron Super.

Run from the project root:
    python -m ingest.extract_rules                         # all schemes
    python -m ingest.extract_rules --limit 20              # first 20 only
    python -m ingest.extract_rules --ids uk:universal-credit,in:pm-kisan

Results are cached per scheme in data/rules_cache/. A scheme is only sent to the
model again if its eligibility text changed (or with --force), so re-runs are cheap.
"""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import ValidationError

from core.llm import MODELS, chat_json
from core.rules import EligibilityRules, sanitize, schema_for_prompt
from core.schemes import load_all
from ingest.common import PROCESSED_DIR, ROOT, save_json

MODEL = "super"
CACHE_DIR = ROOT / "data" / "rules_cache"
MAX_INPUT_CHARS = 8000
WORKERS = 6

SYSTEM_PROMPT = f"""You convert the eligibility criteria of a government scheme into structured JSON rules.

Return ONLY one JSON object with exactly these keys:
{schema_for_prompt()}

These fields are used as HARD FILTERS: if a person fails one, they are told they are NOT eligible.
Wrongly excluding an eligible person is the worst possible mistake. So:
- Only fill a field with a condition that EVERY applicant must meet.
- If the text gives alternatives ("any of the following", "or"), and the alternatives mix different kinds of
  conditions (e.g. "SC households OR ration card holders OR forest dwellers"), do NOT fill any field from that
  list. Put the whole list in other_conditions as one sentence.
- If a limit differs between groups (e.g. income limit ₹2.5 lakh for EBC and ₹3 lakh for OBC; or rural vs urban),
  put the LOOSEST value in the field (here income_max = 300000) and describe the exact per-group limits in other_conditions.
- Booleans: true = must be; false = must NOT be (e.g. "must not be in full-time education" -> is_student false).
  Use false ONLY when the text explicitly excludes it. If the text says nothing about it, use null.

Rules for filling it:
- Use null when the text does NOT restrict on that field. Never guess or add requirements that are not written.
- Only set a field when the text states it as a requirement of the APPLICANT (not of a family member, unless it is family income).
- Money: plain integers in the scheme's currency (INR for India, GBP for UK). "2.5 lakh" = 250000. If a limit is monthly, multiply by 12.
- Ages in years. "18 years or above" -> age_min 18. "below 40" -> age_max 39.
- Lists (genders, caste_categories, occupations, ...) contain the ALLOWED values only, using the exact allowed spellings.
- "Backward Class (BC)" in Bihar -> "OBC"; "Extremely Backward Class" -> "EBC".
- Do not encode the state/country of residence: that is handled separately.
- Anything that cannot be expressed in the fields (including exclusions like "government employees are not eligible")
  goes into other_conditions as a short plain-English sentence.
- confidence: "high" if the criteria are explicit, "medium" if partly vague, "low" if the text barely states criteria.
"""


def scheme_text(scheme: dict) -> str:
    """The text we send to the model for one scheme."""
    sections = scheme["sections"]
    eligibility = sections.get("eligibility") or sections.get("overview") or ""
    parts = [
        f"Scheme: {scheme['name']}",
        f"Country: {scheme['country']}",
        f"Summary: {scheme.get('summary') or ''}",
        f"Eligibility:\n{eligibility}",
    ]
    # Exclusions live in "other" for Indian schemes; they matter for eligibility
    if "## Exclusions" in (sections.get("other") or ""):
        exclusions = sections["other"].split("## Exclusions", 1)[1].split("\n## ", 1)[0]
        parts.append(f"Exclusions:{exclusions}")
    return "\n\n".join(parts)[:MAX_INPUT_CHARS]


def cache_path(scheme_id: str):
    return CACHE_DIR / f"{scheme_id.replace(':', '__').replace('/', '__')}.json"


def extract(scheme: dict, force: bool = False) -> tuple[str, dict | None, str]:
    """Returns (scheme_id, rules or None, status)."""
    text = scheme_text(scheme)
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    path = cache_path(scheme["id"])

    if not force and path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("input_hash") == text_hash:
            return scheme["id"], cached["rules"], "cached"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    # Up to 2 tries: if the JSON is invalid, show the model its mistake and ask again.
    raw = None
    for _ in range(2):
        try:
            raw = chat_json(MODEL, messages, max_tokens=3000)
            rules = EligibilityRules.model_validate(raw).model_dump()
            save_json(path, {"input_hash": text_hash, "model": MODELS[MODEL], "rules": rules})
            return scheme["id"], rules, "extracted"
        except (ValueError, ValidationError) as error:
            messages += [
                {"role": "assistant", "content": json.dumps(raw) if raw is not None else "(no JSON)"},
                {"role": "user", "content": f"That was invalid: {str(error)[:800]}\nReturn corrected JSON only."},
            ]
        except Exception as error:  # network / API errors
            return scheme["id"], None, f"error: {error}"
    return scheme["id"], None, "invalid after retry"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract structured eligibility rules with Nemotron Super")
    parser.add_argument("--limit", type=int, help="only process the first N schemes")
    parser.add_argument("--ids", help="comma-separated scheme ids to process")
    parser.add_argument("--force", action="store_true", help="ignore the cache")
    args = parser.parse_args()

    schemes = load_all()
    if args.ids:
        wanted = set(args.ids.split(","))
        schemes = [s for s in schemes if s["id"] in wanted]
    if args.limit:
        schemes = schemes[: args.limit]

    print(f"Extracting rules for {len(schemes)} schemes with {MODELS[MODEL]} ({WORKERS} at a time)...")
    results: dict[str, dict] = {}
    failures = []
    counts = {"cached": 0, "extracted": 0}

    # Run several model calls in parallel: each call mostly waits on the network.
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(extract, s, args.force) for s in schemes]
        for done, future in enumerate(as_completed(futures), start=1):
            scheme_id, rules, status = future.result()
            if rules is None:
                failures.append((scheme_id, status))
            else:
                # Cache keeps the model's raw answer; cleanup rules are applied on top every run
                results[scheme_id] = sanitize(EligibilityRules.model_validate(rules)).model_dump()
                counts[status] += 1
            if done % 50 == 0 or done == len(schemes):
                print(f"  {done}/{len(schemes)}")

    # Merge into the full rules file (so partial runs don't wipe earlier results)
    out_file = PROCESSED_DIR / "rules.json"
    all_rules = json.loads(out_file.read_text(encoding="utf-8")) if out_file.exists() else {}
    all_rules.update(results)
    save_json(out_file, dict(sorted(all_rules.items())))

    print(f"\nDone: {counts['extracted']} extracted, {counts['cached']} from cache, {len(failures)} failed")
    for scheme_id, status in failures:
        print(f"  FAIL {scheme_id}: {status}")
    print(f"{len(all_rules)} schemes now have rules in {out_file}")


if __name__ == "__main__":
    main()
