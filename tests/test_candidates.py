from core.candidates import is_for_this_person
from core.catalog import Scheme
from core.profile import Profile
from core.rules import EligibilityRules


def scheme(targets):
    return Scheme(id="in:x", country="IN", regions=None, name="X", summary=None, categories=[], sections={},
                  apply_url=None, source_url="https://example.org", source=None,
                  meta={"target_beneficiaries": targets}, rules=EligibilityRules())


def test_schemes_for_people_are_kept():
    student = Profile(occupation="student")
    assert is_for_this_person(scheme(["Individual"]), student)
    assert is_for_this_person(scheme(["Family", "Individual"]), student)
    assert is_for_this_person(scheme([]), student)  # unknown: keep, never wrongly exclude


def test_institution_only_schemes_are_dropped():
    assert not is_for_this_person(scheme(["State Government", "University / Institution"]), Profile(occupation="student"))


def test_business_schemes_only_for_business_owners():
    assert not is_for_this_person(scheme(["Business Entity"]), Profile(occupation="student"))
    assert is_for_this_person(scheme(["Business Entity"]), Profile(occupation="entrepreneur"))
