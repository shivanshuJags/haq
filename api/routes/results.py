"""POST /api/results         — "show me what I'm entitled to" (all at once)
POST /api/results/stream  — same, but each result card is sent the moment it's ready

Stateless like /api/profile: the browser sends the finished profile, gets result cards back.
"""
import json
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.profile import Country, Profile
from core.profile_agent import Language
from core.results import Results, find_results, stream_results

router = APIRouter(prefix="/api", tags=["results"])


class ResultsRequest(BaseModel):
    country: Country
    profile: Profile
    language: Language = "english"


@router.post("/results", response_model=Results)
def results(request: ResultsRequest) -> Results:
    return find_results(request.profile, request.country, request.language)


@router.post("/results/stream")
def results_stream(request: ResultsRequest) -> StreamingResponse:
    """Newline-delimited JSON (NDJSON): one event object per line — start, card, card, ..., done."""

    def events() -> Iterator[str]:
        try:
            for event in stream_results(request.profile, request.country, request.language):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception:
            yield json.dumps({"type": "error"}) + "\n"

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},  # don't let proxies hold lines back
    )
