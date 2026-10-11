"""The eligibility rule schema: the structured version of a scheme's eligibility text.

Golden rule for every field: `None` means "this scheme does not restrict on this".
A value means "the applicant MUST match this" (for booleans: True = must be, False = must not be).
Fields are hard filters, so they only hold conditions every applicant must meet; when a limit
differs by group, the field holds the loosest value. So code can check rules like:

    if rules.age_min is not None and profile.age < rules.age_min: -> not eligible

Anything that can't be expressed in these fields goes into `other_conditions`
as plain text, so nothing from the official text is lost or invented.
"""
from typing import Literal

from pydantic import BaseModel, Field

Gender = Literal["male", "female", "transgender"]
Caste = Literal["SC", "ST", "OBC", "EBC", "General", "PVTG", "DNT", "Minority"]
Residence = Literal["rural", "urban"]
MaritalStatus = Literal["married", "unmarried", "widowed", "divorced", "separated"]
Occupation = Literal[
    "student", "farmer", "agricultural_labourer", "fisherman", "artisan_weaver",
    "construction_worker", "street_vendor", "unorganised_worker", "self_employed",
    "salaried_employee", "unemployed", "ex_serviceman", "sportsperson", "artist",
    "teacher", "researcher", "entrepreneur", "carer", "retired",
]
Confidence = Literal["high", "medium", "low"]


class EligibilityRules(BaseModel):
    # Who
    age_min: int | None = Field(None, description="Minimum age in years")
    age_max: int | None = Field(None, description="Maximum age in years")
    genders: list[Gender] | None = Field(None, description="Only these genders may apply")
    caste_categories: list[Caste] | None = Field(None, description="Only these social categories may apply")
    marital_status: list[MaritalStatus] | None = None
    residence: Residence | None = Field(None, description="Only rural or only urban residents")

    # Money (amounts in the scheme's local currency: INR for India, GBP for UK)
    income_max: int | None = Field(None, description="Maximum annual FAMILY income")
    personal_income_max: int | None = Field(None, description="Maximum annual income of the applicant alone")
    savings_max: int | None = Field(None, description="Maximum savings / capital (common in UK benefits)")
    bpl_required: bool | None = Field(None, description="Must hold a Below Poverty Line card")

    # Situation
    occupations: list[Occupation] | None = Field(None, description="Applicant must have one of these occupations")
    is_student: bool | None = Field(None, description="True = must be a student, False = must not be")
    education_levels: list[str] | None = Field(None, description="e.g. 'class 10', 'class 12', 'graduate', 'postgraduate', 'ITI', 'PhD'")
    disability_required: bool | None = None
    disability_min_percent: int | None = None
    has_children: bool | None = Field(None, description="True = must have/expect a child")
    is_pregnant: bool | None = None
    is_carer: bool | None = Field(None, description="True = must care for someone")
    receives_benefit: list[str] | None = Field(None, description="Must already receive one of these benefits/schemes")
    land_holding_max_acres: float | None = None

    # Everything else, kept as plain text — never dropped, never guessed
    other_conditions: list[str] = Field(default_factory=list)
    confidence: Confidence = Field("medium", description="How clearly the text states the rules")


def sanitize(rules: EligibilityRules) -> EligibilityRules:
    """Remove restrictions that look like rules but don't actually exclude anyone in practice,
    or that would wrongly exclude people. Applied after every extraction."""
    # "men/women" is not a gender restriction — listing both would wrongly exclude transgender people
    if rules.genders and {"male", "female"} <= set(rules.genders):
        rules.genders = None
    # "60 to 150 years" — an upper age of 100+ is just a placeholder, not a real limit
    if rules.age_max is not None and rules.age_max >= 100:
        rules.age_max = None
    # Empty lists mean "no restriction", same as None
    for name in ("genders", "caste_categories", "marital_status", "occupations",
                 "education_levels", "receives_benefit"):
        if getattr(rules, name) == []:
            setattr(rules, name, None)
    return rules


def schema_for_prompt() -> str:
    """A compact description of the fields, to put in the LLM prompt."""
    lines = []
    for name, field in EligibilityRules.model_fields.items():
        type_name = str(field.annotation).replace("typing.", "").replace("NoneType", "null")
        hint = f" — {field.description}" if field.description else ""
        lines.append(f'  "{name}": {type_name}{hint}')
    return "{\n" + ",\n".join(lines) + "\n}"
