from core.grounded import Extraction, Fact, facts_to_update, is_grounded

MESSAGE = "I'm a 31 year old single mum of two, earning about 900 pounds a month. I have 500 pounds saved."


def test_quote_must_be_in_message():
    assert is_grounded("31 year old", MESSAGE)
    assert is_grounded("  900 Pounds a Month ", MESSAGE)  # case and spacing don't matter
    assert not is_grounded("lives in a rural area", MESSAGE)


def test_invented_fact_is_dropped():
    extraction = Extraction(facts=[
        Fact(field="age", value=31, quote="31 year old"),
        Fact(field="residence", value="rural", quote="rural area"),  # never said
    ])
    update, rejected = facts_to_update(extraction, MESSAGE)
    assert update == {"age": 31}
    assert len(rejected) == 1


def test_monthly_income_is_converted_in_code():
    extraction = Extraction(facts=[
        Fact(field="personal_annual_income", value=900, unit="per_month", quote="900 pounds a month"),
    ])
    update, _ = facts_to_update(extraction, MESSAGE)
    assert update["personal_annual_income"] == 10800


def test_lakh_and_bigha_conversion():
    message = "ghar ki income 1.5 lakh hai, 2 bigha zameen hai"
    extraction = Extraction(facts=[
        Fact(field="annual_family_income", value=1.5, unit="lakh_per_year", quote="1.5 lakh"),
        Fact(field="land_acres", value=2, unit="bigha", quote="2 bigha zameen"),
    ])
    update, _ = facts_to_update(extraction, message)
    assert update["annual_family_income"] == 150000
    assert update["land_acres"] == 1.2


def test_hazaar_and_zero_income():
    message = "income 80 hazaar saal ki, ilaaj ke liye paisa nahi hai"
    extraction = Extraction(facts=[
        Fact(field="annual_family_income", value=80, unit="thousand_per_year", quote="80 hazaar"),
        Fact(field="savings", value=0, quote="paisa nahi hai"),
    ])
    update, rejected = facts_to_update(extraction, message)
    assert update == {"annual_family_income": 80000}
    assert len(rejected) == 1 and rejected[0].startswith("savings=0")


def test_student_occupation_implies_is_student():
    message = "BA kar rahi hoon"
    extraction = Extraction(facts=[Fact(field="occupation", value="student", quote="BA kar rahi hoon")])
    update, _ = facts_to_update(extraction, message)
    assert update["is_student"] is True


def test_number_must_appear_in_quote():
    message = "BA second year mein padh rahi hoon, mum of two"
    extraction = Extraction(facts=[
        # "second" is in the message, but it doesn't say "2 lakh" — this must be rejected
        Fact(field="annual_family_income", value=2, unit="lakh_per_year", quote="second year"),
        Fact(field="children_count", value=2, quote="mum of two"),  # spelled numbers are fine
    ])
    update, rejected = facts_to_update(extraction, message)
    assert "annual_family_income" not in update
    assert update["children_count"] == 2
    assert "number not in quote" in rejected[0]


def test_grammar_fills_what_the_model_missed():
    update, _ = facts_to_update(Extraction(facts=[]), "Main 20 saal ki hoon, BA kar rahi hoon")
    assert update["gender"] == "female"
    assert update["occupation"] == "student"
    assert update["is_student"] is True


def test_grammar_never_overrides_the_model_or_guesses():
    # The model's answer (with words that prove it) wins over the grammar guess ("rahi" = female)
    extraction = Extraction(facts=[Fact(field="gender", value="male", quote="main ladka hoon")])
    update, _ = facts_to_update(extraction, "main ladka hoon, padh rahi hoon")
    assert update["gender"] == "male"
    # ...but "papa" proves nothing about the person — the grammar ("padh rahi hoon") decides
    extraction = Extraction(facts=[Fact(field="gender", value="male", quote="papa")])
    update, _ = facts_to_update(extraction, "papa kisan hain, main padh rahi hoon")
    assert update["gender"] == "female"
    update, _ = facts_to_update(Extraction(facts=[]), "main kisan hoon UP se")
    assert "gender" not in update  # "hoon" alone says nothing about gender


