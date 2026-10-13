"""Fast, grounded profile extraction: every fact must come with the exact words that prove it.

Why: with thinking switched off, Nano answers ~6x faster but sometimes INVENTS facts
("rural", "class 12", "is a carer") or gets arithmetic wrong (£900/month -> £108,000/year).
Wrong facts can wrongly exclude people from benefits. So:

  1. The model returns each fact with a `quote` copied from the person's message.
     Code checks the quote really is in the message — if not, the fact is dropped.
  2. The model never does arithmetic. It returns the number as said plus a unit
     ("900", "per_month"; "2", "bigha"); code converts to yearly amounts / acres.
"""
import re
from typing import Literal, get_args

from pydantic import BaseModel, Field, ValidationError

from core.profile import Profile

Unit = Literal["per_year", "per_month", "per_week", "lakh_per_year", "thousand_per_year",
               "acre", "bigha", "hectare", "none"]


class Fact(BaseModel):
    field: str = Field(description="One of the profile field names")
    value: str | int | float | bool
    unit: Unit = Field("none", description="For money and land only; otherwise 'none'")
    quote: str = Field(description="The exact words from the message that state this fact")


class Extraction(BaseModel):
    facts: list[Fact]
    needs: str | None = Field(None, description="Short English sentence: what help they want")


MONEY_FIELDS = {"annual_family_income", "personal_annual_income", "savings"}
PER_YEAR = {"per_year": 1, "per_month": 12, "per_week": 52, "lakh_per_year": 100_000,
            "thousand_per_year": 1_000, "none": 1}
ACRES_PER = {"acre": 1.0, "bigha": 0.6, "hectare": 2.47, "none": 1.0}  # bigha ≈ 0.6 acre in UP/Bihar


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip(" .,!?\"'")


def is_grounded(quote: str, message: str) -> bool:
    """The quote must be a real piece of what the person said (or of our last question's context)."""
    quote = _normalise(quote)
    return len(quote) >= 2 and quote in _normalise(message)


NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhe": 6, "saat": 7, "aath": 8,
}


def number_in_quote(value, quote: str) -> bool:
    """A number fact must show that number in its quote ("1.5 lakh" for 1.5, "two" for 2).
    Stops quotes like "second year" being used to justify an income of 2 lakh."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return True
    text = quote.lower().replace(",", "")
    as_text = f"{value:g}"  # 1.5 -> "1.5", 80.0 -> "80"
    if re.search(rf"(?<![\d.]){re.escape(as_text)}(?![\d])", text):
        return True
    return any(NUMBER_WORDS.get(word) == value for word in re.findall(r"[a-z]+", text))


def _match_choice(field: str, value):
    """Fix the case of choice values ("general" -> "General", "Female" -> "female"),
    so a correct answer isn't rejected just for its capitalisation."""
    if not isinstance(value, str):
        return value
    annotation = Profile.model_fields[field].annotation
    for allowed in get_args(get_args(annotation)[0]) if get_args(annotation) else ():
        if isinstance(allowed, str) and allowed.lower() == value.strip().lower():
            return allowed
    return value


def convert(fact: Fact):
    """Do the arithmetic in code, never in the model."""
    if fact.field in MONEY_FIELDS:
        amount = float(str(fact.value).replace(",", ""))
        if fact.field == "savings":
            # savings are a total, not per year — only the "lakh"/"thousand" scale applies
            multiplier = {"lakh_per_year": 100_000, "thousand_per_year": 1_000}.get(fact.unit, 1)
        else:
            multiplier = PER_YEAR.get(fact.unit, 1)
        return int(round(amount * multiplier))
    if fact.field == "land_acres":
        return round(float(fact.value) * ACRES_PER.get(fact.unit, 1.0), 2)
    return _match_choice(fact.field, fact.value)


