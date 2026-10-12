"""POST /api/results — "show me what I'm entitled to".

Stateless like /api/profile: the browser sends the finished profile, gets result cards back.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from core.profile import Country, Profile
from core.profile_agent import Language
from core.results import Results, find_results

router = APIRouter(prefix="/api", tags=["results"])


class ResultsRequest(BaseModel):
    country: Country
    profile: Profile
    language: Language = "english"


@router.post("/results", response_model=Results)
def results(request: ResultsRequest) -> Results:
    return find_results(request.profile, request.country, request.language)
