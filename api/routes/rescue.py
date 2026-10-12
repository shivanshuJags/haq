"""POST /api/rescue — US-501/502 Rejection Rescue.

Send either the letter's text or a photo of it (as a data URL). Nothing is stored.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from core.profile import Country
from core.profile_agent import Language
from core.rescue import RescueOutcome, rescue

router = APIRouter(prefix="/api", tags=["rescue"])

MAX_IMAGE_CHARS = 8_000_000  # ~6 MB image after base64


class RescueRequest(BaseModel):
    country: Country
    language: Language = "english"
    letter_text: str | None = Field(None, max_length=20_000)
    image: str | None = Field(None, max_length=MAX_IMAGE_CHARS, description="data:image/...;base64,...")

    @model_validator(mode="after")
    def text_or_image(self) -> "RescueRequest":
        if not (self.letter_text and self.letter_text.strip()) and not self.image:
            raise ValueError("Send letter_text or image")
        return self


@router.post("/rescue", response_model=RescueOutcome)
def rescue_letter(request: RescueRequest) -> RescueOutcome:
    try:
        return rescue(request.country, request.language, request.letter_text, request.image)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
