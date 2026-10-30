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
import unicodedata
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
    # "-20" doesn't say 20 (a range like "18-20" does: there the dash follows a digit)
    if value > 0 and re.search(rf"(?<![\d\s])\s*[-−–]\s*{re.escape(as_text)}(?![\d])|^\s*[-−–]\s*{re.escape(as_text)}", text):
        return False
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


# --- Money read straight from the person's words -------------------------------------------------
# Nano gets spoken amounts wrong: "dedh lakh" -> 1 (should be 1.5), "15 hazaar mahina" -> 15,000 a
# YEAR (should be 1.8 lakh). So when the quote itself states the amount, code reads number, scale and
# period from it. Words in Latin, Devanagari (Hindi/Marathi) and Bengali script.
def _table(groups: dict) -> dict[str, float]:
    """{value: "word word ..."} -> {word: value}, in the same Unicode form as _tokens() produces."""
    return {unicodedata.normalize("NFC", word): value for value, words in groups.items() for word in words.split()}


CARDINALS = _table({
    1: "one ek एक এক", 2: "two do दो दोन দুই", 3: "three teen तीन তিন", 4: "four char chaar चार চার",
    5: "five paanch panch पाँच पांच पाच পাঁচ", 6: "six chhe chhah छह छः सहा ছয়", 7: "seven saat सात সাত",
    8: "eight aath आठ আট", 9: "nine nau नौ नऊ নয়", 10: "ten das दस दहा দশ",
})
HALVES = _table({1.5: "dedh dhedh डेढ़ डेढ दीड দেড়", 2.5: "dhai dhaai ढाई अडीच আড়াই"})
# "sava 2" = 2.25, "saadhe 3" = 3.5, "paune 2" = 1.75
MODIFIERS = _table({0.25: "sava savaa सवा সওয়া", 0.5: "saadhe sadhe saade साढ़े साढे साडे সাড়ে",
                    -0.25: "paune पौने পৌনে"})
SCALES = _table({
    100_000: "lakh lac lakhs lacs लाख লাখ", 1_000: "hazaar hazar hajar thousand k हज़ार हजार হাজার",
    10_000_000: "crore karod करोड़ करोड কোটি",
})
PERIODS = _table({
    12: "month monthly mahina mahine mahinay maah pm महीना महीने माह मासिक प्रतिमाह महिना महिने महिन्याला दरमहा "
        "মাস মাসে মাসিক",
    52: "week weekly hafta hafte हफ्ता हफ़्ता हफ्ते सप्ताह आठवडा आठवड्याला সপ্তাহ সপ্তাহে",
})
_TOKEN = re.compile(r"[^\s,.!?।()/:;\"']+")
_DIGITS = re.compile(r"[₹£$]?(\d+(?:\.\d+)?)(k)?")


def _tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"(?<=\d),(?=\d)", "", text)  # 1,50,000 -> 150000 (before commas split tokens)
    return _TOKEN.findall(text)


def spoken_amount(quote: str) -> float | None:
    """The amount a short quote states, before any per-month/per-week maths: "1.5 lakh" -> 150000,
    "डेढ़ लाख" -> 150000, "15 hazaar" -> 15000, "saadhe 3 lakh" -> 350000. None if unclear."""
    tokens = _tokens(quote)
    numbers: list[tuple[int, float]] = []  # (token index, number)
    i = 0
    while i < len(tokens):
        token = tokens[i]
        digits = _DIGITS.fullmatch(token)
        if digits:
            numbers.append((i, float(digits.group(1)) * (1000 if digits.group(2) else 1)))
        elif token in HALVES:
            numbers.append((i, HALVES[token]))
        elif token in MODIFIERS and i + 1 < len(tokens):
            nxt = _DIGITS.fullmatch(tokens[i + 1])
            base = float(nxt.group(1)) if nxt else CARDINALS.get(tokens[i + 1])
            if base is not None:
                numbers.append((i + 1, base + MODIFIERS[token]))
                i += 1
        elif token in CARDINALS:
            numbers.append((i, CARDINALS[token]))
        i += 1
    if len(numbers) != 1:
        return None  # nothing, or several numbers ("20 saal ... 2 lakh") — let the model's value decide
    index, number = numbers[0]
    following = tokens[index + 1:index + 3]
    scale = next((SCALES[word] for word in following if word in SCALES), 1)
    return number * scale


