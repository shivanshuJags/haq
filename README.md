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

## Data pipeline

```bash
python -m ingest.uk              # UK benefits from the GOV.UK Content API   -> data/processed/uk.json
python -m ingest.india           # UP, Bihar + central schemes from myScheme -> data/processed/india.json
python -m ingest.extract_rules   # Nemotron Super: eligibility text -> rules -> data/processed/rules.json
python -m db.load                # load into PostgreSQL + embeddings (needs DATABASE_URL)
python -m db.snapshot            # catalog snapshot the API runs from -> data/snapshot/
```

## Run locally

One command (Windows) starts both servers in their own windows and opens the app:

```bash
powershell -ExecutionPolicy Bypass -File dev.ps1
```

Or start them yourself, in two terminals:

```bash
.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000   # backend — http://localhost:8000/docs
cd web && npm install && npm run dev                           # frontend — http://localhost:5173
```

The frontend needs the backend running: without it every request fails with a 502.

```bash
pytest                           # backend unit tests
```

Checks:

```bash
python -m scripts.check_llm      # Nemotron models reachable, Hinglish + tool calling
python -m scripts.try_search     # vector search with sample queries
```

## Data sources and attribution

- UK: [GOV.UK](https://www.gov.uk) content, licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
- India: [myScheme.gov.in](https://www.myscheme.gov.in), Government of India.

Haq provides guidance only. Always confirm eligibility on the official website before applying.

## License

[MIT](LICENSE)
