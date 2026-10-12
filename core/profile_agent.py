"""US-201 / US-202: Nemotron Nano turns what a person says into a profile,
and writes short follow-up questions for what's still missing.

Nano is used here because these calls happen on every chat message:
they must be fast and cheap.
"""
from typing import Literal

from pydantic import BaseModel, ValidationError

from core.llm import chat_json
from core.profile import Country, Profile

MODEL = "nano"

EXTRACT_PROMPT = """You extract facts about a person from what they say, to check which government schemes they qualify for.
Country: {country}

You get the profile known so far and the person's new message. Return ONLY a JSON object with the facts
stated or clearly implied in the NEW message, using these keys (omit or null if not mentioned):
{fields}

Rules:
- Only facts about the person applying (if they ask on behalf of someone, e.g. "my mother", describe THAT person).
- Money as plain integers in local currency (INR for India, GBP for UK). "1.5 lakh" = 150000. Monthly -> multiply by 12.
- Hindi grammar implies gender ("main padhti hoon", "20 saal ki hoon" -> female; "karta hoon" -> male).
- India: "BC"/"backward class" -> "OBC"; "extremely backward" -> "EBC"; "dalit" -> "SC"; "adivasi"/"tribal" -> "ST".
- region: the Indian state name in English, properly capitalised (e.g. "Uttar Pradesh"). Null for UK.
- occupation must be one of the allowed values; a person in school/college is occupation "student" and is_student true.
- needs: one short English sentence describing the help they want (e.g. "money for college fees").
- land_acres in acres: 1 hectare = 2.47 acres; "bigha" varies by state — for Uttar Pradesh/Bihar use 1 bigha ≈ 0.6 acre.
  "Zameen nahi hai" / "no land" -> 0.
- "single" / "single mum" says nothing about marital_status (could be unmarried, divorced, widowed): leave it null.
- If the person is answering our question (see "They are answering"), map a bare answer to THAT field:
  e.g. answering "the whole family's yearly income" with "80 hazaar" -> annual_family_income 80000.
- Never invent facts. If the message has no new facts, return {{}}.
"""

FOLLOW_UP_PROMPT = """You are Haq, a friendly assistant that helps people find government benefits.
Write ONE short follow-up question, addressed directly to the person ("you" / "aap"), that asks for ALL of these:
{fields}

- Write it in {language}. Under 30 words, warm and simple. No greeting, don't repeat what they said.
- Use everyday words. Never show technical names like "annual_family_income".
- Briefly say why it helps only if it fits naturally (e.g. "kai scholarships income par depend karti hain").
- If an item is a choice (e.g. category, gender), give its 2–5 quick-reply options; otherwise [].
Return ONLY JSON: {{"question": "...", "options": ["...", "..."]}}
"""

# How to describe each field to the model when asking about it
FIELD_LABELS = {
    "region": "which Indian state they live in",
    "age": "their age",
    "gender": "their gender",
    "annual_family_income": "the whole family's yearly income",
    "caste_category": "their social category (General, OBC, EBC, SC or ST)",
    "occupation": "what they do (student, farmer, labourer, job, unemployed...)",
    "has_children": "whether they have children",
    "personal_annual_income": "how much they earn",
    "savings": "roughly how much savings they have",
    "has_disability": "whether they have a disability or long-term health condition",
    "land_acres": "how much farm land is in their own name (0 if none)",
}


# Common Hindi words written in Latin script. If a message has a few of these, it's Hinglish.
HINGLISH_WORDS = {
    "hai", "hain", "hoon", "hu", "main", "mera", "meri", "mere", "mujhe", "hum", "aap", "kya", "nahi",
    "ka", "ki", "ke", "ko", "se", "mein", "saal", "ghar", "papa", "maa", "chahiye", "karta", "karti",
    "padh", "rahi", "raha", "batao", "koi", "kitna", "aur", "bhi",
}


Language = Literal["hinglish", "english"]

LANGUAGE_INSTRUCTIONS = {
    "hinglish": "Hinglish (Hindi written in Latin script, like 'Aapki umar kitni hai?')",
    "english": "simple English",
}


def detect_language(message: str, country: Country, previous: Language | None) -> Language:
    """Decide the reply language in code, so the model can't drift into the wrong one.
    Short answers like "58, male" don't say much, so we keep the conversation's earlier language."""
    if country == "UK":
        return "english"
    words = set(message.lower().replace(",", " ").replace(".", " ").replace("?", " ").split())
    hinglish_hits = len(words & HINGLISH_WORDS)
    if hinglish_hits >= 2:
        return "hinglish"
    if previous:
        return previous
    return "hinglish" if hinglish_hits else "english"


class FollowUp(BaseModel):
    question: str
    options: list[str] = []


def _field_list() -> str:
    lines = []
    for name, field in Profile.model_fields.items():
        type_name = str(field.annotation).replace("typing.", "").replace("NoneType", "null")
        hint = f" — {field.description}" if field.description else ""
        lines.append(f'  "{name}": {type_name}{hint}')
    return "{\n" + ",\n".join(lines) + "\n}"


FIELDS_TEXT = _field_list()


def extract_profile(message: str, known: Profile, country: Country, answering: list[str] | None = None) -> Profile:
    """Read the new message and return the known profile updated with any new facts.
    `answering` = the fields our last follow-up question asked about, so short answers map correctly."""
    context = f"Profile so far: {known.model_dump_json(exclude_none=True)}\n\n"
    if answering:
        asked = "; ".join(f"{name} ({FIELD_LABELS.get(name, name)})" for name in answering)
        context += f"They are answering our question about: {asked}\n\n"
    raw = chat_json(MODEL, [
        {"role": "system", "content": EXTRACT_PROMPT.format(country=country, fields=FIELDS_TEXT)},
        {"role": "user", "content": context + f"New message: {message}"},
    ], max_tokens=4000)  # thinking stays on: inferring facts from Hinglish benefits from reasoning
    # Drop keys the model invented that aren't in our Profile, then validate field by field,
    # so one bad value (e.g. an unknown occupation) doesn't throw away every other fact.
    update = {}
    for name, value in raw.items():
        if name in Profile.model_fields and value not in (None, "", []):
            try:
                Profile.model_validate({name: value})
                update[name] = value
            except ValidationError:
                pass
    return known.merged_with(Profile(**update))


def follow_up_question(fields: list[str], last_message: str, language: Language) -> FollowUp:
    wanted = "\n".join(f"- {FIELD_LABELS.get(name, name)}" for name in fields)
    raw = chat_json(MODEL, [
        {"role": "system", "content": FOLLOW_UP_PROMPT.format(fields=wanted, language=LANGUAGE_INSTRUCTIONS[language])},
        {"role": "user", "content": f"The person's last message: {last_message}"},
    ], schema=FollowUp, max_tokens=300, temperature=0.3,
       thinking=False)  # a short question doesn't need step-by-step reasoning
    return FollowUp.model_validate(raw)