def spoken_period(text: str) -> int | None:
    """12 for monthly, 52 for weekly, None if the words don't say."""
    return next((PERIODS[token] for token in _tokens(text) if token in PERIODS), None)


def repair_money_quote(fact: Fact, message: str) -> Fact | None:
    """Nano sometimes misspells the start of a quote ("bachet dedh lakh" for "bachat dedh lakh").
    For money only, keep the longest ending of the quote that IS in the message and still states the
    amount — code reads the amount from those words, so nothing is guessed."""
    words = fact.quote.split()
    for start in range(1, len(words)):
        tail = " ".join(words[start:])
        if is_grounded(tail, message) and spoken_amount(tail) is not None:
            return fact.model_copy(update={"quote": tail})
    return None


def money_from_words(fact: Fact, message: str) -> int | None:
    """Yearly amount (or savings total) computed from the person's own words, or None."""
    amount = spoken_amount(fact.quote)
    if amount is None:
        return None
    if fact.field == "savings":
        return int(round(amount))  # a total, not per year
    # The period may sit just outside the quote ("mahine ke | 15 hazaar", "15 hazaar | har mahine"):
    # look a few words either side, but never past a comma or full stop (that's another fact)
    text, quote = _normalise(message), _normalise(fact.quote)
    start = text.find(quote)
    before = re.split(r"[,.।]", text[max(0, start - 20):start])[-1] if start > 0 else ""
    after = re.split(r"[,.।]", text[start + len(quote):][:25])[0] if start >= 0 else ""
    period = spoken_period(f"{before} {fact.quote} {after}")
    if period is None:
        period = {"per_month": 12, "per_week": 52}.get(fact.unit, 1)
    return int(round(amount * period))


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
# "20 saal ki hoon", "35 saal ka mazdoor hoon" (one word may sit in between), "kamati hoon"
FEMALE_GRAMMAR = re.compile(r"\b(saal|varsh|sal) ki (\w+ )?(hoon|hu|hun)\b|\b(rahi|karti|padhti|chuki|kamati) (hoon|hu|hun)\b")
MALE_GRAMMAR = re.compile(r"\b(saal|varsh|sal) ka (\w+ )?(hoon|hu|hun)\b|\b(raha|karta|padhta|chuka|kamata) (hoon|hu|hun)\b")
# The same in Hindi script ("62 साल का किसान हूँ", "पढ़ रही हूँ") and Marathi ("४५ वर्षांचा" / "वर्षांची").
# Indian scripts: no \b (marks like ा ी aren't "word" characters), so words are matched by spaces.
_HOON = "(हूँ|हूं|हू)"
SCRIPT_FEMALE = re.compile(unicodedata.normalize("NFC", rf"(साल|वर्ष) की (\S+ )?{_HOON}|(रही|करती|पढ़ती|कमाती|चुकी) {_HOON}|वर्षांची"))
SCRIPT_MALE = re.compile(unicodedata.normalize("NFC", rf"(साल|वर्ष) का (\S+ )?{_HOON}|(रहा|करता|पढ़ता|कमाता|चुका) {_HOON}|वर्षांचा"))
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
    script = unicodedata.normalize("NFC", text)
    female = bool(FEMALE_GRAMMAR.search(text) or SCRIPT_FEMALE.search(script))
    male = bool(MALE_GRAMMAR.search(text) or SCRIPT_MALE.search(script))
    if female != male:  # only when the grammar points one way
        found["gender"] = "female" if female else "male"
    if STUDYING.search(text):
        found["occupation"] = "student"
        found["is_student"] = True
    # Nano sometimes returns nothing at all for a clear message ("Main 60 saal ki vidhwa hoon")
    ages = stated_ages(script)
    if len(ages) == 1:  # only when one age is stated ("20 saal ki, papa 50 saal ke" is ambiguous)
        found["age"] = ages.pop()
    if WIDOWED.search(script):
        found["marital_status"] = "widowed"
    if WIDOW_FEMALE.search(script):  # "widow"/"vidhwa" is a woman; "widowed" could be anyone
        found.setdefault("gender", "female")
    return found


