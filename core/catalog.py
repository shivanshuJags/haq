"""In-memory copy of every scheme — including its embedding — loaded once at startup.

Scheme data only changes when the weekly ingest runs, so the API keeps all ~1,000 schemes in
memory (~4 MB of vectors) and answers "which schemes are closest in meaning?" itself, with numpy.
That's microseconds per request, and no request ever waits on the database.

It loads from the snapshot shipped inside the app (db/snapshot.py) — or, if there is none,
straight from PostgreSQL.
"""
import json
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from core.config import ROOT
from core.db import connect
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


@dataclass(frozen=True)
class Catalog:
    schemes: dict[str, Scheme]
    ids: list[str]            # row i of `vectors` belongs to scheme ids[i]
    vectors: np.ndarray       # shape (n, 1024), each row normalised to length 1

    def __getitem__(self, scheme_id: str) -> Scheme:
        return self.schemes[scheme_id]

    def __len__(self) -> int:
        return len(self.schemes)

    def get(self, scheme_id: str | None) -> Scheme | None:
        return self.schemes.get(scheme_id) if scheme_id else None

    def similar(self, query_vector: list[float], country: str, region: str | None) -> list[tuple[Scheme, float]]:
        """Every scheme for this country (national + the person's state), with cosine similarity
        to the query — the same thing pgvector's `<=>` computes, done in memory."""
        query = np.asarray(query_vector, dtype=np.float32)
        query /= np.linalg.norm(query)
        similarities = self.vectors @ query  # one dot product per scheme (vectors are pre-normalised)
        results = []
        for scheme_id, similarity in zip(self.ids, similarities):
            scheme = self.schemes[scheme_id]
            if scheme.country != country:
                continue
            if scheme.regions and region not in scheme.regions:
                continue
            results.append((scheme, float(similarity)))
        return results


SNAPSHOT_DIR = ROOT / "data" / "snapshot"


def _build(rows: list[dict], vectors: list) -> Catalog:
    schemes, ids = {}, []
    for row in rows:
        fields = {name: row.get(name) for name in Scheme.__dataclass_fields__ if name != "rules"}
        fields["meta"] = fields["meta"] or {}
        fields["categories"] = fields["categories"] or []
        schemes[row["id"]] = Scheme(**fields, rules=EligibilityRules.model_validate(row.get("rules") or {}))
        ids.append(row["id"])
    matrix = np.vstack(vectors).astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    return Catalog(schemes=schemes, ids=ids, vectors=matrix)


def _from_snapshot() -> Catalog:
    rows = json.loads((SNAPSHOT_DIR / "schemes.json").read_text(encoding="utf-8"))
    return _build(rows, list(np.load(SNAPSHOT_DIR / "embeddings.npy")))


def _from_database() -> Catalog:
    with connect() as conn:
        rows = conn.execute("""
            SELECT id, country, regions, name, summary, categories, sections,
                   apply_url, source_url, source, meta, rules, embedding
            FROM schemes
            WHERE embedding IS NOT NULL
            ORDER BY id
        """).fetchall()

    vectors = []
    for row in rows:
        embedding = row.pop("embedding")
        vectors.append(embedding.to_numpy() if hasattr(embedding, "to_numpy") else np.asarray(embedding))
    return _build(rows, vectors)


@lru_cache  # load once per process
def catalog() -> Catalog:
    """From the snapshot shipped with the app when it exists (fast, no network), else the database."""
    if (SNAPSHOT_DIR / "embeddings.npy").exists():
        return _from_snapshot()
    return _from_database()