# Safety net for facts the fast model sometimes misses, but which certain Hindi phrasings
# state unambiguously. Only used when the model didn't give the field itself.
FEMALE_GRAMMAR = re.compile(r"\b(saal|varsh|sal) ki (hoon|hu|hun)\b|\b(rahi|karti|padhti|chuki) (hoon|hu|hun)\b")
MALE_GRAMMAR = re.compile(r"\b(saal|varsh|sal) ka (hoon|hu|hun)\b|\b(raha|karta|padhta|chuka) (hoon|hu|hun)\b")
STUDYING = re.compile(
    r"\b(ba|bsc|b\.?sc|bcom|b\.?com|ma|msc|mcom|btech|b\.?tech|mbbs|iti|polytechnic|diploma|class \d+|\d+(th|vi|vee) class)\b"
    r".{0,25}\b(kar|padh)\s*(rahi|raha)\b"
    r"|\b(padh|padhai kar)\s*(rahi|raha)\b"
    r"|\b(i am|i'm) (a )?(student|studying)\b"
)


# "general category", "OBC caste", "category: SC", "hum OBC hain" — the category word must sit next to
# "category"/"caste"/"varg"/"hum ... hain", so "st" or "sc" elsewhere in a sentence isn't misread.
CATEGORY_NAMES = {"general": "General", "obc": "OBC", "ebc": "EBC", "sc": "SC", "st": "ST"}
_CAT = r"(general|obc|ebc|sc|st)"
CATEGORY_PHRASE = re.compile(
    rf"\b{_CAT}\s+(category|caste|varg|jaati|jati)\b"
    rf"|\b(category|caste|varg|jaati|jati)\s*(?:is|hai|:|-)?\s*{_CAT}\b"
    rf"|\bhum\s+{_CAT}\s+(hain|hai|hu|hoon)\b"
)


def facts_from_grammar(message: str) -> dict:
    text = message.lower()
    found: dict = {}
    category = CATEGORY_PHRASE.search(text)
    if category:
        word = next(group for group in category.groups() if group in CATEGORY_NAMES)
        found["caste_category"] = CATEGORY_NAMES[word]
    female, male = bool(FEMALE_GRAMMAR.search(text)), bool(MALE_GRAMMAR.search(text))
    if female != male:  # only when the grammar points one way
        found["gender"] = "female" if female else "male"
    if STUDYING.search(text):
        found["occupation"] = "student"
        found["is_student"] = True
    return found


def facts_to_update(extraction: Extraction, message: str) -> tuple[dict, list[str]]:
    """Return (profile fields to update, descriptions of facts we rejected)."""
    update: dict = {}
    rejected: list[str] = []
    for fact in extraction.facts:
        if fact.field not in Profile.model_fields or fact.field == "needs":
            continue
        if not is_grounded(fact.quote, message):
            rejected.append(f"{fact.field}={fact.value!r} (quote not in message: {fact.quote!r})")
            continue
        if not number_in_quote(fact.value, fact.quote):
            rejected.append(f"{fact.field}={fact.value!r} (number not in quote: {fact.quote!r})")
            continue
        try:
            value = convert(fact)
            if fact.field == "receives_benefits" and not isinstance(value, list):
                value = [str(value)]
            if fact.field in MONEY_FIELDS and value == 0:
                # "paisa nahi hai" (no money for treatment) isn't "income is zero" — too risky to keep
                rejected.append(f"{fact.field}=0 (ambiguous zero)")
                continue
            Profile.model_validate({fact.field: value})
            update[fact.field] = value
        except (ValueError, ValidationError):
            rejected.append(f"{fact.field}={fact.value!r} (invalid value)")

    # Unambiguous grammar facts the model missed
    for name, value in facts_from_grammar(message).items():
        update.setdefault(name, value)

    # Facts that follow from other facts — derived in code so the model can't forget them
    if update.get("occupation") == "student":
        update.setdefault("is_student", True)

    if extraction.needs:
        update["needs"] = extraction.needs
    return update, rejected
