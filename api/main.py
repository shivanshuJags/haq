"""Haq API entry point.

Run locally from the project root:
    uvicorn api.main:app --reload

Then open http://localhost:8000/docs for interactive API docs.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import profile, rescue, results
from core.catalog import catalog


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts: load all schemes into memory now,
    # so the first user doesn't wait for it.
    catalog()
    yield


app = FastAPI(
    title="Haq API",
    description="Find the government benefits you're entitled to. Powered by NVIDIA Nemotron on Nebius Token Factory.",
    version="0.1.0",
    lifespan=lifespan,
)

def parse_origins(raw: str) -> list[str]:
    """ALLOWED_ORIGINS="https://haq.vercel.app, https://other.app" -> clean list.
    Browsers send the origin with no trailing slash and compare it exactly, so tidy up
    the usual copy-paste slips: spaces, quotes, a trailing "/"."""
    origins = []
    for item in raw.split(","):
        origin = item.strip().strip("'\"").strip().rstrip("/")
        if origin:
            origins.append(origin)
    return origins


# Local dev origins (Vite on port 5173) + the deployed frontend URL(s) from the environment
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"] + parse_origins(
    os.environ.get("ALLOWED_ORIGINS", "")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(results.router)
app.include_router(rescue.router)


@app.get("/api/health", tags=["system"])
def health() -> dict:
    # Allowed origins are public URLs, not secrets — showing them makes CORS problems easy to diagnose
    return {"status": "ok", "schemes": len(catalog()), "allowed_origins": ALLOWED_ORIGINS}