def test_invalid_value_is_dropped():
    extraction = Extraction(facts=[Fact(field="gender", value="robot", quote="31 year old")])
    update, rejected = facts_to_update(extraction, MESSAGE)
    assert "gender" not in update  # (the age safety net still reads "31 year old" from the message)
    assert rejected


def test_spoken_amounts_are_read_in_code():
    # Nano said 1 for "dedh lakh" and per-YEAR for "15 hazaar mahina" — code reads the words itself
    cases = [
        ("ghar ki income dedh lakh hai", 1, "lakh_per_year", "dedh lakh", 150_000),
        ("घर की सालाना आमदनी डेढ़ लाख है", 1.5, "lakh_per_year", "डेढ़ लाख", 150_000),
        ("kamai dhai lakh", 2.5, "lakh_per_year", "dhai lakh", 250_000),
        ("income saadhe 3 lakh", 3, "lakh_per_year", "saadhe 3 lakh", 350_000),
        ("papa 15 hazaar mahina kamate hain", 15, "thousand_per_year", "15 hazaar mahina", 180_000),
        ("papa 15 hazaar kamate hain har mahine", 15, "thousand_per_year", "15 hazaar", 180_000),
        ("উপার্জন মাসে ১২ হাজার", 12, "thousand_per_year", "মাসে 12 হাজার", 144_000),
        ("income 1,50,000 per year", 150000, "per_year", "1,50,000", 150_000),
        ("I earn £300 a week", 300, "per_week", "£300 a week", 15_600),
        ("income 80k", 80, "thousand_per_year", "80k", 80_000),
    ]
    for message, value, unit, quote, expected in cases:
        from core.languages import ascii_digits
        message = ascii_digits(message)
        extraction = Extraction(facts=[Fact(field="annual_family_income", value=value, unit=unit, quote=quote)])
        update, rejected = facts_to_update(extraction, message)
        assert update.get("annual_family_income") == expected, (message, update, rejected)


def test_period_after_the_quote_stops_at_a_comma():
    # "mahina" belongs to papa's income, not to the family's 2 lakh
    message = "ghar ki income 2 lakh, papa 15 hazaar mahina"
    extraction = Extraction(facts=[Fact(field="annual_family_income", value=2, unit="lakh_per_year", quote="income 2 lakh")])
    update, _ = facts_to_update(extraction, message)
    assert update["annual_family_income"] == 200_000


def test_savings_are_a_total():
    message = "bachat dedh lakh hai mahine ki kamai alag"
    extraction = Extraction(facts=[Fact(field="savings", value=1, unit="lakh_per_year", quote="dedh lakh")])
    update, _ = facts_to_update(extraction, message)
    assert update["savings"] == 150_000


def test_period_words_in_indian_languages_and_before_the_number():
    cases = [
        ("घरचे उत्पन्न महिन्याला 12 हजार आहे", "घरचे उत्पन्न महिन्याला 12 हजार", 144_000),  # Marathi
        ("mahine ke 15 hazaar milte hain", "15 hazaar", 180_000),  # period just before the quote
        ("papa 15 hazaar mahina, ghar ki income 2 lakh", "income 2 lakh", 200_000),  # not across a comma
    ]
    for message, quote, expected in cases:
        extraction = Extraction(facts=[Fact(field="annual_family_income", value=1, unit="thousand_per_year", quote=quote)])
        update, rejected = facts_to_update(extraction, message)
        assert update.get("annual_family_income") == expected, (message, update, rejected)


