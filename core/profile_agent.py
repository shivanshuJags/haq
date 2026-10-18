"""US-201 / US-202: Nemotron Nano turns what a person says into a profile,
and writes short follow-up questions for what's still missing.

Nano is used here because these calls happen on every chat message: they must be fast.
Both calls run with thinking OFF + structured output (~1–2s instead of ~11s).
Extraction stays accurate because every fact must carry a quote from the message,
which code verifies, and code does all the arithmetic (see core/grounded.py).
"""
import re

from pydantic import BaseModel

from core.grounded import Extraction, facts_to_update
from core.languages import INSTRUCTIONS, Language
from core.llm import chat_json
from core.profile import Country, Profile

MODEL = "nano"

GROUNDED_PROMPT = """You extract facts about a person from their message, to check which government schemes they qualify for.
Country: {country}

Return JSON: {{"facts": [{{"field", "value", "unit", "quote"}}], "needs": "..."}}

Each fact:
- field: one of these profile fields:
{fields}
- value: the value in the field's type. For money and land give the number EXACTLY as the person said it
  (e.g. 900, 1.5, 80000, 2) and put the unit in `unit` — never convert or multiply yourself.
- unit: money -> "per_year" | "per_month" | "per_week" | "lakh_per_year" (for "1.5 lakh" -> value 1.5)
  | "thousand_per_year" (for "80 hazaar"/"80k" -> value 80);
  savings amounts are totals -> "none" (or "lakh_per_year" if said in lakh); land -> "acre" | "bigha" | "hectare";
  everything else -> "none".
- quote: copy the EXACT words from the message that state this fact (a few words). If you can't quote it, don't include the fact.

Rules:
- Only facts the person actually states about the person applying (if asking for someone else, e.g. "my mother", that person).
- Never guess: no residence, education, carer status, disability, marital status, occupation unless stated.
- "single" / "single mum" is NOT a marital status.
- Hindi grammar shows gender: "20 saal ki hoon", "padh rahi hoon" -> female (quote those words); "karta hoon" -> male.
  Words also show gender: mum/mom/mother/wife/widow/maa -> female; dad/father/husband/papa -> male (for the person applying).
- India: "BC"/"backward class" -> "OBC"; "extremely backward" -> "EBC"; "dalit" -> "SC"; "adivasi" -> "ST".
- region: Indian state in English, e.g. "UP" -> "Uttar Pradesh".
- Messages may be in Hindi, Marathi or Bengali script. Quote the original words exactly, but write enum values
  (gender, caste_category, occupation…) and region in English as listed. Never guess a state or category that
  isn't stated.
- A person in school/college: occupation "student" AND is_student true. "BA"/"BSc"/"B.Com" -> education_level "graduate".
- Occupation words: "kisan"/"kheti" -> "farmer"; "majdoor"/"mazdoor"/"mazdoori" -> "unorganised_worker";
  "berozgaar"/"out of work" -> "unemployed"; "naukri"/"job"/"employed" -> "salaried_employee";
  "apna kaam"/"business"/"self-employed" -> "self_employed".
- Short yes/no answers ("Haan", "Nahi", "Yes", "No") to our question set THAT field to true/false (quote the word).
- "Purush" -> male; "Mahila"/"stree" -> female.
- If they are answering our question (see "They are answering"), a bare answer belongs to THAT field.
- needs: one short English sentence on the help they want, or null.
- Extract EVERY stated fact — check each field in the list above against the message.

Example 1 (Country: IN)
Message: "Main 19 saal ki hoon, BSc kar rahi hoon, Bihar se, ghar ki kamai 2 lakh"
{{"facts": [
  {{"field": "age", "value": 19, "unit": "none", "quote": "19 saal"}},
  {{"field": "gender", "value": "female", "unit": "none", "quote": "saal ki hoon"}},
  {{"field": "is_student", "value": true, "unit": "none", "quote": "BSc kar rahi hoon"}},
  {{"field": "occupation", "value": "student", "unit": "none", "quote": "BSc kar rahi hoon"}},
  {{"field": "education_level", "value": "graduate", "unit": "none", "quote": "BSc"}},
  {{"field": "region", "value": "Bihar", "unit": "none", "quote": "Bihar"}},
  {{"field": "annual_family_income", "value": 2, "unit": "lakh_per_year", "quote": "kamai 2 lakh"}}
 ], "needs": null}}

Example 2 (Country: UK)
Message: "I'm a dad of three, 40, out of work, and I get £300 a week from my partner's job"
{{"facts": [
  {{"field": "gender", "value": "male", "unit": "none", "quote": "dad"}},
  {{"field": "has_children", "value": true, "unit": "none", "quote": "dad of three"}},
  {{"field": "children_count", "value": 3, "unit": "none", "quote": "dad of three"}},
  {{"field": "age", "value": 40, "unit": "none", "quote": "40"}},
  {{"field": "occupation", "value": "unemployed", "unit": "none", "quote": "out of work"}},
  {{"field": "annual_family_income", "value": 300, "unit": "per_week", "quote": "£300 a week"}}
 ], "needs": null}}
"""

