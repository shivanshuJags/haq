from core.profile import Profile, missing_fields


def test_merge_keeps_old_facts_and_adds_new_ones():
    known = Profile(region="Bihar", age=20)
    update = Profile(caste_category="OBC")
    merged = known.merged_with(update)
    assert merged.region == "Bihar"
    assert merged.age == 20
    assert merged.caste_category == "OBC"


def test_merge_new_fact_overrides_old():
    merged = Profile(age=20).merged_with(Profile(age=21))
    assert merged.age == 21


def test_missing_fields_in_priority_order():
    profile = Profile(region="Bihar", age=20)
    assert missing_fields(profile, "IN", already_asked=[]) == [
        "gender", "annual_family_income", "caste_category", "occupation",
    ]


def test_student_counts_as_known_occupation():
    profile = Profile(region="Bihar", age=20, gender="female", annual_family_income=150000,
                      caste_category="OBC", is_student=True)
    assert missing_fields(profile, "IN", already_asked=[]) == []


def test_farmer_is_asked_about_land():
    profile = Profile(region="Uttar Pradesh", age=58, gender="male", annual_family_income=80000,
                      caste_category="General", occupation="farmer")
    assert missing_fields(profile, "IN", already_asked=[]) == ["land_acres"]


def test_does_not_ask_twice():
    profile = Profile(region="Bihar")
    missing = missing_fields(profile, "IN", already_asked=["age", "gender"])
    assert "age" not in missing
    assert "gender" not in missing
