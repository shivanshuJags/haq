"""A message that tells us nothing must not move the chat on (and must not use up a round)."""
from fastapi.testclient import TestClient

import api.routes.profile as route
from api.main import app
from core.grounded import Extraction, Fact, facts_to_update
from core.profile import Profile

client = TestClient(app)


def turn(message, profile=None, answering=None, language="hinglish"):
    return client.post("/api/profile", json={
        "country": "IN", "message": message, "profile": profile or {"region": "Bihar"},
        "asked": answering or [], "answering": answering or [], "rounds": 1 if answering else 0, "language": language,
    }).json()


def test_gibberish_first_message_asks_again(monkeypatch):
    monkeypatch.setattr(route, "extract_profile", lambda message, known, *args: known)  # nothing learned
    reply = turn("sdfsdf")
    assert reply["retry"] is True and reply["ready"] is False
    assert "galti se type" in reply["follow_up"]["question"]
    assert reply["asking"] == []


def test_unclear_answer_repeats_the_same_question(monkeypatch):
    monkeypatch.setattr(route, "extract_profile", lambda message, known, *args: known)
    reply = turn("-20", answering=["age"], language="english")
    assert reply["retry"] is True
    assert reply["follow_up"]["question"].startswith("Sorry, I didn't understand that")
    assert "How old are you?" in reply["follow_up"]["question"]
    assert reply["asking"] == ["age"]


def test_dont_know_moves_on(monkeypatch):
    monkeypatch.setattr(route, "extract_profile", lambda message, known, *args: known)
    for message in ("skip", "pata nahi", "Don't know.", "पता नहीं"):
        assert turn(message, answering=["annual_family_income"])["retry"] is False


def test_impossible_numbers_are_rejected():
    message = "meri umar -20 hai, 500 saal"
    extraction = Extraction(facts=[Fact(field="age", value=-20, quote="-20"), Fact(field="age", value=500, quote="500 saal")])
    update, rejected = facts_to_update(extraction, message)
    assert "age" not in update and len(rejected) == 2
    assert Profile(age=35).age == 35
