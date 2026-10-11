"""The person's profile: what we know about them, in the same terms as the eligibility rules.

Field names line up with core/rules.py so the rules engine can compare them directly
(e.g. profile.age vs rules.age_min, profile.caste_category vs rules.caste_categories).
"""
from typing import Literal

from pydantic import BaseModel, Field

from core.rules import Caste, Gender, MaritalStatus, Occupation, Residence

Country = Literal["UK", "IN"]


class Profile(BaseModel):
    region: str | None = Field(None, description="Indian state, e.g. 'Bihar'; null for UK")
    age: int | None = None
    gender: Gender | None = None
    caste_category: Caste | None = Field(None, description="India only")
    marital_status: MaritalStatus | None = None
    residence: Residence | None = None

    annual_family_income: int | None = Field(None, description="Whole household, per year, local currency")
    personal_annual_income: int | None = Field(None, description="The person alone, per year, local currency")
    savings: int | None = Field(None, description="Savings and investments, local currency")
    has_bpl_card: bool | None = Field(None, description="India: holds a Below Poverty Line / Antyodaya card")
    land_acres: float | None = Field(None, description="Farm land owned, in acres")

    occupation: Occupation | None = None
    is_student: bool | None = None
    education_level: str | None = Field(None, description="e.g. 'class 10', 'class 12', 'graduate', 'postgraduate'")
    has_disability: bool | None = None
    disability_percent: int | None = None
    has_children: bool | None = None
    is_pregnant: bool | None = None
    is_carer: bool | None = None
    receives_benefits: list[str] = Field(default_factory=list, description="Schemes/benefits already received")

    needs: str | None = Field(None, description="Short English summary of what help they are looking for")

    def merged_with(self, update: "Profile") -> "Profile":
        """New facts override old ones; facts the update doesn't mention are kept."""
        data = self.model_dump()
        for name, value in update.model_dump().items():
            if value not in (None, []):
                data[name] = value
        return Profile(**data)


# The facts that matter most for eligibility, in the order we ask about them.
# One follow-up question may ask about up to two of these at once.
IMPORTANT_FIELDS: dict[str, list[str]] = {
    "IN": ["region", "age", "gender", "annual_family_income", "caste_category", "occupation"],
    "UK": ["age", "has_children", "personal_annual_income", "savings", "has_disability"],
}

MAX_FOLLOW_UP_ROUNDS = 3


def missing_fields(profile: Profile, country: Country, already_asked: list[str]) -> list[str]:
    """Important fields we still don't know and haven't asked about yet.
    A student's occupation is already known, so is_student counts as filling `occupation`."""
    missing = []
    for name in IMPORTANT_FIELDS[country]:
        if name in already_asked:
            continue  # asked before: the person skipped it or didn't know — don't nag
        if name == "occupation" and profile.is_student:
            continue
        if getattr(profile, name) is None:
            missing.append(name)
    return missing
