"""Download Indian government schemes from myScheme.gov.in into Haq's common scheme format.

Covers: all Uttar Pradesh and Bihar state schemes + all central (Government of India) schemes.

Run from the project root:
    python -m ingest.india

Downloads are cached in data/raw/india/, so if the script stops halfway you can
simply run it again and it continues where it left off.
"""
import json
import re
from datetime import date, datetime, timezone

from ingest.common import PROCESSED_DIR, RAW_DIR, PoliteClient, save_json

API = "https://www.myscheme.gov.in/api/apisetu"
PAGE_SIZE = 100

# Matches the URL inside a markdown link: [text](https://...)
MARKDOWN_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")

# Each group is one search on myScheme: a name and the filters to send.
GROUPS = {
    "Uttar Pradesh": [
        {"identifier": "level", "value": "State"},
        {"identifier": "beneficiaryState", "value": "Uttar Pradesh"},
    ],
    "Bihar": [
        {"identifier": "level", "value": "State"},
        {"identifier": "beneficiaryState", "value": "Bihar"},
    ],
    "Central": [
        {"identifier": "level", "value": "Central"},
    ],
}


def search_all(client: PoliteClient, filters: list[dict]) -> list[dict]:
    """Page through search results and return every hit's `fields`."""
    hits = []
    start = 0
    while True:
        data = client.get_json(f"{API}/search/schemes", params={
            "lang": "en",
            "q": json.dumps(filters),
            "keyword": "",
            "sort": "multiple_sort",
            "from": start,
            "size": PAGE_SIZE,
        })["data"]["hits"]
        hits.extend(item["fields"] for item in data["items"])
        start += PAGE_SIZE
        if start >= data["page"]["total"]:
            return hits


def fetch_scheme(client: PoliteClient, slug: str) -> dict | None:
    """Download one scheme's details + required documents. Uses the raw cache if present."""
    cache_file = RAW_DIR / "india" / f"{slug}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    detail = client.get_json(f"{API}/schemes", params={"slug": slug, "lang": "en"})["data"]
    if not detail or not detail.get("en"):
        return None

    documents = None
    try:
        documents = client.get_json(f"{API}/schemes/{detail['_id']}/documents", params={"lang": "en"})["data"]
    except Exception:
        pass  # some schemes have no documents entry; that's fine

    raw = {"detail": detail, "documents": documents}
    save_json(cache_file, raw)
    return raw


def label(value) -> str | None:
    """myScheme stores many values as {"label": "...", "value": "..."}; return the label."""
    return value.get("label") if isinstance(value, dict) else value


def labels(values) -> list[str]:
    return [label(v) for v in (values or []) if label(v)]


def is_closed(close_date: str | None) -> bool:
    if not close_date:
        return False
    try:
        return date.fromisoformat(close_date[:10]) < date.today()
    except ValueError:
        return False


def build_how_to_apply(processes: list[dict]) -> tuple[str, str | None]:
    """Turn the list of application modes into markdown + the first online apply link."""
    parts = []
    apply_url = None
    for process in processes or []:
        mode = process.get("mode") or "Application"
        text = (process.get("process_md") or "").strip()
        parts.append(f"### {mode}\n\n{text}")
        if not apply_url:
            # Prefer the explicit url field; otherwise use the first link in the steps text.
            # Only online processes get an apply link — an offline form download isn't "apply here".
            found = MARKDOWN_LINK.search(text)
            if process.get("url"):
                apply_url = process["url"]
            elif found and "online" in mode.lower():
                apply_url = found.group(1)
    return "\n\n".join(parts), apply_url


