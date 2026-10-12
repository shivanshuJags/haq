from core.eligibility import assess
from core.profile import Profile
from core.rules import EligibilityRules

PRIYA = Profile(region="Bihar", age=20, gender="female", caste_category="OBC",
                annual_family_income=150000, occupation="student", is_student=True)


def test_priya_passes_bihar_post_matric_scholarship():
    rules = EligibilityRules(caste_categories=["EBC", "OBC"], income_max=300000, is_student=True)
    assert assess(rules, PRIYA).status == "pass"


def test_income_above_limit_fails():
    rules = EligibilityRules(income_max=100000)
    assert assess(rules, PRIYA).status == "fail"


def test_unknown_fact_is_unknown_not_fail():
    # We don't know Priya's savings — never reject for a missing fact
    rules = EligibilityRules(savings_max=16000)
    result = assess(rules, PRIYA)
    assert result.status == "unknown"
    assert result.unknown_count == 1


def test_wrong_gender_fails():
    rules = EligibilityRules(genders=["male"])
    assert assess(rules, PRIYA).status == "fail"


def test_ebc_person_with_obc_scheme_is_unknown_not_fail():
    person = PRIYA.model_copy(update={"caste_category": "EBC"})
    rules = EligibilityRules(caste_categories=["OBC"])
    assert assess(rules, person).status == "unknown"


def test_own_income_above_family_limit_fails_even_without_family_income():
    person = Profile(personal_annual_income=500000)
    rules = EligibilityRules(income_max=300000)
    assert assess(rules, person).status == "fail"


def test_family_income_within_personal_limit_passes():
    person = Profile(annual_family_income=10000)
    rules = EligibilityRules(personal_income_max=10608)
    assert assess(rules, person).status == "pass"


def test_student_inferred_from_occupation():
    person = Profile(occupation="farmer")
    rules = EligibilityRules(is_student=True)
    assert assess(rules, person).status == "fail"


def test_education_level_is_left_to_ultra():
    rules = EligibilityRules(education_levels=["graduate"])
    assert assess(rules, PRIYA).status == "unknown"


def test_no_rules_means_pass():
    assert assess(EligibilityRules(), PRIYA).status == "pass"