# Follow-up questions are fixed templates, not generated: we always know exactly which fact we
# need, so a template is instant, never drifts off-topic, and its quick-reply buttons always match.
# (The AI's job is understanding the ANSWER — see extract_profile.)
# Each entry: (question, quick-reply options). Numbers (age, income, land) get no options on purpose:
# a range like "₹0–2L" can't be checked against an exact income limit.
QUESTIONS: dict[str, dict[str, tuple[str, list[str]]]] = {
    "hinglish": {
        "region": ("Aap kis rajya mein rehte hain?", []),
        "age": ("Aapki umar kitni hai?", []),
        "gender": ("Aap purush hain ya mahila?", ["Purush", "Mahila", "Transgender"]),
        "annual_family_income": ("Aapke poore parivaar ki saal bhar ki kamaai lagbhag kitni hai? (jaise: 80 hazaar, 1.5 lakh)", []),
        "caste_category": ("Aapki category kya hai?", ["General", "OBC", "EBC", "SC", "ST"]),
        "occupation": ("Aap mukhya roop se kya karte hain?", ["Student", "Kisan", "Mazdoor", "Naukri", "Apna kaam", "Berozgaar"]),
        "land_acres": ("Aapke naam par kitni kheti ki zameen hai? (bigha ya acre mein; nahi hai to 0)", []),
        "has_children": ("Kya aapke bachche hain?", ["Haan", "Nahi"]),
        "personal_annual_income": ("Aap khud kitna kamaate hain? (mahine ya saal ka)", []),
        "savings": ("Aapke paas lagbhag kitni bachat (savings) hai?", []),
        "has_disability": ("Kya aapko koi viklangta ya lambi bimari hai?", ["Haan", "Nahi"]),
    },
    "english": {
        "region": ("Which state do you live in?", []),
        "age": ("How old are you?", []),
        "gender": ("What is your gender?", ["Male", "Female", "Transgender"]),
        "annual_family_income": ("Roughly how much does your whole household earn in a year?", []),
        "caste_category": ("What is your social category?", ["General", "OBC", "EBC", "SC", "ST"]),
        "occupation": ("What do you mainly do?", ["Student", "Employed", "Self-employed", "Unemployed", "Carer", "Retired"]),
        "land_acres": ("How much farm land is in your name? (0 if none)", []),
        "has_children": ("Do you have children?", ["Yes", "No"]),
        "personal_annual_income": ("How much do you earn, roughly? (per week, month or year)", []),
        "savings": ("Roughly how much do you have in savings?", []),
        "has_disability": ("Do you have a disability or long-term health condition?", ["Yes", "No"]),
    },
    "hindi": {
        "region": ("आप किस राज्य में रहते हैं?", []),
        "age": ("आपकी उम्र कितनी है?", []),
        "gender": ("आप पुरुष हैं या महिला?", ["पुरुष", "महिला", "ट्रांसजेंडर"]),
        "annual_family_income": ("आपके पूरे परिवार की साल भर की कमाई लगभग कितनी है? (जैसे: 80 हज़ार, 1.5 लाख)", []),
        "caste_category": ("आपकी श्रेणी (कैटेगरी) क्या है?", ["सामान्य", "OBC", "EBC", "SC", "ST"]),
        "occupation": ("आप मुख्य रूप से क्या करते हैं?", ["छात्र", "किसान", "मज़दूर", "नौकरी", "अपना काम", "बेरोज़गार"]),
        "land_acres": ("आपके नाम पर कितनी खेती की ज़मीन है? (बीघा या एकड़ में; नहीं है तो 0)", []),
        "has_children": ("क्या आपके बच्चे हैं?", ["हाँ", "नहीं"]),
        "personal_annual_income": ("आप खुद कितना कमाते हैं? (महीने या साल का)", []),
        "savings": ("आपके पास लगभग कितनी बचत है?", []),
        "has_disability": ("क्या आपको कोई दिव्यांगता या लंबी बीमारी है?", ["हाँ", "नहीं"]),
    },
    "marathi": {
        "region": ("तुम्ही कोणत्या राज्यात राहता?", []),
        "age": ("तुमचे वय किती आहे?", []),
        "gender": ("तुम्ही पुरुष आहात की स्त्री?", ["पुरुष", "स्त्री", "ट्रान्सजेंडर"]),
        "annual_family_income": ("तुमच्या संपूर्ण कुटुंबाचे वार्षिक उत्पन्न साधारण किती आहे? (उदा. 80 हजार, 1.5 लाख)", []),
        "caste_category": ("तुमचा प्रवर्ग (कॅटेगरी) कोणता आहे?", ["सर्वसाधारण", "OBC", "EBC", "SC", "ST"]),
        "occupation": ("तुम्ही मुख्यतः काय करता?", ["विद्यार्थी", "शेतकरी", "मजूर", "नोकरी", "स्वतःचा व्यवसाय", "बेरोजगार"]),
        "land_acres": ("तुमच्या नावावर किती शेतजमीन आहे? (एकर मध्ये; नसल्यास 0)", []),
        "has_children": ("तुम्हाला मुले आहेत का?", ["हो", "नाही"]),
        "personal_annual_income": ("तुम्ही स्वतः किती कमावता? (महिन्याचे किंवा वर्षाचे)", []),
        "savings": ("तुमच्याकडे साधारण किती बचत आहे?", []),
        "has_disability": ("तुम्हाला काही अपंगत्व किंवा दीर्घ आजार आहे का?", ["हो", "नाही"]),
    },
    "bengali": {
        "region": ("আপনি কোন রাজ্যে থাকেন?", []),
        "age": ("আপনার বয়স কত?", []),
        "gender": ("আপনি পুরুষ না মহিলা?", ["পুরুষ", "মহিলা", "ট্রান্সজেন্ডার"]),
        "annual_family_income": ("আপনার পুরো পরিবারের বার্ষিক আয় মোটামুটি কত? (যেমন: 80 হাজার, 1.5 লাখ)", []),
        "caste_category": ("আপনার শ্রেণী (ক্যাটেগরি) কী?", ["সাধারণ", "OBC", "EBC", "SC", "ST"]),
        "occupation": ("আপনি মূলত কী করেন?", ["ছাত্র/ছাত্রী", "কৃষক", "শ্রমিক", "চাকরি", "নিজের ব্যবসা", "বেকার"]),
        "land_acres": ("আপনার নামে কতটা চাষের জমি আছে? (একরে; না থাকলে 0)", []),
        "has_children": ("আপনার কি সন্তান আছে?", ["হ্যাঁ", "না"]),
        "personal_annual_income": ("আপনি নিজে কত আয় করেন? (মাসিক বা বার্ষিক)", []),
        "savings": ("আপনার কাছে মোটামুটি কত সঞ্চয় আছে?", []),
        "has_disability": ("আপনার কি কোনো প্রতিবন্ধকতা বা দীর্ঘমেয়াদি অসুখ আছে?", ["হ্যাঁ", "না"]),
    },
}

