"""US-301: the rules engine. Compares a person's profile with a scheme's hard rules — in code, no AI.

Every rule gives one of three answers:
  "pass"     the person clearly meets it
  "fail"     the person clearly does NOT meet it  -> scheme is dropped
  "unknown"  we don't know enough (missing profile fact, or a fuzzy rule) -> Ultra decides later

The golden rule: only say "fail" when we are SURE. When in doubt, "unknown".
Telling an eligible person "you don't qualify" is the worst mistake Haq can make.
"""
from dataclasses import dataclass
from typing import Literal

from core.profile import Profile
from core.rules import EligibilityRules

Status = Literal["pass", "fail", "unknown"]


@dataclass
class Check:
    criterion: str  # e.g. "age_min"
    status: Status
    detail: str     # short English description, e.g. "age 20 ≥ 18"


@dataclass
class Assessment:
    checks: list[Check]

    @property
    def status(self) -> Status:
        statuses = {c.status for c in self.checks}
        if "fail" in statuses:
            return "fail"
        return "unknown" if "unknown" in statuses else "pass"

    @property
    def unknown_count(self) -> int:
        return sum(c.status == "unknown" for c in self.checks)


def _compare_number(name: str, value, limit, ok: bool, label: str) -> Check:
    if value is None:
        return Check(name, "unknown", f"{label} not known (limit {limit})")
    return Check(name, "pass" if ok else "fail", f"{label} {value} vs limit {limit}")


def _compare_flag(name: str, value: bool | None, required: bool, label: str) -> Check:
    if value is None:
        return Check(name, "unknown", f"{label}: not known")
    ok = value == required
    return Check(name, "pass" if ok else "fail", f"{label}: {'yes' if value else 'no'} (needs {'yes' if required else 'no'})")


def _occupation_of(profile: Profile) -> str | None:
    if profile.occupation:
        return profile.occupation
    return "student" if profile.is_student else None


