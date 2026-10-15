# Deploying Haq

Two pieces, both on free plans:

| Piece | Where | What it is |
|---|---|---|
| Backend (FastAPI) | **Render** — free web service, Docker | The repo's `Dockerfile`: code + catalog snapshot (`data/snapshot/`). Never needs the database at runtime. |
| Frontend (React) | **Vercel** — free | The `web/` folder, a static site. Calls the backend via `VITE_API_URL`. |

All AI runs on **NVIDIA Nemotron via Nebius Token Factory** — the hosting choice doesn't change that.

Tested with Render's free limits (`docker run --memory=512m --cpus=0.1`): starts in ~30s,
peak memory ~125 MB of 512 MB, chat / results / Rejection Rescue all work.

## 0. Before deploying

Refresh the snapshot if scheme data or rules changed, and commit it:

```bash
python -m db.snapshot
```

Push everything to GitHub (`data/snapshot/` must be in the repo — Render builds from it).

## 1. Backend → Render

1. Sign up at render.com with your GitHub account (the free plan needs no card).
2. **New + → Web Service** → connect your GitHub repo.
3. Settings:
   - **Name:** `haq-api`
   - **Language / Runtime:** **Docker** (Render finds the `Dockerfile` in the repo root)
   - **Branch:** `main`, **Root directory:** empty
   - **Instance type:** **Free**
4. **Environment variables:**
   - `NEBIUS_API_KEY` = your Token Factory key
   - `NEBIUS_BASE_URL` = `https://api.tokenfactory.nebius.com/v1/`
   - `ALLOWED_ORIGINS` = your Vercel URL (add after step 2, e.g. `https://haq.vercel.app`)
5. **Advanced → Health check path:** `/api/health`
6. **Create Web Service.** The first build takes ~5 minutes (see Logs). Render sets `PORT` itself;
   the Dockerfile already listens on it.
7. Check: `https://haq-api.onrender.com/api/health` → `{"status":"ok","schemes":976}`

Render redeploys automatically on every push to `main`.

**Free plan behaviour:** the service sleeps after 15 minutes without traffic and takes about a minute
to wake (Render shows a loading page). Open the URL once before a demo or judging.

## 2. Frontend → Vercel

1. vercel.com → sign in with GitHub → **Add New → Project** → import the repo.
2. **Root directory:** `web`. Framework: Vite (auto-detected).
3. **Environment variable:** `VITE_API_URL` = `https://haq-api.onrender.com` (your Render URL, no trailing slash).
4. Deploy. Copy the Vercel URL into Render's `ALLOWED_ORIGINS` (Render restarts the service).

## 3. Check the live app

Open the Vercel URL and run: India chat → results, UK chat → results, Rejection Rescue with a sample letter.
A CORS error in the browser console means `ALLOWED_ORIGINS` doesn't exactly match the Vercel URL.

---

## Other hosts

- **Nebius Serverless Endpoint** (AI Cloud credits, billed per second): push the image to a registry,
  then Console → AI Services → Endpoints → Create endpoint, container port `8000`, smallest CPU preset,
  same env vars, authentication none. Docs: https://docs.nebius.com/serverless/endpoints/manage
- **Hugging Face Spaces:** Docker Spaces now need a paid PRO plan.