# What each quick-reply button means. A tapped button is understood in code — instantly and
# exactly — without asking the model. Keys are lower-case button labels, in every language.
OPTION_VALUES: dict[str, dict[str, object]] = {
    "gender": {
        "purush": "male", "male": "male", "पुरुष": "male", "পুরুষ": "male",
        "mahila": "female", "female": "female", "महिला": "female", "स्त्री": "female", "মহিলা": "female",
        "transgender": "transgender", "ट्रांसजेंडर": "transgender", "ट्रान्सजेंडर": "transgender", "ট্রান্সজেন্ডার": "transgender",
    },
    "caste_category": {
        "general": "General", "सामान्य": "General", "सर्वसाधारण": "General", "সাধারণ": "General",
        "obc": "OBC", "ebc": "EBC", "sc": "SC", "st": "ST",
    },
    "occupation": {
        "student": "student", "छात्र": "student", "विद्यार्थी": "student", "ছাত্র/ছাত্রী": "student",
        "kisan": "farmer", "किसान": "farmer", "शेतकरी": "farmer", "কৃষক": "farmer",
        "mazdoor": "unorganised_worker", "मज़दूर": "unorganised_worker", "मजूर": "unorganised_worker", "শ্রমিক": "unorganised_worker",
        "naukri": "salaried_employee", "employed": "salaried_employee", "नौकरी": "salaried_employee", "नोकरी": "salaried_employee", "চাকরি": "salaried_employee",
        "apna kaam": "self_employed", "self-employed": "self_employed", "अपना काम": "self_employed",
        "स्वतःचा व्यवसाय": "self_employed", "নিজের ব্যবসা": "self_employed",
        "berozgaar": "unemployed", "unemployed": "unemployed", "बेरोज़गार": "unemployed", "बेरोजगार": "unemployed", "বেকার": "unemployed",
        "carer": "carer", "retired": "retired",
    },
    "has_children": {"haan": True, "yes": True, "हाँ": True, "हो": True, "হ্যাঁ": True,
                     "nahi": False, "no": False, "नहीं": False, "नाही": False, "না": False},
    "has_disability": {"haan": True, "yes": True, "हाँ": True, "हो": True, "হ্যাঁ": True,
                       "nahi": False, "no": False, "नहीं": False, "नाही": False, "না": False},
}