def assess(rules: EligibilityRules, profile: Profile) -> Assessment:
    checks: list[Check] = []
    add = checks.append

    # --- Age
    if rules.age_min is not None:
        add(_compare_number("age_min", profile.age, rules.age_min,
                            profile.age is not None and profile.age >= rules.age_min, "age"))
    if rules.age_max is not None:
        add(_compare_number("age_max", profile.age, rules.age_max,
                            profile.age is not None and profile.age <= rules.age_max, "age"))

    # --- Gender
    if rules.genders:
        if profile.gender is None:
            add(Check("genders", "unknown", f"gender not known (for {', '.join(rules.genders)})"))
        else:
            ok = profile.gender in rules.genders
            add(Check("genders", "pass" if ok else "fail", f"gender {profile.gender} (for {', '.join(rules.genders)})"))

    # --- Social category
    if rules.caste_categories:
        allowed = set(rules.caste_categories)
        person = profile.caste_category
        if person is None:
            add(Check("caste_categories", "unknown", f"category not known (for {', '.join(sorted(allowed))})"))
        elif person in allowed:
            add(Check("caste_categories", "pass", f"category {person}"))
        elif person == "EBC" and "OBC" in allowed:
            # EBC castes are part of the backward-class lists in many states — let Ultra read the text
            add(Check("caste_categories", "unknown", "category EBC; scheme mentions OBC"))
        elif "Minority" in allowed:
            # We don't ask about religion; can't be sure either way
            add(Check("caste_categories", "unknown", "scheme is for minority communities"))
        else:
            add(Check("caste_categories", "fail", f"category {person} (for {', '.join(sorted(allowed))})"))

    # --- Marital status / residence
    if rules.marital_status:
        if profile.marital_status is None:
            add(Check("marital_status", "unknown", f"marital status not known (for {', '.join(rules.marital_status)})"))
        else:
            ok = profile.marital_status in rules.marital_status
            add(Check("marital_status", "pass" if ok else "fail", f"marital status {profile.marital_status}"))
    if rules.residence:
        if profile.residence is None:
            add(Check("residence", "unknown", f"rural/urban not known (for {rules.residence})"))
        else:
            ok = profile.residence == rules.residence
            add(Check("residence", "pass" if ok else "fail", f"lives in {profile.residence} area (for {rules.residence})"))

    # --- Money
    if rules.income_max is not None:
        family = profile.annual_family_income
        if family is not None:
            add(_compare_number("income_max", family, rules.income_max, family <= rules.income_max, "family income"))
        elif profile.personal_annual_income is not None and profile.personal_annual_income > rules.income_max:
            # family income is at least the person's own income
            add(Check("income_max", "fail", f"own income {profile.personal_annual_income} already above family limit {rules.income_max}"))
        else:
            add(Check("income_max", "unknown", f"family income not known (limit {rules.income_max})"))
    if rules.personal_income_max is not None:
        own = profile.personal_annual_income
        if own is not None:
            add(_compare_number("personal_income_max", own, rules.personal_income_max,
                                own <= rules.personal_income_max, "own income"))
        elif profile.annual_family_income is not None and profile.annual_family_income <= rules.personal_income_max:
            # own income can't be more than the whole family's
            add(Check("personal_income_max", "pass", f"family income {profile.annual_family_income} within personal limit"))
        else:
            add(Check("personal_income_max", "unknown", f"own income not known (limit {rules.personal_income_max})"))
    if rules.savings_max is not None:
        add(_compare_number("savings_max", profile.savings, rules.savings_max,
                            profile.savings is not None and profile.savings <= rules.savings_max, "savings"))
    if rules.bpl_required:
        add(_compare_flag("bpl_required", profile.has_bpl_card, True, "BPL card"))
    if rules.land_holding_max_acres is not None:
        add(_compare_number("land_holding_max_acres", profile.land_acres, rules.land_holding_max_acres,
                            profile.land_acres is not None and profile.land_acres <= rules.land_holding_max_acres,
                            "land (acres)"))

    # --- Work and study
    if rules.occupations:
        occupation = _occupation_of(profile)
        if occupation is None:
            add(Check("occupations", "unknown", f"occupation not known (for {', '.join(rules.occupations)})"))
        else:
            ok = occupation in rules.occupations
            add(Check("occupations", "pass" if ok else "fail", f"occupation {occupation} (for {', '.join(rules.occupations)})"))
    if rules.is_student is not None:
        is_student = profile.is_student
        if is_student is None and profile.occupation:
            is_student = profile.occupation == "student"
        add(_compare_flag("is_student", is_student, rules.is_student, "student"))
    if rules.education_levels:
        # Education levels are free text ("class 12", "graduate"...) — too fuzzy to fail on in code
        add(Check("education_levels", "unknown", f"needs education: {', '.join(rules.education_levels)}"))

    # --- Health and family
    if rules.disability_required is not None:
        add(_compare_flag("disability_required", profile.has_disability, rules.disability_required, "disability"))
    if rules.disability_min_percent is not None:
        percent = profile.disability_percent
        add(_compare_number("disability_min_percent", percent, rules.disability_min_percent,
                            percent is not None and percent >= rules.disability_min_percent, "disability %"))
    if rules.has_children is not None:
        add(_compare_flag("has_children", profile.has_children, rules.has_children, "has children"))
    if rules.is_pregnant is not None:
        add(_compare_flag("is_pregnant", profile.is_pregnant, rules.is_pregnant, "pregnant"))
    if rules.is_carer is not None:
        add(_compare_flag("is_carer", profile.is_carer, rules.is_carer, "carer"))
    if rules.receives_benefit:
        known = {b.lower() for b in profile.receives_benefits}
        if any(b.lower() in known for b in rules.receives_benefit):
            add(Check("receives_benefit", "pass", "already receives a required benefit"))
        else:
            add(Check("receives_benefit", "unknown", f"must already get: {', '.join(rules.receives_benefit)}"))

    return Assessment(checks)
