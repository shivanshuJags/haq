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


def test_a_real_sentence_is_not_called_a_typo(monkeypatch):
    monkeypatch.setattr(route, "extract_profile", lambda message, known, *args: known)
    reply = turn("mere ghar mein bahut pareshani chal rahi hai")
    assert reply["retry"] is True
    assert reply["follow_up"]["question"].startswith("Maaf kijiye")
    assert "galti se type" not in reply["follow_up"]["question"]


def test_unemployed_must_be_said():
    from core.grounded import Extraction, Fact, facts_to_update
    message = "I'm 31, a single mum of two, earning £900 a month"
    wrong = Extraction(facts=[Fact(field="occupation", value="unemployed", quote="earning £900 a month")])
    assert "occupation" not in facts_to_update(wrong, message)[0]
    said = Extraction(facts=[Fact(field="occupation", value="unemployed", quote="out of work")])
    assert facts_to_update(said, "I'm 40 and out of work")[0]["occupation"] == "unemployed"
