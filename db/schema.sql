-- Haq database schema. Safe to run many times (everything is IF NOT EXISTS).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schemes (
    id              text PRIMARY KEY,           -- "uk:universal-credit", "in:pmssb"
    country         text NOT NULL,              -- "UK" | "IN"
    regions         text[],                     -- NULL = whole country, else e.g. {"Bihar"}
    name            text NOT NULL,
    summary         text,
    categories      text[] NOT NULL DEFAULT '{}',
    format          text,
    sections        jsonb NOT NULL,             -- overview, eligibility, benefits, documents, how_to_apply, other
    apply_url       text,
    source_url      text NOT NULL,
    source          text,
    license         text,
    meta            jsonb NOT NULL DEFAULT '{}',
    rules           jsonb,                      -- EligibilityRules (core/rules.py)
    fetched_at      timestamptz,
    embedding       vector(1024),               -- Qwen3-Embedding-8B, 1024 dims
    embedding_hash  text,                       -- hash of the text that was embedded
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- Fast "closest meaning" search (cosine distance)
CREATE INDEX IF NOT EXISTS schemes_embedding_idx ON schemes USING hnsw (embedding vector_cosine_ops);

-- Fast filtering by country and region
CREATE INDEX IF NOT EXISTS schemes_country_idx ON schemes (country);
CREATE INDEX IF NOT EXISTS schemes_regions_idx ON schemes USING gin (regions);
