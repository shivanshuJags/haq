from core.profile_agent import detect_language


def test_hinglish_message():
    assert detect_language("Main Bihar se hoon, 20 saal ki hoon", "IN", None) == "hinglish"


def test_english_message_in_india():
    assert detect_language("I am a farmer from Uttar Pradesh", "IN", None) == "english"


def test_uk_is_always_english():
    assert detect_language("main kisan hoon", "UK", None) == "english"


def test_short_answer_keeps_conversation_language():
    # "58 saal, purush" has only one Hinglish word — not enough on its own
    assert detect_language("58 saal, purush", "IN", "hinglish") == "hinglish"
