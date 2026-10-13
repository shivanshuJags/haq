# Haq backend (FastAPI) — the container Nebius Serverless (or any container host) runs.
# Build:  docker build -t haq-api .
# Run:    docker run -p 8000:8000 --env-file .env haq-api
FROM python:3.13-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8

# Install dependencies first, so code changes don't re-download every library
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only what the API needs at runtime: code + the catalog snapshot (schemes, rules, embeddings),
# so the container starts in seconds and never depends on the database being reachable
COPY core ./core
COPY api ./api
COPY data/snapshot ./data/snapshot

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
