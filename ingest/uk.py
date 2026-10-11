"""Download UK benefits from the GOV.UK Content API into Haq's common scheme format.

Run from the project root:
    python -m ingest.uk
"""
from datetime import datetime, timezone

from markdownify import markdownify

from ingest.common import PROCESSED_DIR, RAW_DIR, PoliteClient, save_json

SEARCH_URL = "https://www.gov.uk/api/search.json"
CONTENT_URL = "https://www.gov.uk/api/content"

# Sub-sections of https://www.gov.uk/browse/benefits.
# "manage-your-benefit" is skipped: it is about changing an existing claim, not new benefits.
CATEGORIES = [
    "families",
    "help-for-carers",
    "disability",
    "looking-for-work",
    "low-income",
    "unable-to-work",
    "bereavement",
]

# Interactive tools with no static text worth storing.
SKIP_FORMATS = {"smart_answer", "calculator", "simple_smart_answer"}

# A guide is split into "parts" (Eligibility, What you'll get, ...). We map each part
# title to one of our section names. Order matters: first match wins.
SECTION_RULES = [
    ("eligibility", ("eligib", "who can", "can get", "qualify")),
    ("documents", ("what you need", "documents", "information you need")),
    ("benefits", ("what you'll get", "what you get", "how much", "amount", "rates")),
    ("how_to_apply", ("how to claim", "how to apply", "make a claim", "apply")),
]

# For pages without parts, these `details` fields hold the readable text.
TEXT_FIELDS = ["introductory_paragraph", "introduction", "body", "need_to_know", "more_information"]

SECTIONS = ["overview", "eligibility", "benefits", "documents", "how_to_apply", "other"]


def classify_part(title: str) -> str:
    lowered = title.lower()
    for section, keywords in SECTION_RULES:
        if any(word in lowered for word in keywords):
            return section
    return "other"


def html_to_md(html: str) -> str:
    md = markdownify(html, heading_style="ATX").strip()
    # GOV.UK uses site-relative links like (/state-pension-age); make them absolute
    return md.replace("](/", "](https://www.gov.uk/")


def list_benefits(client: PoliteClient) -> dict[str, dict]:
    """Return {"/universal-credit": {"title": ..., "format": ..., "categories": [...]}, ...}"""
    benefits: dict[str, dict] = {}
    for category in CATEGORIES:
        data = client.get_json(SEARCH_URL, params={
            "filter_mainstream_browse_pages": f"benefits/{category}",
            "count": 100,
            "fields": "title,link,format",
        })
        for result in data["results"]:
            entry = benefits.setdefault(result["link"], {
                "title": result["title"],
                "format": result.get("format"),
                "categories": [],
            })
            entry["categories"].append(category)
        print(f"  {category}: {data['total']} pages")
    return benefits


def to_record(content: dict, categories: list[str]) -> dict:
    """Convert one GOV.UK content item into Haq's common scheme format."""
    details = content.get("details", {})
    sections: dict[str, list[str]] = {name: [] for name in SECTIONS}

    parts = details.get("parts") or []
    if parts:
        for part in parts:
            section = classify_part(part["title"])
            sections[section].append(f"## {part['title']}\n\n{html_to_md(part['body'])}")
    else:
        for field in TEXT_FIELDS:
            value = details.get(field)
            if isinstance(value, str) and value.strip():
                sections["overview"].append(html_to_md(value))

    base_path = content["base_path"]
    return {
        "id": f"uk:{base_path.strip('/')}",
        "country": "UK",
        "region": None,
        "name": content["title"],
        "summary": content.get("description"),
        "categories": categories,
        "format": content.get("schema_name"),
        "sections": {name: "\n\n".join(texts) for name, texts in sections.items()},
        "apply_url": details.get("transaction_start_link"),
        "source_url": f"https://www.gov.uk{base_path}",
        "source": "GOV.UK",
        "license": "Open Government Licence v3.0",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> None:
    raw_dir = RAW_DIR / "uk"
    records = []

    with PoliteClient(delay=0.3) as client:
        print("Listing UK benefits...")
        benefits = list_benefits(client)
        print(f"Found {len(benefits)} unique pages. Downloading...")

        for path, info in benefits.items():
            if info["format"] in SKIP_FORMATS:
                print(f"  skip  {path} ({info['format']})")
                continue
            try:
                content = client.get_json(f"{CONTENT_URL}{path}")
            except Exception as error:
                print(f"  FAIL  {path}: {error}")
                continue
            save_json(raw_dir / f"{path.strip('/').replace('/', '__')}.json", content)
            records.append(to_record(content, info["categories"]))
            print(f"  ok    {path}")

    out_file = PROCESSED_DIR / "uk.json"
    save_json(out_file, records)

    with_eligibility = sum(1 for r in records if r["sections"]["eligibility"])
    print(f"\nSaved {len(records)} records to {out_file}")
    print(f"{with_eligibility} have a dedicated eligibility section")


if __name__ == "__main__":
    main()
