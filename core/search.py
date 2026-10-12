"""Find schemes whose meaning is closest to what the person said (vector search)."""
from pgvector import Vector

from core.db import pooled
from core.embeddings import embed_query

SEARCH_SQL = """
SELECT id, name, summary, regions, source_url,
       1 - (embedding <=> %(vector)s) AS similarity      -- <=> is cosine distance; 1 - distance = similarity
FROM schemes
WHERE country = %(country)s
  AND (regions IS NULL OR %(region)s::text = ANY(regions))  -- national schemes + the person's state
ORDER BY embedding <=> %(vector)s                         -- closest meaning first
LIMIT %(limit)s
"""


def search(query: str, country: str, region: str | None = None, limit: int = 10) -> list[dict]:
    vector = Vector(embed_query(query))
    with pooled() as conn:
        return conn.execute(SEARCH_SQL, {
            "vector": vector, "country": country, "region": region, "limit": limit,
        }).fetchall()
