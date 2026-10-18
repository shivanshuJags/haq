"""GET /api/highlights — what the welcome screen shows for a country / Indian state (no AI)."""
from fastapi import APIRouter, Response

from core.highlights import Highlights, highlights
from core.profile import Country

router = APIRouter(prefix="/api", tags=["highlights"])


@router.get("/highlights", response_model=Highlights)
def get_highlights(response: Response, country: Country, region: str | None = None) -> Highlights:
    # Same answer until the next deploy: let browsers (and any CDN) reuse it for an hour, and keep
    # showing a saved copy for a day while fetching a fresh one in the background.
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    return highlights(country, region or None)
