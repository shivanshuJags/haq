# Deploying Haq

Two pieces:

| Piece | Where | What it is |
|---|---|---|
| Backend (FastAPI) | **Nebius Serverless Endpoint** | The `Dockerfile` in the repo root. Contains the code + the catalog snapshot (`data/snapshot/`), so it never needs the database at runtime. |
| Frontend (React) | **Vercel** | The `web/` folder, a static site. Calls the backend via `VITE_API_URL`. |

## 0. Before you start

Refresh the catalog snapshot whenever the scheme data or rules change:

```bash
python -m db.snapshot
```

## 1. Build and push the backend image

The image has no secrets (keys are passed as environment variables), and the data inside is public
government information, so a public registry is fine. Docker Hub is the simplest from Windows:

```bash
docker build -t <your-dockerhub-user>/haq-api:latest .
docker login
docker push <your-dockerhub-user>/haq-api:latest
```

Test it locally first:

```bash
docker run -p 8000:8000 --env-file .env <your-dockerhub-user>/haq-api:latest
# then open http://localhost:8000/api/health
```

(Alternative: Nebius Container Registry, `cr.<region>.nebius.cloud/...` — needs the Nebius CLI
credential helper or a service-account token. See https://docs.nebius.com/container-registry/quickstart)

## 2. Create the Nebius Serverless Endpoint (web console)

Console → **AI Services → Endpoints → Create endpoint**:

- **Name:** `haq-api`
- **Image:** `docker.io/<your-dockerhub-user>/haq-api:latest`
- **Platform / preset:** a CPU platform, smallest preset (the API needs no GPU; ~1 GB RAM is plenty)
- **Container port:** `8000`
- **Environment variables:**
  - `NEBIUS_API_KEY` = your Token Factory key (prefer a secret if offered)
  - `NEBIUS_BASE_URL` = `https://api.tokenfactory.nebius.com/v1/`
  - `ALLOWED_ORIGINS` = your Vercel URL (add after step 3, e.g. `https://haq.vercel.app`)
- **Authentication:** **none / public**. The browser calls this API directly, so a token would be
  visible to everyone anyway.

Creation takes ~5 minutes. Copy the `https://...` URL from **Public endpoints**, then check:

```bash
curl https://<endpoint-url>/api/health
```

Docs: https://docs.nebius.com/serverless/endpoints/manage

## 3. Deploy the frontend on Vercel

1. Push the repo to GitHub.
2. vercel.com → **Add New → Project** → import the repo.
3. **Root directory:** `web`. Framework: Vite (auto-detected).
4. **Environment variable:** `VITE_API_URL` = the Nebius endpoint URL from step 2 (no trailing slash).
5. Deploy. Then put the Vercel URL into the endpoint's `ALLOWED_ORIGINS` and restart the endpoint.

## 4. Check the live app

Open the Vercel URL and run the three demo flows: India chat → results, UK chat → results,
Rejection Rescue with a sample letter.