def quick_reply_value(message: str, answering: list[str] | None):
    """If the message is exactly one of our buttons for the field just asked, return (field, value)."""
    if not answering or len(answering) != 1:
        return None
    field = answering[0]
    value = OPTION_VALUES.get(field, {}).get(message.strip().lower())
    return (field, value) if value is not None else None


# How to describe each field to the model when the person is answering it
FIELD_LABELS = {
    "region": "which Indian state they live in",
    "age": "their age",
    "gender": "their gender",
    "annual_family_income": "the whole family's yearly income",
    "caste_category": "their social category (General, OBC, EBC, SC or ST)",
    "occupation": "what they mainly do for work or study",
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


LANGUAGE_INSTRUCTIONS = INSTRUCTIONS  # re-exported for core/verdict.py and core/rescue.py


def detect_language(message: str, country: Country, previous: Language | None) -> Language:
    """Decide the reply language in code, so the model can't drift into the wrong one.
    A language the person picked (Hindi, Marathi, Bengali…) is kept as is. Between English and
    Hinglish we follow how they write. Short answers like "58, male" keep the earlier language."""
    if country == "UK":
        return "english"
    if previous and previous not in ("english", "hinglish"):
        return previous
    words = set(message.lower().replace(",", " ").replace(".", " ").replace("?", " ").split())
    hinglish_hits = len(words & HINGLISH_WORDS)
    if hinglish_hits >= 2:
        return "hinglish"
    if previous:
        return previous
    return "hinglish" if hinglish_hits else "english"


UNMARRIED_WORDS = re.compile(
    r"\b(unmarried|never married|not married|kunwar[ai]?|avivahit|shaadi nahi|shadi nahi)\b", re.IGNORECASE
)


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
    tapped = quick_reply_value(message, answering)
    if tapped:
        field, value = tapped
        return known.merged_with(Profile(**{field: value}))

    context = f"Profile so far: {known.model_dump_json(exclude_none=True)}\n\n"
    if answering:
        asked = "; ".join(f"{name} ({FIELD_LABELS.get(name, name)})" for name in answering)
        context += f"They are answering our question about: {asked}\n\n"
    raw = chat_json(MODEL, [
        {"role": "system", "content": GROUNDED_PROMPT.format(country=country, fields=FIELDS_TEXT)},
        {"role": "user", "content": context + f"New message: {message}"},
    ], schema=Extraction, max_tokens=1500, thinking=False)
    # Keeps only facts whose quote is really in the message, converts units in code,
    # and validates each field on its own so one bad value doesn't drop the rest.
    update, _rejected = facts_to_update(Extraction.model_validate(raw), message)

    # Nano tends to read "single mum" as "unmarried", despite the prompt. Single could also mean
    # divorced, separated or widowed, and a wrong marital status can exclude people — so only keep
    # "unmarried" when the person actually said so.
    if update.get("marital_status") == "unmarried" and not UNMARRIED_WORDS.search(message):
        del update["marital_status"]

    return known.merged_with(Profile(**update))


def follow_up_question(fields: list[str], language: Language) -> FollowUp:
    """One question for one or two missing facts. Choice fields are always asked alone
    (see api/routes/profile.py), so their options belong to the whole question."""
    templates = QUESTIONS[language]
    parts = [templates[name] for name in fields if name in templates]
    question = " ".join(text for text, _ in parts)
    options = parts[0][1] if len(parts) == 1 else []
    return FollowUp(question=question, options=options)
