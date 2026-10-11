"""POST /api/profile — one chat turn of the "tell us about yourself" conversation.

The server keeps NOTHING between requests (US-203): the browser sends the profile
it has so far with every message, and gets the updated profile back.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.privacy import redact
from core.profile import MAX_FOLLOW_UP_ROUNDS, Country, Profile, missing_fields
from core.profile_agent import FollowUp, Language, detect_language, extract_profile, follow_up_question

router = APIRouter(prefix="/api", tags=["profile"])

PRIVACY_NOTE = {
    "hinglish": "Aapka number hata diya gaya hai. Haq ko Aadhaar, PAN ya bank details ki zaroorat nahi hai.",
    "english": "We removed that number. Haq never needs ID numbers (Aadhaar, PAN, National Insurance) or bank details.",
}


class ProfileTurn(BaseModel):
    country: Country
    message: str = Field(min_length=1, max_length=2000)
    profile: Profile = Field(default_factory=Profile)
    asked: list[str] = Field(default_factory=list, description="All fields we've asked about so far")
    answering: list[str] = Field(default_factory=list, description="Fields the previous follow-up asked about")
    rounds: int = Field(0, ge=0, description="How many follow-up questions were asked so far")
    language: Language | None = Field(None, description="Conversation language from the previous reply")


class ProfileReply(BaseModel):
    profile: Profile
    follow_up: FollowUp | None = Field(description="Next question, or null when we have enough to search")
    asking: list[str] = Field(description="Fields the follow-up asks about — send back as `answering` and add to `asked`")
    ready: bool = Field(description="True when it's time to show results")
    language: Language = Field(description="Send back as `language` next turn")
    privacy_note: str | None = None


@router.post("/profile", response_model=ProfileReply)
def profile_turn(turn: ProfileTurn) -> ProfileReply:
    message, removed = redact(turn.message)
    language = detect_language(message, turn.country, turn.language)
    profile = extract_profile(message, turn.profile, turn.country, turn.answering)

    missing = missing_fields(profile, turn.country, turn.asked)
    follow_up, asking = None, []
    if missing and turn.rounds < MAX_FOLLOW_UP_ROUNDS:
        asking = missing[:2]  # at most two facts per question
        follow_up = follow_up_question(asking, message, language)

    return ProfileReply(
        profile=profile,
        follow_up=follow_up,
        asking=asking,
        ready=follow_up is None,
        language=language,
        privacy_note=PRIVACY_NOTE[language] if removed else None,
    )
