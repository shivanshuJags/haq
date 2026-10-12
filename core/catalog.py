"""In-memory copy of every scheme (without embeddings), loaded once from the database.

Scheme data only changes when the weekly ingest runs, so there's no reason to fetch
names, rules and sections from the database on every request. The API reads them from
memory; the database is only asked the one thing it's uniquely good at: vector similarity.
"""
from dataclasses import dataclass
from functools import lru_cache

from core.db import pooled
from core.rules import EligibilityRules


@dataclass(frozen=True)
class Scheme:
    id: str
    country: str
    regions: list[str] | None
    name: str
    summary: str | None
    categories: list[str]
    sections: dict
    apply_url: str | None
    source_url: str
    source: str | None
    meta: dict
    rules: EligibilityRules


@lru_cache  # load once per process; call catalog.cache_clear() after a data refresh
def catalog() -> dict[str, Scheme]:
    with pooled() as conn:
        rows = conn.execute("""
            SELECT id, country, regions, name, summary, categories, sections,
                   apply_url, source_url, source, meta, rules
            FROM schemes
        """).fetchall()
    return {
        row["id"]: Scheme(**{**row, "rules": EligibilityRules.model_validate(row["rules"] or {})})
        for row in rows
    }
