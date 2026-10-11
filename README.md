# Haq

An AI caseworker that finds the government benefits you're entitled to, tells you exactly how to claim them, and helps you appeal rejections.

Built for the Nebius x NVIDIA Global AI Hackathon with NVIDIA Nemotron models on Nebius Token Factory.

> Work in progress — full README with architecture, Nemotron usage, and deployment coming soon.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env          # then add your Nebius API key
```

## Data ingestion

```bash
python -m ingest.uk           # UK benefits from the GOV.UK Content API
```

Output: `data/processed/uk.json`

## Data sources and attribution

- UK: [GOV.UK](https://www.gov.uk) content, licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- India: [myScheme.gov.in](https://www.myscheme.gov.in), Government of India.

Haq provides guidance only. Always confirm eligibility on the official website before applying.

## License

[MIT](LICENSE)
