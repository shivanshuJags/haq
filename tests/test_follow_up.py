from core.grounded import Extraction, Fact, facts_from_grammar, facts_to_update
from core.profile import Profile
from core.profile_agent import OPTION_VALUES, QUESTIONS, extract_profile, follow_up_question


def test_choice_question_has_its_options():
    question = follow_up_question(["gender"], "hinglish")
    assert question.question == "Aap purush hain ya mahila?"
    assert question.options == ["Purush", "Mahila", "Transgender"]


def test_two_facts_are_combined_without_options():
    question = follow_up_question(["age", "annual_family_income"], "english")
    assert "How old are you?" in question.question
    assert "household" in question.question
    assert question.options == []


def test_income_never_offers_ranges():
    for language in QUESTIONS:
        assert QUESTIONS[language]["annual_family_income"][1] == []


def test_every_question_exists_in_every_language():
    from core.languages import INSTRUCTIONS
    assert set(QUESTIONS) == set(INSTRUCTIONS)  # a language needs templates AND a model instruction
    for language in QUESTIONS:
        assert QUESTIONS[language].keys() == QUESTIONS["english"].keys(), language


def test_indian_language_buttons_are_understood():
    assert extract_profile("महिला", Profile(), "IN", answering=["gender"]).gender == "female"
    assert extract_profile("शेतकरी", Profile(), "IN", answering=["occupation"]).occupation == "farmer"
    assert extract_profile("হ্যাঁ", Profile(), "IN", answering=["has_children"]).has_children is True


def test_indian_digits_become_ascii():
    from core.languages import ascii_digits
    assert ascii_digits("मेरी उम्र २० साल, आय ১.৫ লাখ") == "मेरी उम्र 20 साल, आय 1.5 লাখ"


def test_every_button_has_a_meaning():
    # If a button's meaning were missing, tapping it would fall through to the model
    for language in QUESTIONS:
        for field, (_, options) in QUESTIONS[language].items():
            for option in options:
                assert option.lower() in OPTION_VALUES[field], f"{language}/{field}: {option}"


def test_tapped_button_is_understood_without_the_model():
    # No network call happens here: the button is mapped in code
    profile = extract_profile("Purush", Profile(age=58), "IN", answering=["gender"])
    assert profile.gender == "male"
    assert profile.age == 58
    profile = extract_profile("Haan", Profile(), "IN", answering=["has_children"])
    assert profile.has_children is True


def test_category_phrases():
    assert facts_from_grammar("80 hazaar saal ki, general category")["caste_category"] == "General"
    assert facts_from_grammar("hum OBC hain")["caste_category"] == "OBC"
    assert facts_from_grammar("caste: SC")["caste_category"] == "SC"
    assert "caste_category" not in facts_from_grammar("I live on Main St and go to sc hool")


def test_choice_case_is_fixed():
    # "general category" -> the model may say "general"; the allowed value is "General"
    message = "80 hazaar saal ki, general category"
    extraction = Extraction(facts=[Fact(field="caste_category", value="general", quote="general category")])
    update, rejected = facts_to_update(extraction, message)
    assert update["caste_category"] == "General"
    assert rejected == []