def to_record(raw: dict, search_fields: dict, group: str) -> dict:
    """Convert one myScheme scheme into Haq's common scheme format."""
    detail = raw["detail"]
    en = detail["en"]
    basic = en.get("basicDetails") or {}
    content = en.get("schemeContent") or {}
    eligibility = en.get("eligibilityCriteria") or {}
    docs_en = ((raw.get("documents") or {}).get("en")) or {}

    how_to_apply, apply_url = build_how_to_apply(en.get("applicationProcess"))

    other = []
    if (content.get("exclusions_md") or "").strip():
        other.append(f"## Exclusions\n\n{content['exclusions_md'].strip()}")
    references = [r for r in content.get("references") or [] if r.get("url")]
    if references:
        links = "\n".join(f"* [{r.get('title') or r['url']}]({r['url']})" for r in references)
        other.append(f"## References\n\n{links}")

    # State schemes apply to that state; central schemes apply everywhere
    # unless myScheme lists specific states.
    states = [s for s in search_fields.get("beneficiaryState") or [] if s != "All"]
    regions = [group] if group != "Central" else (states or None)

    slug = detail["slug"]
    return {
        "id": f"in:{slug}",
        "country": "IN",
        "regions": regions,
        "name": basic.get("schemeName"),
        "summary": content.get("briefDescription"),
        "categories": labels(basic.get("schemeCategory")),
        "format": "central_scheme" if group == "Central" else "state_scheme",
        "sections": {
            "overview": (content.get("detailedDescription_md") or "").strip(),
            "eligibility": (eligibility.get("eligibilityDescription_md") or "").strip(),
            "benefits": (content.get("benefits_md") or "").strip(),
            "documents": (docs_en.get("documentsRequired_md") or "").strip(),
            "how_to_apply": how_to_apply,
            "other": "\n\n".join(other),
        },
        "apply_url": apply_url,
        "source_url": f"https://www.myscheme.gov.in/schemes/{slug}",
        "source": "myScheme.gov.in, Government of India",
        "license": "Reproduced with attribution per myScheme copyright policy",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "meta": {
            "level": label(basic.get("level")),
            "ministry": label(basic.get("nodalMinistryName")),
            "department": label(basic.get("nodalDepartmentName")),
            "benefit_type": label(content.get("benefitTypes")),
            "target_beneficiaries": labels(basic.get("targetBeneficiaries")),
            "tags": basic.get("tags") or [],
            "close_date": basic.get("schemeCloseDate"),
            "open_date": (basic.get("schemeOpenDate") or "")[:10] or None,  # launch date, for "recently launched"
        },
    }


def main() -> None:
    records = []
    missing = []  # listed in search but myScheme has no detail page — fill these by hand later
    seen = set()

    with PoliteClient(delay=0.4) as client:
        for group, filters in GROUPS.items():
            hits = search_all(client, filters)
            print(f"\n{group}: {len(hits)} schemes")

            for i, fields in enumerate(hits, start=1):
                slug = fields["slug"]
                if slug in seen:
                    continue
                seen.add(slug)

                if is_closed(fields.get("schemeCloseDate")):
                    print(f"  [{i}/{len(hits)}] closed  {slug}")
                    continue
                try:
                    raw = fetch_scheme(client, slug)
                except Exception as error:
                    print(f"  [{i}/{len(hits)}] FAIL    {slug}: {error}")
                    continue
                if raw is None:
                    print(f"  [{i}/{len(hits)}] empty   {slug}")
                    missing.append({"slug": slug, "name": fields.get("schemeName"), "group": group})
                    continue

                records.append(to_record(raw, fields, group))
                if i % 25 == 0 or i == len(hits):
                    print(f"  [{i}/{len(hits)}] done")

    out_file = PROCESSED_DIR / "india.json"
    save_json(out_file, records)
    save_json(PROCESSED_DIR / "india_missing.json", missing)

    print(f"\nSaved {len(records)} records to {out_file}")
    print(f"{len(missing)} schemes had no detail page (see india_missing.json)")
    print(f"  apply_url     {sum(1 for r in records if r['apply_url'])}/{len(records)}")
    for section in ["eligibility", "benefits", "documents", "how_to_apply"]:
        filled = sum(1 for r in records if r["sections"][section])
        print(f"  {section:13} {filled}/{len(records)}")


if __name__ == "__main__":
    main()
