# Manual data

Schemes written by hand, in the same common format as `data/processed/*.json`.
Used when an official source is missing or broken (e.g. myScheme's page for Ayushman Bharat PM-JAY).

- `india.json` — Indian schemes added manually. Records with `meta.needs_verification` must be checked
  against the official website before the demo.

The rules extractor (`python -m ingest.extract_rules`) includes these files automatically.
Manual records override processed records with the same `id`.
