"""US-105: load every scheme + its rules into PostgreSQL and compute embeddings.

Run from the project root:
    python -m db.load

Safe to re-run: schemes are upserted (insert or update), and embeddings are only
recomputed for schemes whose text changed.
"""
import hashlib
import json

from pgvector import Vector
from psycopg.types.json import Jsonb

from core.config import ROOT
from core.db import connect
from core.embeddings import embed_documents, scheme_document
from core.schemes import load_all

SCHEMA_FILE = ROOT / "db" / "schema.sql"
RULES_FILE = ROOT / "data" / "processed" / "rules.json"
EMBED_BATCH = 32

UPSERT = """
INSERT INTO schemes (id, country, regions, name, summary, categories, format, sections,
                     apply_url, source_url, source, license, meta, rules, fetched_at, updated_at)
VALUES (%(id)s, %(country)s, %(regions)s, %(name)s, %(summary)s, %(categories)s, %(format)s, %(sections)s,
        %(apply_url)s, %(source_url)s, %(source)s, %(license)s, %(meta)s, %(rules)s, %(fetched_at)s, now())
ON CONFLICT (id) DO UPDATE SET
    country = EXCLUDED.country, regions = EXCLUDED.regions, name = EXCLUDED.name,
    summary = EXCLUDED.summary, categories = EXCLUDED.categories, format = EXCLUDED.format,
    sections = EXCLUDED.sections, apply_url = EXCLUDED.apply_url, source_url = EXCLUDED.source_url,
    source = EXCLUDED.source, license = EXCLUDED.license, meta = EXCLUDED.meta,
    rules = EXCLUDED.rules, fetched_at = EXCLUDED.fetched_at, updated_at = now()
"""


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    schemes = load_all()
    rules = json.loads(RULES_FILE.read_text(encoding="utf-8"))

    with connect() as conn:
        print("Applying schema...")
        conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))

        print(f"Upserting {len(schemes)} schemes...")
        with conn.cursor() as cur:
            cur.executemany(UPSERT, [{
                **scheme,
                "sections": Jsonb(scheme["sections"]),
                "meta": Jsonb(scheme.get("meta") or {}),
                "rules": Jsonb(rules[scheme["id"]]) if scheme["id"] in rules else None,
            } for scheme in schemes])

        # Remove schemes that no longer exist in our data (e.g. closed since last load)
        current_ids = [s["id"] for s in schemes]
        deleted = conn.execute("DELETE FROM schemes WHERE NOT (id = ANY(%s))", (current_ids,)).rowcount
        if deleted:
            print(f"Removed {deleted} schemes that are no longer in the data")

        # Only embed schemes that are new or whose text changed
        existing = {row["id"]: row["embedding_hash"]
                    for row in conn.execute("SELECT id, embedding_hash FROM schemes")}
        todo = []
        for scheme in schemes:
            document = scheme_document(scheme)
            digest = text_hash(document)
            if existing.get(scheme["id"]) != digest:
                todo.append((scheme["id"], document, digest))

        print(f"Embedding {len(todo)} schemes ({len(schemes) - len(todo)} unchanged)...")
        for start in range(0, len(todo), EMBED_BATCH):
            batch = todo[start : start + EMBED_BATCH]
            vectors = embed_documents([document for _, document, _ in batch])
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE schemes SET embedding = %s, embedding_hash = %s WHERE id = %s",
                    [(Vector(vector), digest, scheme_id)
                     for (scheme_id, _, digest), vector in zip(batch, vectors)],
                )
            conn.commit()  # save progress after every batch
            print(f"  {min(start + EMBED_BATCH, len(todo))}/{len(todo)}")

        summary = conn.execute("""
            SELECT country, count(*) AS schemes, count(embedding) AS embedded, count(rules) AS with_rules
            FROM schemes GROUP BY country ORDER BY country
        """).fetchall()
    print("\nDatabase now contains:")
    for row in summary:
        print(f"  {row['country']}: {row['schemes']} schemes, {row['embedded']} embedded, {row['with_rules']} with rules")


if __name__ == "__main__":
    main()
