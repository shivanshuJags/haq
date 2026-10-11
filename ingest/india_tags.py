"""Collect myScheme's own eligibility tags for every Indian scheme (US-104 cross-check).

myScheme tags each scheme with filters like gender, caste, student, occupation.
The detail API doesn't return these tags, but the search API can FILTER by them.
So for every tag value we search "which schemes have this tag?" and invert the result:

    search(gender=Female) -> [a, b, c]   =>   a: {gender: [Female]}, b: {...}, c: {...}

Run from the project root (after ingest.india):
    python -m ingest.india_tags
"""
import json
from collections import defaultdict

from ingest.common import PROCESSED_DIR, PoliteClient, save_json
from ingest.india import API, GROUPS, PAGE_SIZE

# myScheme filter identifier -> the key we store it under
FACETS = {
    "gender": "genders",
    "caste": "caste_categories",
    "isStudent": "is_student",
    "occupation": "occupations",
    "isBpl": "bpl_required",
    "disability": "disability_required",
    "residence": "residence",
    "maritalStatus": "marital_status",
}
# Values that mean "no restriction" — not useful as tags
IGNORE_VALUES = {"All", "No", "Both"}


def search(client: PoliteClient, filters: list[dict], size: int = PAGE_SIZE, start: int = 0) -> dict:
    return client.get_json(f"{API}/search/schemes", params={
        "lang": "en", "q": json.dumps(filters), "keyword": "",
        "sort": "multiple_sort", "from": start, "size": size,
    })["data"]


def slugs_matching(client: PoliteClient, filters: list[dict]) -> list[str]:
    slugs, start = [], 0
    while True:
        hits = search(client, filters, start=start)["hits"]
        slugs += [item["fields"]["slug"] for item in hits["items"]]
        start += PAGE_SIZE
        if start >= hits["page"]["total"]:
            return slugs


def main() -> None:
    tags: dict[str, dict] = defaultdict(dict)

    with PoliteClient(delay=0.3) as client:
        for group, group_filters in GROUPS.items():
            # One search with size=1 just to read which tag values exist in this group
            facets = {f["identifier"]: f["entries"] for f in search(client, group_filters, size=1)["facets"]}
            print(f"\n{group}")
            for identifier, key in FACETS.items():
                for entry in facets.get(identifier, []):
                    value = entry["label"]
                    if value in IGNORE_VALUES:
                        continue
                    filters = group_filters + [{"identifier": identifier, "value": value}]
                    slugs = slugs_matching(client, filters)
                    for slug in slugs:
                        scheme_tags = tags[f"in:{slug}"]
                        if value == "Yes":
                            scheme_tags[key] = True
                        else:
                            scheme_tags.setdefault(key, []).append(value)
                    print(f"  {identifier}={value}: {len(slugs)}")

    out_file = PROCESSED_DIR / "india_tags.json"
    save_json(out_file, dict(sorted(tags.items())))
    print(f"\nSaved tags for {len(tags)} schemes to {out_file}")


if __name__ == "__main__":
    main()
