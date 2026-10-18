"""GET /api/highlights — what the welcome screen shows for a country / Indian state (no AI)."""
from fastapi import APIRouter

from core.highlights import Highlights, highlights
from core.profile import Country

router = APIRouter(prefix="/api", tags=["highlights"])


@router.get("/highlights", response_model=Highlights)
def get_highlights(country: Country, region: str | None = None) -> Highlights:
    return highlights(country, region)
