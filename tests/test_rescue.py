import pytest
from pydantic import ValidationError

from api.routes.rescue import RescueRequest
from core.rescue import transcribe


def test_request_needs_text_or_image():
    with pytest.raises(ValidationError):
        RescueRequest(country="IN")
    with pytest.raises(ValidationError):
        RescueRequest(country="IN", letter_text="   ")
    assert RescueRequest(country="UK", letter_text="Your claim was refused").letter_text


def test_transcribe_rejects_non_image_data():
    # Checked before any model call — no network needed
    with pytest.raises(ValueError):
        transcribe("data:application/pdf;base64,AAAA")
    with pytest.raises(ValueError):
        transcribe("https://example.com/letter.png")