def test_misspelled_money_quote_is_repaired_from_the_real_words():
    message = "Mahine ke 15 hazaar kamata hoon, bachat dedh lakh hai."
    extraction = Extraction(facts=[
        Fact(field="savings", value=2.5, unit="lakh_per_year", quote="bachet dedh lakh"),  # typo + wrong value
        Fact(field="occupation", value="farmer", quote="not a farmer"),  # non-money: never trimmed
    ])
    update, rejected = facts_to_update(extraction, message)
    assert update["savings"] == 150_000
    assert "occupation" not in update


def test_grammar_with_a_word_in_between():
    from core.grounded import facts_from_grammar
    assert facts_from_grammar("Main 35 saal ka mazdoor hoon")["gender"] == "male"
    assert facts_from_grammar("20 saal ki student hoon")["gender"] == "female"
    assert facts_from_grammar("15 hazaar kamata hoon")["gender"] == "male"


def test_gender_and_education_need_words_that_say_so():
    from core.grounded import quote_shows
    # Nano's real mistake: "student hoon" proves neither gender nor education level
    message = "Main student hoon, ghar ki income 1 lakh"
    extraction = Extraction(facts=[
        Fact(field="gender", value="female", quote="student hoon"),
        Fact(field="education_level", value="graduate", quote="student hoon"),
        Fact(field="occupation", value="student", quote="student hoon"),
    ])
    update, rejected = facts_to_update(extraction, message)
    assert "gender" not in update and "education_level" not in update
    assert update["occupation"] == "student" and len(rejected) == 2
    for quote in ("20 saal ki hoon", "BA kar rahi hoon", "single mum", "Mahila", "female", "मैं 20 साल की हूँ",
                  "मी 45 वर्षांचा", "আমি ছাত্রী", "widow"):
        assert quote_shows("gender", quote), quote
    for quote in ("BA kar rahi hoon", "class 10 pass", "बीए", "graduate", "ITI", "12th"):
        assert quote_shows("education_level", quote), quote
    for quote in ("student hoon", "reject hua hai", "kisan hoon"):
        assert not quote_shows("gender", quote), quote
    assert not quote_shows("education_level", "I want to be a teacher")


def test_grammar_in_hindi_and_marathi_script():
    from core.grounded import facts_from_grammar
    assert facts_from_grammar("मैं 62 साल का किसान हूँ")["gender"] == "male"
    assert facts_from_grammar("मैं कॉलेज में पढ़ रही हूँ")["gender"] == "female"
    assert facts_from_grammar("मी 45 वर्षांचा शेतकरी आहे")["gender"] == "male"
    assert facts_from_grammar("मी 30 वर्षांची आहे")["gender"] == "female"
    assert "gender" not in facts_from_grammar("मैं किसान हूँ")


def test_age_and_widow_safety_net():
    from core.grounded import facts_from_grammar
    assert facts_from_grammar("Main 60 saal ki vidhwa hoon, BPL card hai") == {"gender": "female", "age": 60, "marital_status": "widowed"}
    assert facts_from_grammar("I'm 67 years old")["age"] == 67
    assert facts_from_grammar("मैं 62 साल का किसान हूँ")["age"] == 62
    assert facts_from_grammar("मी 45 वर्षांचा शेतकरी आहे")["age"] == 45
    assert facts_from_grammar("আমি 20 বছরের ছাত্রী")["age"] == 20
    assert "age" not in facts_from_grammar("10 saal se kheti kar raha hoon")  # years of farming, not age
    assert "age" not in facts_from_grammar("main 20 saal ki hoon, papa 50 saal ke hain")  # two ages: unclear
    assert "gender" not in facts_from_grammar("I'm widowed")  # could be anyone


def test_a_minus_sign_is_not_the_number():
    from core.grounded import number_in_quote
    assert not number_in_quote(20, "-20")
    assert not number_in_quote(20, "umar -20")
    assert number_in_quote(20, "18-20 saal")  # a range still shows 20
    assert number_in_quote(20, "20 saal")
