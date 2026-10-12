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
    extraction = Extraction(facts=[Fact(field="gender", value="male", quote="papa")])
    update, _ = facts_to_update(extraction, "papa kisan hain, main padh rahi hoon")
    assert update["gender"] == "male"  # model's answer kept
    update, _ = facts_to_update(Extraction(facts=[]), "main kisan hoon UP se")
    assert "gender" not in update  # "hoon" alone says nothing about gender


def test_invalid_value_is_dropped():
    extraction = Extraction(facts=[Fact(field="gender", value="robot", quote="31 year old")])
    update, rejected = facts_to_update(extraction, MESSAGE)
    assert update == {}
    assert rejected