# Only phrasings that state an AGE: "60 saal ki/ka", "31 years old", "aged 67", "umar 40", "62 साल का",
# "४५ वर्षांचा", "২০ বছরের", "বয়স ৪০" (digits are ASCII by now). Not "10 saal se kheti" (10 years of farming).
AGE_PHRASE = re.compile(
    r"\b(\d{1,3})\s*(?:saal|sal|varsh)\s+(?:ki|ka|ke)\b|\b(\d{1,3})\s*(?:years?|yrs?)[\s-]old\b"
    r"|\baged?\s+(?:of\s+)?(\d{1,3})\b|\b(?:umar|umr|umra|age)\s*(?:is|hai|:)?\s*(\d{1,3})\b"
    r"|(\d{1,3})\s*(?:साल|वर्ष)\s+(?:का|की|के)|(?:उम्र|उमर|वय)\s*(?:है|:)?\s*(\d{1,3})|(\d{1,3})\s*वर्षांच"
    r"|(\d{1,3})\s*বছরের|বয়স\s*(\d{1,3})", re.IGNORECASE)
WIDOWED = re.compile(r"\b(widow|widowed|vidhwa|vidhva|bewa)\b|विधवा|বিধবা", re.IGNORECASE)
WIDOW_FEMALE = re.compile(r"\b(widow|vidhwa|vidhva|bewa)\b|विधवा|বিধবা", re.IGNORECASE)


def stated_ages(text: str) -> set[int]:
    ages = set()
    for match in AGE_PHRASE.finditer(text):
        number = int(next(group for group in match.groups() if group))
        if 0 < number <= 120:
            ages.add(number)
    return ages


# Some facts need more than "the quote is in the message": the quote must actually SAY it.
# Nano once gave gender=female and education=graduate with the quote "student hoon" (copied from the
# prompt's example) — the words are real, but they prove neither. Latin words need word boundaries;
# Indian scripts are matched as plain text.
_LATIN_GENDER = (r"female|male|woman|women|man|men|girl|boy|lady|gentleman|mother|mum|mom|father|dad|wife|husband|"
                 r"widow|widower|daughter|son|transgender|trans|mahila|purush|aurat|aadmi|mard|stree|ladki|ladka|"
                 r"vidhwa|vidhva|beti|beta|(saal|varsh|sal) k[ai]|(rahi|raha|karti|karta|padhti|padhta|chuki|chuka|"
                 r"kamati|kamata|sakti|sakta|hui|hua) (hoon|hu|hun)|she|he|her|his")
_SCRIPT_GENDER = ("महिला", "पुरुष", "स्त्री", "औरत", "आदमी", "लड़की", "लड़का", "लडकी", "लडका", "विधवा", "छात्रा", "छात्र",
                  "बेटी", "बेटा", "पत्नी", "पति", "की हूँ", "का हूँ", "की हूं", "का हूं", "रही हूँ", "रहा हूँ", "रही हूं",
                  "रहा हूं", "करती", "करता", "कमाती", "कमाता", "ट्रांसजेंडर", "वर्षांची", "वर्षांचा", "करते", "करतो",
                  "मुलगी", "मुलगा", "साल का", "साल की", "वर्ष का", "वर्ष की", "মহিলা", "পুরুষ", "মেয়ে", "ছেলে", "ছাত্রী", "বিধবা", "স্ত্রী", "স্বামী")
