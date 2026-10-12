"""Haq API entry point.

Run locally from the project root:
    uvicorn api.main:app --reload

Then open http://localhost:8000/docs for interactive API docs.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import profile, results
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

# Allow the React dev server (Vite runs on port 5173) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(results.router)


@app.get("/api/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "schemes": len(catalog())}
