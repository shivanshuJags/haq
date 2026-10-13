"""Build the catalog snapshot the API runs from: every scheme + its rules + its embedding.

Why a snapshot? The data changes only when the weekly ingest runs, and it's small (~1,000 schemes,
~10 MB). Shipping it inside the container means the API starts in about a second and never
depends on the database being awake or reachable — a free Neon database sleeps when idle and
can take a minute to answer from far away. PostgreSQL + pgvector stay the system of record for
the data pipeline (ingest, db/load.py, scripts/try_search.py).

Run from the project root (after ingest.extract_rules):
    python -m db.snapshot

Output: data/snapshot/schemes.json and data/snapshot/embeddings.npy (row i = schemes[i]).
"""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from core.config import ROOT
from core.embeddings import DIMENSIONS, embed_documents, scheme_document
from core.schemes import load_all

SNAPSHOT_DIR = ROOT / "data" / "snapshot"
CACHE_DIR = ROOT / "data" / "embedding_cache"  # one .npy per text hash, saved as we go
RULES_FILE = ROOT / "data" / "processed" / "rules.json"
BATCH = 8
WORKERS = 8


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    schemes = sorted(load_all(), key=lambda s: s["id"])
    rules = json.loads(RULES_FILE.read_text(encoding="utf-8"))

    # Reuse embeddings from the previous snapshot when a scheme's text hasn't changed
    previous: dict[str, np.ndarray] = {}
    old_schemes, old_vectors = SNAPSHOT_DIR / "schemes.json", SNAPSHOT_DIR / "embeddings.npy"
    if old_schemes.exists() and old_vectors.exists():
        vectors = np.load(old_vectors)
        for i, old in enumerate(json.loads(old_schemes.read_text(encoding="utf-8"))):
            previous[old["embedding_hash"]] = vectors[i]

    documents = [scheme_document(s) for s in schemes]
    hashes = [text_hash(d) for d in documents]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for h in hashes:
        if h not in previous and (CACHE_DIR / f"{h}.npy").exists():
            previous[h] = np.load(CACHE_DIR / f"{h}.npy")
    todo = [i for i, h in enumerate(hashes) if h not in previous]
    print(f"{len(schemes)} schemes: {len(schemes) - len(todo)} embeddings reused, {len(todo)} to compute", flush=True)

    new_vectors: dict[int, np.ndarray] = {}

    def embed_batch(batch: list[int]) -> None:
        for i, vector in zip(batch, embed_documents([documents[i] for i in batch])):
            new_vectors[i] = np.asarray(vector, dtype=np.float32)
            np.save(CACHE_DIR / f"{hashes[i]}.npy", new_vectors[i])  # survives a crash or Ctrl+C

    # Several batches at once: each request mostly waits on the network
    batches = [todo[start : start + BATCH] for start in range(0, len(todo), BATCH)]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for done, _ in enumerate(pool.map(embed_batch, batches), start=1):
            print(f"  {min(done * BATCH, len(todo))}/{len(todo)}", flush=True)

    matrix = np.zeros((len(schemes), DIMENSIONS), dtype=np.float32)
    records = []
    for i, scheme in enumerate(schemes):
        matrix[i] = new_vectors[i] if i in new_vectors else previous[hashes[i]]
        records.append({**scheme, "rules": rules.get(scheme["id"]), "embedding_hash": hashes[i]})

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    (SNAPSHOT_DIR / "schemes.json").write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    np.save(SNAPSHOT_DIR / "embeddings.npy", matrix)
    size_mb = sum(p.stat().st_size for p in SNAPSHOT_DIR.iterdir()) / 1e6
    print(f"Saved snapshot of {len(records)} schemes to {SNAPSHOT_DIR} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