_LATIN_EDUCATION = (r"class|std|standard|grade|\d+\s*(th|st|nd|rd|vi|vee)|ba|b\.\s?a|bsc|b\.?\s?sc|bcom|b\.?\s?com|"
                    r"m\.\s?a|msc|m\.?\s?sc|mcom|btech|b\.?\s?tech|mtech|bba|mba|bca|mca|mbbs|llb|phd|iti|polytechnic|"
                    r"diploma|graduate|graduation|graduated|degree|post\s?graduate|pg|ug|matric|matriculation|inter|"
                    r"intermediate|school|high school|gcse|a\s?levels?|university|padhai|padhi|padha|anpadh|illiterate")
_SCRIPT_EDUCATION = ("बीए", "बी.ए", "बीएससी", "बीकॉम", "एमए", "कक्षा", "क्लास", "स्नातक", "ग्रेजुएट", "डिप्लोमा", "आईटीआई",
                     "मैट्रिक", "इंटर", "वीं", "दसवी", "बारावी", "पदवी", "इयत्ता", "शाळा", "स्कूल", "पढ़", "अनपढ़",
                     "স্নাতক", "শ্রেণি", "শ্রেণী", "ক্লাস", "বিএ", "মাধ্যমিক", "উচ্চমাধ্যমিক", "ডিপ্লোমা", "স্কুল")
EVIDENCE = {
    "gender": (re.compile(rf"\b({_LATIN_GENDER})\b", re.IGNORECASE), _SCRIPT_GENDER),
    "education_level": (re.compile(rf"\b({_LATIN_EDUCATION})\b", re.IGNORECASE), _SCRIPT_EDUCATION),
}


# "Unemployed" can wrongly exclude someone from schemes for workers — it must be said, not inferred
# (Nano gave occupation=unemployed for the quote "earning £900 a month").
UNEMPLOYED_WORDS = re.compile(
    r"\b(unemployed|jobless|out of work|no job|not working|lost my job|laid off|redundant|berozgaar|berozgar|"
    r"berojgar|kaam nahi|naukri nahi)\b|बेरोजगार|बेरोज़गार|काम नहीं|नौकरी नहीं|नोकरी नाही|বেকার|কাজ নেই", re.IGNORECASE)


def quote_shows(field: str, quote: str, value=None) -> bool:
    """True when the quote contains a word that actually states this kind of fact (or none is needed)."""
    if field == "occupation" and value == "unemployed":
        return bool(UNEMPLOYED_WORDS.search(unicodedata.normalize("NFC", quote)))
    if field not in EVIDENCE:
        return True
    latin, script_words = EVIDENCE[field]
    text = unicodedata.normalize("NFC", quote)
    return bool(latin.search(text)) or any(unicodedata.normalize("NFC", word) in text for word in script_words)


def facts_to_update(extraction: Extraction, message: str) -> tuple[dict, list[str]]:
    """Return (profile fields to update, descriptions of facts we rejected)."""
    update: dict = {}
    rejected: list[str] = []
    for fact in extraction.facts:
        if fact.field not in Profile.model_fields or fact.field == "needs":
            continue
        if not is_grounded(fact.quote, message) and fact.field in MONEY_FIELDS:
            fact = repair_money_quote(fact, message) or fact
        if not is_grounded(fact.quote, message):
            rejected.append(f"{fact.field}={fact.value!r} (quote not in message: {fact.quote!r})")
            continue
        if not quote_shows(fact.field, fact.quote, fact.value):
            rejected.append(f"{fact.field}={fact.value!r} (quote doesn't say it: {fact.quote!r})")
            continue
        from_words = money_from_words(fact, message) if fact.field in MONEY_FIELDS else None
        if from_words is None and not number_in_quote(fact.value, fact.quote):
            rejected.append(f"{fact.field}={fact.value!r} (number not in quote: {fact.quote!r})")
            continue
        try:
            value = from_words if from_words is not None else convert(fact)
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
