"""Find schemes whose meaning is closest to some text (vector search, in memory)."""
from core.catalog import catalog
from core.embeddings import embed_query


def search(query: str, country: str, region: str | None = None, limit: int = 10) -> list[dict]:
    rows = catalog().similar(embed_query(query), country, region)
    rows.sort(key=lambda pair: pair[1], reverse=True)
    return [
        {"id": scheme.id, "name": scheme.name, "summary": scheme.summary, "regions": scheme.regions,
         "source_url": scheme.source_url, "similarity": similarity}
        for scheme, similarity in rows[:limit]
    ]
