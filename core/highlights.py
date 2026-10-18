"""What the welcome screen shows for a country (and Indian state) — straight from the catalog, no AI.

  stats       how many schemes Haq knows for this place
  categories  "browse by category" tiles with counts (like myScheme.gov.in)
  popular     hand-picked, widely used schemes (national + the state's own)
  recent      recently launched (India: launch date) / recently updated (UK: GOV.UK update date)

There is no reliable public feed of *upcoming* policies, so we only show dated, official facts.
"""
from collections import Counter
from functools import lru_cache

from pydantic import BaseModel

from core.candidates import PEOPLE
from core.catalog import catalog

# Widely used schemes, in display order. Edit freely — unknown ids are skipped.
POPULAR: dict[str, list[str]] = {
    "IN": ["in:pm-kisan", "in:ab-pmjay", "in:pmuy2", "in:pmay-g", "in:pmjdy", "in:apy", "in:pmmy", "in:pmvs"],
    "UK": ["uk:universal-credit", "uk:child-benefit", "uk:pip", "uk:pension-credit", "uk:carers-allowance",
           "uk:attendance-allowance", "uk:housing-benefit", "uk:winter-fuel-payment"],
}
POPULAR_BY_STATE: dict[str, list[str]] = {
    "Bihar": ["in:pmssb", "in:bsccs", "in:cmkuy", "in:ignoapsb"],
    "Uttar Pradesh": ["in:ksy", "in:upoaps", "in:mpss", "in:kvsy"],
}

# GOV.UK's browse-section slugs -> readable category names
UK_CATEGORY_NAMES = {
    "families": "Families & children", "disability": "Disability", "low-income": "Low income",
    "bereavement": "Bereavement", "looking-for-work": "Looking for work", "help-for-carers": "Carers",
    "unable-to-work": "Unable to work",
}

TOP_CATEGORIES = 8
TOP_RECENT = 5


class SchemeLink(BaseModel):
    id: str
    name: str
    summary: str | None = None
    source_url: str
    is_state_scheme: bool = False
    date: str | None = None


class Category(BaseModel):
    name: str
    count: int


class Highlights(BaseModel):
    country: str
    region: str | None
    schemes: int
    national: int
    state: int
    categories: list[Category]
    popular: list[SchemeLink]
    recent: list[SchemeLink]


def _for_people(scheme) -> bool:
    targets = set(scheme.meta.get("target_beneficiaries") or [])
    return not targets or bool(targets & PEOPLE)


def _link(scheme, date: str | None = None) -> SchemeLink:
    return SchemeLink(id=scheme.id, name=scheme.name.strip(), summary=(scheme.summary or "").strip()[:180] or None,
                      source_url=scheme.source_url, is_state_scheme=bool(scheme.regions), date=date)


# The catalog only changes on a redeploy, so each country/state is worked out once per server start
# (~0.2 s over ~1,000 schemes) and then answered from memory. Bounded: `region` comes from the URL.
@lru_cache(maxsize=64)
def highlights(country: str, region: str | None) -> Highlights:
    data = catalog()
    # National schemes + the person's state (same rule as the search)
    here = [s for s in data.schemes.values()
            if s.country == country and (not s.regions or (region and region in s.regions))]
    state_count = sum(1 for s in here if s.regions)

    categories = Counter(c for s in here for c in s.categories)
    named = [Category(name=UK_CATEGORY_NAMES.get(name, name), count=count)
             for name, count in categories.most_common(TOP_CATEGORIES)]

    ids = POPULAR.get(country, [])
    if region:
        ids = POPULAR_BY_STATE.get(region, []) + ids  # the state's own schemes first
    popular = [_link(data[i]) for i in ids if data.get(i)]

    date_field = "updated" if country == "UK" else "open_date"
    # Only schemes people can apply for themselves (not ones for industries or institutions)
    dated = [(s.meta.get(date_field), s) for s in here
             if s.meta.get(date_field) and _for_people(s)]
    dated.sort(key=lambda pair: pair[0], reverse=True)
    recent = [_link(s, date) for date, s in dated[:TOP_RECENT]]

    return Highlights(country=country, region=region, schemes=len(here), national=len(here) - state_count,
                      state=state_count, categories=named, popular=popular, recent=recent)
